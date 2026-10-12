"""Sending patient verification codes. The platform pays for these (ADR 009), so they do not touch a
clinic's credit balance; abuse is limited in `otp.py`. The code is never logged outside development."""

import structlog
from fastapi import HTTPException, status

from app.core.config import settings

logger = structlog.get_logger()


async def dispatch_sms(phone: str, message: str, code: str) -> None:
    """Send `message` to `phone` through the platform SMS provider.

    With no provider configured: development logs the code to the server log (so the flow can be
    tried locally); anything else refuses, so a code is never silently lost."""
    from app.core.messaging import platform_sms_service  # lazy: avoids an import cycle with integrations

    service = platform_sms_service()
    if service is None:
        if settings.ENVIRONMENT == "development":
            logger.warning("otp_dev_code", phone=phone[:6] + "***", code=code)
            return
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SMS is not available right now")
    try:
        result = await service.send_sms(recipient=phone, message=message)
    except Exception as exc:  # noqa: BLE001
        logger.warning("otp_sms_failed", phone=phone[:6] + "***")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not send the code. Try again.") from exc
    if not result.get("success"):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not send the code. Try again.")
