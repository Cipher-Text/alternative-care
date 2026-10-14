"""Celery tasks for integration operations."""

import asyncio

from celery import Task
from sqlalchemy import select

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_credentials
from app.modules.integration.factory import IntegrationProviderFactory
from app.shared.models import IntegrationLog, IntegrationProvider, TenantIntegration


class IntegrationTask(Task):
    """Base task with error handling and logging."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@celery_app.task(base=IntegrationTask, bind=True)
def send_sms_task(
    self, tenant_id: str, tenant_integration_id: int, recipient: str, message: str, **kwargs
):
    """Send SMS via configured provider.

    Args:
        tenant_id: Tenant ID
        tenant_integration_id: TenantIntegration ID
        recipient: Phone number
        message: SMS message text

    Returns:
        Dict with send results
    """

    async def _send():
        async with AsyncSessionLocal() as db:
            try:
                # Load integration
                result = await db.execute(
                    select(TenantIntegration, IntegrationProvider)
                    .join(IntegrationProvider)
                    .where(TenantIntegration.id == tenant_integration_id)
                )
                row = result.first()

                if not row:
                    raise ValueError(
                        f"Integration {tenant_integration_id} not found"
                    )

                integration, provider = row

                # Decrypt credentials
                credentials = decrypt_credentials(integration.encrypted_credentials)

                # Create provider service
                service = IntegrationProviderFactory.create_provider(
                    provider_name=provider.name,
                    credentials=credentials,
                )

                # Send SMS
                response = await service.send_sms(recipient=recipient, message=message)

                # Log success
                log = IntegrationLog(
                    tenant_id=tenant_id,
                    tenant_integration_id=tenant_integration_id,
                    transaction_type="sms_sent",
                    status="success" if response.get("success") else "failed",
                    request_payload={"recipient": recipient, "message": message},
                    response_payload=response,
                    response_status_code=response.get("status_code"),
                    external_reference=response.get("message_id"),
                    recipient=recipient,
                )
                db.add(log)
                await db.commit()

                return {
                    "success": response.get("success"),
                    "message_id": response.get("message_id"),
                    "log_id": log.id,
                }

            except Exception as e:
                # Log failure
                log = IntegrationLog(
                    tenant_id=tenant_id,
                    tenant_integration_id=tenant_integration_id,
                    transaction_type="sms_sent",
                    status="failed",
                    request_payload={"recipient": recipient, "message": message},
                    error_message=str(e),
                    recipient=recipient,
                )
                db.add(log)
                await db.commit()

                raise

    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send())


@celery_app.task(base=IntegrationTask, bind=True)
def send_email_task(
    self,
    tenant_id: str,
    tenant_integration_id: int,
    recipient: str,
    subject: str,
    body_html: str | None = None,
    body_text: str | None = None,
    **kwargs,
):
    """Send email via configured provider.

    Args:
        tenant_id: Tenant ID
        tenant_integration_id: TenantIntegration ID
        recipient: Email address
        subject: Email subject
        body_html: HTML body (optional)
        body_text: Plain text body (optional)

    Returns:
        Dict with send results
    """

    async def _send():
        async with AsyncSessionLocal() as db:
            try:
                # Load integration
                result = await db.execute(
                    select(TenantIntegration, IntegrationProvider)
                    .join(IntegrationProvider)
                    .where(TenantIntegration.id == tenant_integration_id)
                )
                row = result.first()

                if not row:
                    raise ValueError(
                        f"Integration {tenant_integration_id} not found"
                    )

                integration, provider = row

                # Decrypt credentials
                credentials = decrypt_credentials(integration.encrypted_credentials)

                # Create provider service
                service = IntegrationProviderFactory.create_provider(
                    provider_name=provider.name,
                    credentials=credentials,
                )

                # Send email
                response = await service.send_email(
                    recipient=recipient,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                )

                # Log result
                log = IntegrationLog(
                    tenant_id=tenant_id,
                    tenant_integration_id=tenant_integration_id,
                    transaction_type="email_sent",
                    status="success" if response.get("success") else "failed",
                    request_payload={
                        "recipient": recipient,
                        "subject": subject,
                        "has_html": body_html is not None,
                        "has_text": body_text is not None,
                    },
                    response_payload=response,
                    recipient=recipient,
                    error_message=response.get("error"),
                )
                db.add(log)
                await db.commit()

                return {
                    "success": response.get("success"),
                    "log_id": log.id,
                }

            except Exception as e:
                # Log failure
                log = IntegrationLog(
                    tenant_id=tenant_id,
                    tenant_integration_id=tenant_integration_id,
                    transaction_type="email_sent",
                    status="failed",
                    request_payload={
                        "recipient": recipient,
                        "subject": subject,
                    },
                    error_message=str(e),
                    recipient=recipient,
                )
                db.add(log)
                await db.commit()

                raise

    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send())


# ===== Platform-owned sends (credits already reserved by the caller) =====


async def _log_platform_send(
    tenant_id: str, transaction_type: str, recipient: str, status: str,
    request_payload: dict, response: dict | None = None, error: str | None = None,
) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            IntegrationLog(
                tenant_id=tenant_id,
                tenant_integration_id=None,
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


@celery_app.task(base=IntegrationTask, bind=True)
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


@celery_app.task(base=IntegrationTask, bind=True)
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
