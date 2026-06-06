"""Security headers middleware for HTTP responses."""

from fastapi import Request

from app.core.config import settings


async def add_security_headers(request: Request, call_next):
    """
    Apply baseline HTTP security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff (prevent MIME type sniffing)
    - X-Frame-Options: DENY (prevent clickjacking)
    - Content-Security-Policy: configurable CSP policy
    - Strict-Transport-Security: HSTS (production only)

    Can be disabled via SECURITY_HEADERS_ENABLED setting.
    """
    response = await call_next(request)

    if not settings.SECURITY_HEADERS_ENABLED:
        return response

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = settings.SECURITY_CSP_POLICY

    # HSTS (production only)
    if (
        settings.SECURITY_HSTS_ENABLED
        and settings.ENVIRONMENT.lower() == "production"
    ):
        hsts = f"max-age={settings.SECURITY_HSTS_MAX_AGE}"
        if settings.SECURITY_HSTS_INCLUDE_SUBDOMAINS:
            hsts += "; includeSubDomains"
        if settings.SECURITY_HSTS_PRELOAD:
            hsts += "; preload"
        response.headers["Strict-Transport-Security"] = hsts

    return response
