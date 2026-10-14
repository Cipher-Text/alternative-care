"""Messaging endpoints: send SMS and email through the platform's providers, and read the message log."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import CreditService
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_tenant_user
from app.core.messaging import email_configured, sms_configured
from app.modules.messaging.service import MessageLogService
from app.modules.messaging.tasks import send_platform_email_task, send_platform_sms_task
from app.shared.models import Tenant
from app.shared.schemas import MessageLogListItem, SendEmailRequest, SendOperationResponse, SendSMSRequest

router = APIRouter()


def _unavailable(channel: str) -> HTTPException:
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"{channel} is not available right now.")


@router.get("/logs", response_model=list[MessageLogListItem])
async def list_message_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_tenant_user)],
    transaction_type: str | None = Query(None, description="sms_sent or email_sent"),
    status: str | None = Query(None, description="success or failed"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """The clinic's sent messages, newest first."""
    return await MessageLogService(db, current_user.tenant_id).list_logs(
        transaction_type=transaction_type, status=status, limit=limit, offset=offset
    )


@router.post("/send/sms", response_model=SendOperationResponse)
async def send_sms(
    data: SendSMSRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_tenant_user)],
):
    """Send an SMS through the platform provider. Charged as a messaging credit (the plan's allowance first, then
    purchased credits; spending one also counts it in the clinic's usage). Queued for background sending."""
    if not sms_configured():
        raise _unavailable("SMS")
    source = await CreditService(db, current_user.tenant_id).spend("sms")
    task = send_platform_sms_task.delay(
        tenant_id=current_user.tenant_id, recipient=data.recipient, message=data.message, source=source
    )
    return SendOperationResponse(
        success=True, message=f"SMS queued for sending to {data.recipient}", transaction_id=task.id, queued=True
    )


@router.post("/send/email", response_model=SendOperationResponse)
async def send_email(
    data: SendEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_tenant_user)],
):
    """Send an email through the platform provider, with the clinic's address as the reply-to. Charged as a
    messaging credit. Queued for background sending."""
    if not email_configured():
        raise _unavailable("Email")
    source = await CreditService(db, current_user.tenant_id).spend("email")
    tenant = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    task = send_platform_email_task.delay(
        tenant_id=current_user.tenant_id, recipient=data.recipient, subject=data.subject, body_html=data.body_html,
        body_text=data.body_text, reply_to=tenant.clinic_email or tenant.email, source=source,
    )
    return SendOperationResponse(
        success=True, message=f"Email queued for sending to {data.recipient}", transaction_id=task.id, queued=True
    )
