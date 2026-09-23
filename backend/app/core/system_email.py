"""Platform-level system emails (password reset, email verification).

Distinct from app/modules/integration/tasks.py's send_email_task, which
sends on behalf of a *tenant's* configured SMTP integration
(TenantIntegration row + decrypted credentials). System emails have no
tenant integration to read from — a doctor resetting a forgotten password
hasn't logged in yet, let alone configured SMTP — so this sends via the
platform's own credentials (SENDGRID_API_KEY, over SMTP relay) instead.
"""

import asyncio

import structlog
from celery import Task

from app.core.celery import celery_app
from app.core.config import settings
from app.modules.integration.providers.smtp_service import SMTPService

logger = structlog.get_logger(__name__)


class SystemEmailTask(Task):
    """Base task with retry behavior matching the tenant-email task."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


def _platform_smtp_service() -> SMTPService | None:
    """Build an SMTPService from platform settings, or None if unconfigured.

    Uses SendGrid's SMTP relay (smtp.sendgrid.net) rather than the SendGrid
    HTTP API, so no new dependency is needed beyond stdlib smtplib — the
    same approach app/modules/integration/providers/smtp_service.py already
    uses for tenant-configured SMTP.
    """
    if not settings.SENDGRID_API_KEY:
        return None

    return SMTPService(
        credentials={
            "host": "smtp.sendgrid.net",
            "port": 587,
            "username": "apikey",
            "password": settings.SENDGRID_API_KEY,
            "use_tls": True,
            "from_email": settings.SENDGRID_FROM_EMAIL,
        }
    )


@celery_app.task(base=SystemEmailTask, bind=True)
def send_system_email_task(
    self,
    recipient: str,
    subject: str,
    body_html: str | None = None,
    body_text: str | None = None,
    **kwargs,
):
    """Send a platform system email. No-ops with a logged warning in dev
    when SENDGRID_API_KEY isn't set, rather than failing the calling
    request — a doctor can still request a password reset locally, they
    just won't receive an email until SendGrid is configured.
    """
    service = _platform_smtp_service()
    if service is None:
        logger.warning(
            "system_email_skipped_no_provider",
            recipient=recipient,
            subject=subject,
            reason="SENDGRID_API_KEY not configured",
        )
        return {"success": False, "skipped": True}

    async def _send():
        return await service.send_email(
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_send())

    if not result.get("success"):
        logger.error(
            "system_email_send_failed",
            recipient=recipient,
            subject=subject,
            error=result.get("error"),
        )

    return result
