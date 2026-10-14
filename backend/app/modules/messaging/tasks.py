"""Celery tasks that send SMS and email through the platform's providers.

The credit is reserved by the caller before the task is queued, and refunded here if the send fails for good.
"""

import asyncio

from celery import Task

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.shared.models import MessageLog


class MessageTask(Task):
    """Base task with retries and backoff."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


async def _log_platform_send(
    tenant_id: str, transaction_type: str, recipient: str, status: str,
    request_payload: dict, response: dict | None = None, error: str | None = None,
) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            MessageLog(
                tenant_id=tenant_id,
                transaction_type=transaction_type,
                status=status,
                request_payload=request_payload,
                response_payload=response,
                response_status_code=(response or {}).get("status_code"),
                external_reference=(response or {}).get("message_id"),
                error_message=error,
                recipient=recipient,
            )
        )
        await db.commit()


async def _refund(tenant_id: str, channel: str, source: str) -> None:
    from app.core.credits import CreditService

    async with AsyncSessionLocal() as db:
        await CreditService(db, tenant_id).refund(channel, source)


@celery_app.task(base=MessageTask, bind=True)
def send_platform_sms_task(self, tenant_id: str, recipient: str, message: str, source: str):
    """Send an SMS through the platform provider. The credit was reserved by the caller; it is
    refunded if the send fails for good (provider rejection, or the last retry fails)."""
    from app.core.messaging import platform_sms_service

    async def _send():
        service = platform_sms_service()
        payload = {"recipient": recipient, "message": message}
        if service is None:
            await _refund(tenant_id, "sms", source)
            await _log_platform_send(tenant_id, "sms_sent", recipient, "failed", payload,
                                     error="SMS provider is not configured")
            return {"success": False, "error": "SMS provider is not configured"}
        try:
            response = await service.send_sms(recipient=recipient, message=message)
        except Exception as exc:
            if self.request.retries >= self.max_retries:
                await _refund(tenant_id, "sms", source)
                await _log_platform_send(tenant_id, "sms_sent", recipient, "failed", payload, error=str(exc))
            raise
        ok = bool(response.get("success"))
        if not ok:
            await _refund(tenant_id, "sms", source)
        await _log_platform_send(
            tenant_id, "sms_sent", recipient, "success" if ok else "failed", payload, response=response
        )
        return {"success": ok, "message_id": response.get("message_id")}

    return asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task(base=MessageTask, bind=True)
def send_platform_email_task(
    self, tenant_id: str, recipient: str, subject: str, body_html: str | None,
    body_text: str | None, reply_to: str | None, source: str,
):
    """Send an email through the platform provider; refund the credit if it fails."""
    from app.core.system_email import _platform_smtp_service

    async def _send():
        service = _platform_smtp_service()
        payload = {"recipient": recipient, "subject": subject}
        if service is None:
            await _refund(tenant_id, "email", source)
            await _log_platform_send(tenant_id, "email_sent", recipient, "failed", payload,
                                     error="Email provider is not configured")
            return {"success": False, "error": "Email provider is not configured"}
        result = await service.send_email(
            recipient=recipient, subject=subject, body_html=body_html, body_text=body_text,
            reply_to=reply_to,
        )
        ok = bool(result.get("success"))
        if not ok:
            await _refund(tenant_id, "email", source)
        await _log_platform_send(
            tenant_id, "email_sent", recipient, "success" if ok else "failed", payload,
            response=result, error=None if ok else result.get("error"),
        )
        return {"success": ok}

    return asyncio.get_event_loop().run_until_complete(_send())
