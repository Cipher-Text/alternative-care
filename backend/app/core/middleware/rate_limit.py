"""Rate limiting middleware for API endpoints."""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter

from app.core.config import settings

logger = structlog.get_logger(__name__)

rate_limit_block_total = Counter(
    "altcare_rate_limit_block_total",
    "Total number of blocked requests due to rate limiting.",
    ["scope"],
)


async def rate_limit_middleware(request: Request, call_next):
    """
    Apply baseline rate limiting for auth login and API routes.

    Scopes:
    - auth_login: 10 req/min per IP (POST /api/v1/auth/login, /api/v1/auth/google)
    - auth_sensitive: same limit as auth_login — password reset and email
      verification requests, which send an email and can otherwise be used
      to spam a victim's inbox or probe for registered addresses
    - ai_query: 100 req/hour per user (POST /api/v1/ai/query)
    - api: 100 req/min per IP (all /api/v1/*)

    Returns:
    - 429 with Retry-After header if rate limit exceeded
    - Original response with X-RateLimit-* headers otherwise
    """
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    # Imported here (rather than at module load) so tests can monkeypatch
    # `app.main.enforce_rate_limit` and have that override take effect.
    from app.main import enforce_rate_limit

    path = request.url.path
    scope = None
    limit = None
    window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS

    # Determine rate limit scope
    sensitive_auth_paths = {
        f"{settings.API_V1_PREFIX}/auth/password/forgot",
        f"{settings.API_V1_PREFIX}/auth/password/reset",
        f"{settings.API_V1_PREFIX}/auth/email/verify",
        f"{settings.API_V1_PREFIX}/auth/email/resend",
    }

    login_shaped_paths = {
        f"{settings.API_V1_PREFIX}/auth/login",
        f"{settings.API_V1_PREFIX}/auth/google",
    }

    if request.method == "POST" and path in login_shaped_paths:
        scope = "auth_login"
        limit = settings.RATE_LIMIT_LOGIN_PER_MINUTE
    elif request.method == "POST" and path in sensitive_auth_paths:
        scope = "auth_sensitive"
        limit = settings.RATE_LIMIT_LOGIN_PER_MINUTE
    elif request.method == "POST" and path == f"{settings.API_V1_PREFIX}/ai/query":
        scope = "ai_query"
        limit = settings.RATE_LIMIT_AI_PER_HOUR
        window_seconds = settings.RATE_LIMIT_AI_WINDOW_SECONDS
    elif path.startswith(settings.API_V1_PREFIX):
        scope = "api"
        limit = settings.RATE_LIMIT_PER_MINUTE

    # Enforce rate limit if applicable
    if scope and limit is not None:
        result = await enforce_rate_limit(
            request, scope=scope, limit=limit, window_seconds=window_seconds
        )

        if not result.allowed:
            # Log rate limit block
            rate_limit_block_total.labels(scope=scope).inc()
            logger.warning(
                "rate_limit_exceeded",
                scope=scope,
                path=path,
                method=request.method,
                identifier=result.identifier,
                retry_after=result.retry_after,
                limit=result.limit,
            )

            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "scope": scope,
                    "limit": result.limit,
                    "retry_after": result.retry_after,
                },
                headers={"Retry-After": str(result.retry_after)},
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        return response

    # No rate limit applicable
    return await call_next(request)
