"""Integration tests for rate limiting middleware."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.rate_limit import RateLimitResult
from app.main import app


@pytest.mark.asyncio
async def test_login_route_uses_auth_login_scope(monkeypatch) -> None:
    """Login route should evaluate the dedicated auth_login scope."""
    from app import main as main_module

    async def always_limited(request, scope: str, limit: int) -> RateLimitResult:
        assert scope == "auth_login"
        assert limit == settings.RATE_LIMIT_LOGIN_PER_MINUTE
        return RateLimitResult(allowed=False, limit=limit, remaining=0, retry_after=17)

    monkeypatch.setattr(main_module, "enforce_rate_limit", always_limited)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "any@test.com", "password": "AnyPass123"},
        )

    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "17"
    assert response.json().get("scope") == "auth_login"


@pytest.mark.asyncio
async def test_general_api_rate_limit_enforced() -> None:
    """General API requests should be Redis rate limited independently."""
    prefix = f"test-api-{uuid.uuid4()}"
    original_prefix = settings.RATE_LIMIT_KEY_PREFIX
    original_limit = settings.RATE_LIMIT_PER_MINUTE
    original_window = settings.RATE_LIMIT_WINDOW_SECONDS

    settings.RATE_LIMIT_KEY_PREFIX = prefix
    settings.RATE_LIMIT_PER_MINUTE = 2
    settings.RATE_LIMIT_WINDOW_SECONDS = 60

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            for _ in range(2):
                response = await client.get("/api/v1/auth/me")
                assert response.status_code in [401, 403]
                assert response.headers.get("X-RateLimit-Limit") == "2"

            limited = await client.get("/api/v1/auth/me")
            assert limited.status_code == 429
            assert limited.headers.get("Retry-After") is not None
            assert limited.json().get("scope") == "api"
    finally:
        settings.RATE_LIMIT_KEY_PREFIX = original_prefix
        settings.RATE_LIMIT_PER_MINUTE = original_limit
        settings.RATE_LIMIT_WINDOW_SECONDS = original_window
