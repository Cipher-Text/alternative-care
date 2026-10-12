"""Admin queue for Facebook profile promotion: draft, reject, mark posted."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireAdmin
from app.modules.marketing.service import AdminFacebookService
from app.shared.schemas import (
    AdminFacebookRequest,
    FacebookDraft,
    FacebookPosted,
    FacebookReject,
    FacebookRequestResponse,
)

router = APIRouter()


def get_service(db: Annotated[AsyncSession, Depends(get_db)], admin: RequireAdmin) -> AdminFacebookService:
    return AdminFacebookService(db, admin_id=admin.user_id)


Service = Annotated[AdminFacebookService, Depends(get_service)]


@router.get("/facebook", response_model=list[AdminFacebookRequest])
async def list_requests(
    service: Service,
    status_filter: str | None = Query(
        None, alias="status", pattern="^(requested|drafted|approved|posted|rejected|cancelled)$"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list(status_filter, limit, offset)


@router.post("/facebook/{request_id}/draft", response_model=FacebookRequestResponse)
async def save_draft(request_id: str, data: FacebookDraft, service: Service):
    """Write (or rewrite) the post. The doctor then reviews it; nothing is published yet."""
    return await service.draft(request_id, data.draft_text)


@router.post("/facebook/{request_id}/reject", response_model=FacebookRequestResponse)
async def reject_request(request_id: str, data: FacebookReject, service: Service):
    return await service.reject(request_id, data.reason)


@router.post("/facebook/{request_id}/posted", response_model=FacebookRequestResponse)
async def mark_posted(request_id: str, data: FacebookPosted, service: Service):
    """Only allowed after the doctor approved the exact text (409 otherwise)."""
    return await service.mark_posted(request_id, data.post_url)
