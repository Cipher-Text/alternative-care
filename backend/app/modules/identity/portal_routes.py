"""Patient portal API (ADR 009, Phase 2). Sign-in is public; everything else needs a patient token."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.phone import mask_phone
from app.core.rate_limit import enforce_rate_limit
from app.modules.identity.portal import PatientContext, PortalAuthService, PortalService, get_current_patient
from app.shared.schemas import (
    PortalActivate,
    PortalAuthRequest,
    PortalAuthVerify,
    PortalClinic,
    PortalMe,
    PortalRecords,
    PortalToken,
    VerifyRequestResponse,
)

router = APIRouter()
Patient = Annotated[PatientContext, Depends(get_current_patient)]
Db = Annotated[AsyncSession, Depends(get_db)]


async def _limit(request: Request, scope: str, limit: int, window: int = 3600) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    result = await enforce_rate_limit(request, scope, limit, window)
    if not result.allowed:
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(result.retry_after)})


@router.post("/auth/request", response_model=VerifyRequestResponse)
async def request_code(data: PortalAuthRequest, request: Request, db: Db):
    """Send a sign-in code. The answer is the same whether or not the phone already has an account."""
    await _limit(request, "portal_request", settings.RATE_LIMIT_PORTAL_PER_HOUR)
    challenge, resend = await PortalAuthService(db).request(data.phone)
    return VerifyRequestResponse(
        challenge_id=challenge.id, expires_at=challenge.expires_at, resend_after_seconds=resend,
        phone_masked=mask_phone(data.phone),
    )


@router.post("/auth/verify", response_model=PortalToken)
async def verify_code(data: PortalAuthVerify, request: Request, db: Db):
    await _limit(request, "portal_verify", settings.RATE_LIMIT_PORTAL_PER_HOUR * 3)
    return await PortalAuthService(db).verify(data.challenge_id, data.code)


@router.get("/me", response_model=PortalMe)
async def me(patient: Patient, db: Db):
    return await PortalService(db, patient).me()


@router.get("/profiles/{profile_id}/records", response_model=PortalRecords)
async def records(profile_id: str, patient: Patient, db: Db):
    """Read-only appointments, issued prescriptions and receipts from every clinic linked to this profile."""
    return await PortalService(db, patient).records(profile_id)


@router.post("/links/activate", response_model=PortalClinic)
async def activate(data: PortalActivate, request: Request, patient: Patient, db: Db):
    """Enter a code from the clinic to see an earlier record in this account."""
    await _limit(request, "portal_activate", 10)
    return await PortalService(db, patient).activate(data.code)


@router.post("/links/{link_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke(link_id: str, patient: Patient, db: Db):
    await PortalService(db, patient).revoke(link_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/links/{link_id}/prescriptions/{prescription_id}/pdf")
async def prescription_pdf(link_id: str, prescription_id: str, patient: Patient, db: Db):
    pdf, filename = await PortalService(db, patient).prescription_pdf(link_id, prescription_id)
    return Response(
        content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
