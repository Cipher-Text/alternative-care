"""Clinic-facing appointment requests (ADR 009, Phase 3): see, confirm or decline."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.modules.identity.requests import ClinicRequestService
from app.shared.schemas import ClinicRequestItem, ConfirmRequest, DeclineRequest

router = APIRouter()
Staff = Annotated[CurrentUser, Depends(require_role("doctor", "receptionist"))]


def get_service(db: Annotated[AsyncSession, Depends(get_db)], user: Staff) -> ClinicRequestService:
    return ClinicRequestService(db, user.tenant_id, user.user_id)


Service = Annotated[ClinicRequestService, Depends(get_service)]


@router.get("", response_model=list[ClinicRequestItem])
async def list_requests(
    service: Service,
    status_filter: str | None = Query(None, alias="status", pattern="^(requested|confirmed|declined|cancelled)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list(status_filter, limit, offset)


@router.post("/{request_id}/confirm", response_model=ClinicRequestItem)
async def confirm_request(request_id: str, data: ConfirmRequest, service: Service):
    """Books the appointment (same slot rules as any appointment), creates and links the patient record
    if this person is not linked here yet, and texts the patient from the clinic's own SMS allowance."""
    return await service.confirm(request_id, data)


@router.post("/{request_id}/decline", response_model=ClinicRequestItem)
async def decline_request(request_id: str, data: DeclineRequest, service: Service):
    return await service.decline(request_id, data)
