"""Doctor-facing Facebook promotion API (a Pro / Enterprise benefit)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.modules.marketing.service import FacebookService
from app.shared.schemas import (
    FacebookApprove,
    FacebookChangesRequest,
    FacebookRequestCreate,
    FacebookRequestResponse,
    FacebookSummary,
)

router = APIRouter()

# Doctors only: it is their name and profile being promoted
Doctor = Annotated[CurrentUser, Depends(require_role("doctor"))]


def get_service(db: Annotated[AsyncSession, Depends(get_db)], user: Doctor) -> FacebookService:
    return FacebookService(db, tenant_id=user.tenant_id, user_id=user.user_id)


Service = Annotated[FacebookService, Depends(get_service)]


@router.get("/facebook", response_model=FacebookSummary)
async def get_summary(service: Service):
    """The benefit, this quarter's usage, why a request is or is not possible, and history."""
    return await service.summary()


@router.post("/facebook/requests", response_model=FacebookRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(data: FacebookRequestCreate, service: Service):
    return await service.create(data.doctor_note)


@router.post("/facebook/requests/{request_id}/cancel", response_model=FacebookRequestResponse)
async def cancel_request(request_id: str, service: Service):
    return await service.cancel(request_id)


@router.post("/facebook/requests/{request_id}/approve", response_model=FacebookRequestResponse)
async def approve_draft(request_id: str, data: FacebookApprove, service: Service):
    """Approve the exact drafted text. Staff cannot mark it posted before this."""
    return await service.approve(request_id, data.comment)


@router.post("/facebook/requests/{request_id}/changes", response_model=FacebookRequestResponse)
async def request_changes(request_id: str, data: FacebookChangesRequest, service: Service):
    """Send the draft back to staff with a comment."""
    return await service.request_changes(request_id, data.comment)
