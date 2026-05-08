"""Redis-backed rate limiting utilities."""

from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


@dataclass
class RateLimitResult:
    """Rate limit evaluation result."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int


def _build_key(scope: str, client_ip: str) -> str:
    """Build a namespaced Redis key for rate limiting."""
    return f"{settings.RATE_LIMIT_KEY_PREFIX}:rl:{scope}:{client_ip}"


def _extract_client_ip(request: Request) -> str:
    """Extract client IP from request context."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


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


async def enforce_rate_limit(request: Request, scope: str, limit: int) -> RateLimitResult:
    """
    Enforce rate limit using Redis atomic increment.

    Fail-open behavior is used if Redis is unavailable.
    """
    if limit <= 0:
        return RateLimitResult(allowed=True, limit=limit, remaining=0, retry_after=0)

    client_ip = _extract_client_ip(request)
    key = _build_key(scope, client_ip)
    window = settings.RATE_LIMIT_WINDOW_SECONDS

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
        )
    except Exception:
        # Do not block production traffic when Redis is unavailable.
        return RateLimitResult(allowed=True, limit=limit, remaining=limit, retry_after=0)

