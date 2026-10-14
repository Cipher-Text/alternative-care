"""Platform-owned messaging providers, configured only from the environment.

Clinics never hold provider credentials; they send through these providers and are charged
credits (see `app/core/credits.py`). Secrets are read from settings and never logged or returned.
"""

from app.core.config import settings
from app.modules.messaging.providers.bulksmsbd_service import BulkSMSBDService


def platform_sms_service() -> BulkSMSBDService | None:
    """The configured SMS provider, or None when SMS is not set up."""
    if settings.SMS_PROVIDER.strip().lower() != "bulksmsbd":
        return None
    if not (settings.BULKSMSBD_API_KEY and settings.BULKSMSBD_SENDER_ID):
        return None
    credentials = {
        "api_key": settings.BULKSMSBD_API_KEY,
        "sender_id": settings.BULKSMSBD_SENDER_ID,
    }
    if settings.BULKSMSBD_API_URL:
        credentials["api_url"] = settings.BULKSMSBD_API_URL
    return BulkSMSBDService(credentials=credentials)


def sms_configured() -> bool:
    return platform_sms_service() is not None


def email_configured() -> bool:
    # imported lazily: system_email -> messaging providers -> routes -> this module
    from app.core.system_email import _platform_smtp_service

    return _platform_smtp_service() is not None


def messaging_status() -> dict:
    """Configured-or-not per channel. Deliberately returns no credential material."""
    return {
        "sms": {"provider": settings.SMS_PROVIDER or None, "configured": sms_configured()},
        "email": {"provider": settings.EMAIL_PROVIDER or None, "configured": email_configured()},
    }
