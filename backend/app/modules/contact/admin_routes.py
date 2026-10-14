"""Admin inbox for public contact messages."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.contact.service import ContactService
from app.shared.schemas import ContactMessageResponse, ContactMessageUpdate

router = APIRouter()

Needs_contact_manage = Annotated[CurrentUser, Depends(require_permission("contact.manage"))]



@router.get("", response_model=list[ContactMessageResponse])
async def list_messages(
    admin: Needs_contact_manage,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status", pattern="^(new|handled)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await ContactService(db).list(status_filter, limit, offset)


@router.patch("/{message_id}", response_model=ContactMessageResponse)
async def update_message(
    message_id: str,
    data: ContactMessageUpdate,
    admin: Needs_contact_manage,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ContactService(db).set_status(message_id, data.status, admin.user_id)
