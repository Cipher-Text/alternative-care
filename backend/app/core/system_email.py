"""Platform-level system emails (password reset, email verification).

Distinct from app/modules/integration/tasks.py's send_email_task, which
sends on behalf of a *tenant's* configured SMTP integration
(TenantIntegration row + decrypted credentials). System emails have no
tenant integration to read from — a doctor resetting a forgotten password
hasn't logged in yet, let alone configured SMTP — so this sends via the
platform's own credentials instead, picking one provider by
`settings.EMAIL_PROVIDER`.

SendGrid, Resend, Mailgun, and SMTP2GO all offer an SMTP relay alongside
their HTTP APIs, so this sends over SMTP uniformly via the existing
SMTPService rather than integrating four separate HTTP clients/SDKs — no
new dependency, one send path to test and maintain. A fifth option,
"smtp", is a generic fallback (any host/port/username/password) for a
provider not named above. Relay hosts/ports/username conventions below
are each provider's documented SMTP relay settings, not guessed.
"""

import asyncio
from typing import Callable

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


def _sendgrid_credentials() -> dict | None:
    if not settings.SENDGRID_API_KEY:
        return None
    return {
        "host": "smtp.sendgrid.net",
        "port": 587,
        "username": "apikey",
        "password": settings.SENDGRID_API_KEY,
    }


def _resend_credentials() -> dict | None:
    if not settings.RESEND_API_KEY:
        return None
    return {
        "host": "smtp.resend.com",
        "port": 587,
        # Literally the six letters "resend" for every Resend account —
        # identity comes from the API key sent as the password, not this.
        "username": "resend",
        "password": settings.RESEND_API_KEY,
    }


def _mailgun_credentials() -> dict | None:
    if not (settings.MAILGUN_SMTP_USERNAME and settings.MAILGUN_SMTP_PASSWORD):
        return None
    return {
        "host": settings.MAILGUN_SMTP_HOST,
        "port": 587,
        "username": settings.MAILGUN_SMTP_USERNAME,
        "password": settings.MAILGUN_SMTP_PASSWORD,
    }


def _smtp2go_credentials() -> dict | None:
    if not (settings.SMTP2GO_USERNAME and settings.SMTP2GO_PASSWORD):
        return None
    return {
        "host": "mail.smtp2go.com",
        "port": 587,
        "username": settings.SMTP2GO_USERNAME,
        "password": settings.SMTP2GO_PASSWORD,
    }


def _generic_smtp_credentials() -> dict | None:
    """Fallback for any provider not named above — any SMTP-speaking relay."""
    if not (settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD):
        return None
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USERNAME,
        "password": settings.SMTP_PASSWORD,
        "use_tls": settings.SMTP_USE_TLS,
    }


_PROVIDERS: dict[str, Callable[[], dict | None]] = {
    "sendgrid": _sendgrid_credentials,
    "resend": _resend_credentials,
    "mailgun": _mailgun_credentials,
    "smtp2go": _smtp2go_credentials,
    "smtp": _generic_smtp_credentials,
}


def _platform_smtp_service() -> SMTPService | None:
    """Build an SMTPService for the active provider, or None if unset/misconfigured.

    `settings.EMAIL_PROVIDER` picks the provider; only its own credentials
    need to be set in .env — the other providers' settings can stay blank.
    """
    provider = settings.EMAIL_PROVIDER.strip().lower()
    if not provider:
        return None

    build_credentials = _PROVIDERS.get(provider)
    if build_credentials is None:
        logger.warning(
            "system_email_unknown_provider",
            provider=provider,
            known_providers=sorted(_PROVIDERS),
        )
        return None

    credentials = build_credentials()
    if credentials is None:
        return None

    return SMTPService(
        credentials={
            "use_tls": True,  # default; a provider dict's own use_tls (generic SMTP) wins
            **credentials,
            "from_email": settings.EMAIL_FROM_ADDRESS,
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
    """Send a platform system email. No-ops with a logged warning when
    EMAIL_PROVIDER isn't set (or its credentials are incomplete), rather
    than failing the calling request — a doctor can still request a
    password reset locally, they just won't receive an email until a
    provider is configured.
    """
    service = _platform_smtp_service()
    if service is None:
        logger.warning(
            "system_email_skipped_no_provider",
            recipient=recipient,
            subject=subject,
            reason=(
                f"EMAIL_PROVIDER={settings.EMAIL_PROVIDER!r} not set or its "
                "credentials are incomplete"
            ),
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
