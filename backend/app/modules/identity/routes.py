"""Clinic-facing patient identity API (ADR 009, Phase 1) and the public claim flow."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.core.rate_limit import enforce_rate_limit
from app.modules.identity.service import ClaimService, IdentityService
from app.shared.schemas import (
    BasicDetails,
    ClaimCodeResponse,
    ClaimConfirm,
    ClaimRequest,
    ClaimResult,
    LinkRequest,
    LinkResponse,
    PatientIdentityStatus,
    ProfilePrefillRequest,
    ProfileSearch,
    ProfileSummary,
    RevokeRequest,
    VerifyConfirm,
    VerifyConfirmResponse,
    VerifyRequest,
    VerifyRequestResponse,
)
from app.core.phone import mask_phone

router = APIRouter()
public_router = APIRouter()

# Receptionists register patients, so they verify and link too; only a doctor revokes a link.
Staff = Annotated[CurrentUser, Depends(require_role("doctor", "receptionist"))]
DoctorOnly = Annotated[CurrentUser, Depends(require_role("doctor"))]


def get_service(db: Annotated[AsyncSession, Depends(get_db)], user: Staff) -> IdentityService:
    return IdentityService(db, tenant_id=user.tenant_id, user_id=user.user_id)


Service = Annotated[IdentityService, Depends(get_service)]


async def _limit(request: Request, scope: str, limit: int, window: int = 3600) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    result = await enforce_rate_limit(request, scope, limit, window)
    if not result.allowed:
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(result.retry_after)})


@router.post("/verify/request", response_model=VerifyRequestResponse)
async def request_code(data: VerifyRequest, request: Request, service: Service):
    """Send a code to the patient's phone (the platform pays for the SMS)."""
    await _limit(request, "identity_verify", 60)
    challenge, resend = await service.request_code(data.phone)
    return VerifyRequestResponse(
        challenge_id=challenge.id, expires_at=challenge.expires_at, resend_after_seconds=resend,
        phone_masked=mask_phone(data.phone),
    )


@router.post("/verify/confirm", response_model=VerifyConfirmResponse)
async def confirm_code(data: VerifyConfirm, service: Service):
    """The patient read out the code. Returns a short-lived token for looking up profiles and linking."""
    token, expires, has_profiles = await service.confirm_code(data.challenge_id, data.code)
    return VerifyConfirmResponse(verification_token=token, expires_at=expires, has_profiles=has_profiles)


@router.post("/profiles/search", response_model=list[ProfileSummary])
async def search_profiles(data: ProfileSearch, service: Service):
    """Matching profiles for the visitor's name only (never the whole family list)."""
    return await service.search(data.verification_token, data.name)


@router.post("/profiles/prefill", response_model=BasicDetails)
async def prefill_profile(data: ProfilePrefillRequest, service: Service):
    """Basic details only, to prefill a new patient record. Nothing clinical."""
    return await service.prefill(data.verification_token, data.profile_id)


@router.post("/link", response_model=LinkResponse, status_code=201)
async def link_patient(data: LinkRequest, service: Service):
    return await service.link(data.verification_token, data.patient_id, data.profile_id, data.new_profile)


@router.get("/patients/{patient_id}", response_model=PatientIdentityStatus)
async def patient_status(patient_id: str, service: Service):
    return await service.status(patient_id)


@router.post("/patients/{patient_id}/revoke", response_model=PatientIdentityStatus)
async def revoke_link(patient_id: str, data: RevokeRequest, db: Annotated[AsyncSession, Depends(get_db)], user: DoctorOnly):
    """On the patient's request. The clinic keeps its own medical record; only the link is removed."""
    return await IdentityService(db, user.tenant_id, user.user_id).revoke(patient_id, data.note)


@router.post("/patients/{patient_id}/claim-code", response_model=ClaimCodeResponse)
async def create_claim_code(patient_id: str, service: Service):
    """A code to hand to the patient so they can link this record later from their own phone."""
    code, expires = await service.create_claim_code(patient_id)
    return ClaimCodeResponse(code=code, expires_at=expires)


# ----- public (no login): the patient links a record with a claim code ------------------------


@public_router.post("/claim/request", response_model=VerifyRequestResponse)
async def claim_request(data: ClaimRequest, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    await _limit(request, "identity_claim", settings.RATE_LIMIT_CLAIM_PER_HOUR)
    challenge, resend = await ClaimService(db).request(data.phone, data.claim_code)
    return VerifyRequestResponse(
        challenge_id=challenge.id, expires_at=challenge.expires_at, resend_after_seconds=resend,
        phone_masked=mask_phone(data.phone),
    )


@public_router.post("/claim/confirm", response_model=ClaimResult)
async def claim_confirm(data: ClaimConfirm, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    await _limit(request, "identity_claim_confirm", settings.RATE_LIMIT_CLAIM_PER_HOUR * 2)
    return await ClaimService(db).confirm(data.challenge_id, data.code, data.relationship)
