"""Redis-backed rate limiting utilities."""

from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import decode_token

_redis_client: Redis | None = None


@dataclass
class RateLimitResult:
    """Rate limit evaluation result."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    identifier: str


def _build_key(scope: str, identifier: str) -> str:
    """Build a namespaced Redis key for rate limiting."""
    return f"{settings.RATE_LIMIT_KEY_PREFIX}:rl:{scope}:{identifier}"


def _extract_client_ip(request: Request) -> str:
    """Extract client IP from request context."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _extract_user_identifier(request: Request) -> str | None:
    """Extract JWT user identifier from Bearer token when available."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None

    try:
        payload = decode_token(token)
    except Exception:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return f"user:{user_id}"


async def get_redis_client() -> Redis:
    """Lazily initialize and return Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    """Close shared Redis client."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def enforce_rate_limit(
    request: Request, scope: str, limit: int, window_seconds: int | None = None
) -> RateLimitResult:
    """
    Enforce rate limit using Redis atomic increment.

    Fail-open behavior is used if Redis is unavailable.
    """
    if limit <= 0:
        return RateLimitResult(
            allowed=True, limit=limit, remaining=0, retry_after=0, identifier="disabled"
        )

    identifier = _extract_user_identifier(request) or f"ip:{_extract_client_ip(request)}"
    key = _build_key(scope, identifier)
    window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

    try:
        redis = await get_redis_client()
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window)

        ttl = await redis.ttl(key)
        retry_after = max(1, ttl) if ttl > 0 else window
        remaining = max(0, limit - current)

        return RateLimitResult(
            allowed=current <= limit,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
            identifier=identifier,
        )
    except Exception:
        # Do not block production traffic when Redis is unavailable.
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=limit,
            retry_after=0,
            identifier=identifier,
        )
