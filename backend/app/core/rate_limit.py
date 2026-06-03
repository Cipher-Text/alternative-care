"""Redis-backed rate limiting utilities."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None
_redis_failure_count = 0
_redis_last_failure: datetime | None = None
_in_memory_fallback: dict[str, tuple[int, datetime]] = {}


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


def _use_in_memory_fallback(key: str, limit: int, window: int) -> RateLimitResult:
    """
    In-memory fallback rate limiting when Redis is unavailable.

    SECURITY: This is a temporary circuit breaker. It's less accurate than Redis
    (process-local only) but prevents complete bypass of rate limits.
    """
    now = datetime.now(timezone.utc)

    # Clean up old entries
    _in_memory_fallback.clear() if len(_in_memory_fallback) > 10000 else None

    if key in _in_memory_fallback:
        count, expires_at = _in_memory_fallback[key]
        if now < expires_at:
            count += 1
            _in_memory_fallback[key] = (count, expires_at)
            remaining = max(0, limit - count)
            retry_after = int((expires_at - now).total_seconds())
            return RateLimitResult(
                allowed=count <= limit,
                limit=limit,
                remaining=remaining,
                retry_after=retry_after,
                identifier=key,
            )

    # New window
    expires_at = now + timedelta(seconds=window)
    _in_memory_fallback[key] = (1, expires_at)

    return RateLimitResult(
        allowed=True,
        limit=limit,
        remaining=limit - 1,
        retry_after=window,
        identifier=key,
    )


async def enforce_rate_limit(
    request: Request, scope: str, limit: int, window_seconds: int | None = None
) -> RateLimitResult:
    """
    Enforce rate limit using Redis atomic increment with in-memory fallback.

    SECURITY: Uses circuit breaker pattern - if Redis fails repeatedly,
    falls back to in-memory rate limiting instead of allowing unlimited requests.
    """
    global _redis_failure_count, _redis_last_failure

    if limit <= 0:
        return RateLimitResult(
            allowed=True, limit=limit, remaining=0, retry_after=0, identifier="disabled"
        )

    identifier = _extract_user_identifier(request) or f"ip:{_extract_client_ip(request)}"
    key = _build_key(scope, identifier)
    window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

    # Circuit breaker: if Redis failed recently, use in-memory fallback immediately
    if _redis_failure_count >= 3 and _redis_last_failure:
        time_since_failure = (datetime.now(timezone.utc) - _redis_last_failure).total_seconds()
        if time_since_failure < 60:  # 60 second circuit break
            logger.warning(
                f"Rate limiting using in-memory fallback (Redis circuit breaker active)"
            )
            return _use_in_memory_fallback(key, limit, window)

    try:
        redis = await get_redis_client()
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window)

        ttl = await redis.ttl(key)
        retry_after = max(1, ttl) if ttl > 0 else window
        remaining = max(0, limit - current)

        # Reset failure counter on success
        _redis_failure_count = 0
        _redis_last_failure = None

        return RateLimitResult(
            allowed=current <= limit,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
            identifier=identifier,
        )
    except Exception as e:
        # Track failures for circuit breaker
        _redis_failure_count += 1
        _redis_last_failure = datetime.now(timezone.utc)

        logger.error(
            f"Rate limit Redis error (failure #{_redis_failure_count}): {e}. "
            f"Using in-memory fallback."
        )

        # SECURITY: Use in-memory fallback instead of allowing unlimited requests
        return _use_in_memory_fallback(key, limit, window)
