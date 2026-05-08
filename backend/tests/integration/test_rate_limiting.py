"""Integration tests for rate limiting middleware."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.rate_limit import RateLimitResult
from app.core.security import create_access_token
from app.main import app


@pytest.mark.asyncio
async def test_login_route_uses_auth_login_scope(monkeypatch) -> None:
    """Login route should evaluate the dedicated auth_login scope."""
    from app import main as main_module

    async def always_limited(
        request, scope: str, limit: int, window_seconds: int | None = None
    ) -> RateLimitResult:
        assert scope == "auth_login"
        assert limit == settings.RATE_LIMIT_LOGIN_PER_MINUTE
        assert window_seconds is not None
        return RateLimitResult(
            allowed=False,
            limit=limit,
            remaining=0,
            retry_after=17,
            identifier="ip:test",
        )

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


@pytest.mark.asyncio
async def test_general_api_rate_limit_isolated_per_user_jwt_sub() -> None:
    """Authenticated users should be rate-limited independently by JWT sub."""
    prefix = f"test-user-scope-{uuid.uuid4()}"
    original_prefix = settings.RATE_LIMIT_KEY_PREFIX
    original_limit = settings.RATE_LIMIT_PER_MINUTE
    original_window = settings.RATE_LIMIT_WINDOW_SECONDS
    original_ai_limit = settings.RATE_LIMIT_AI_PER_HOUR

    settings.RATE_LIMIT_KEY_PREFIX = prefix
    settings.RATE_LIMIT_PER_MINUTE = 1
    settings.RATE_LIMIT_WINDOW_SECONDS = 60
    settings.RATE_LIMIT_AI_PER_HOUR = 1

    token_user_1 = create_access_token(
        {
            "sub": "user-1",
            "tenant_id": "tenant-1",
            "role": "doctor",
            "email": "user1@test.com",
            "plan": "pro",
        }
    )
    token_user_2 = create_access_token(
        {
            "sub": "user-2",
            "tenant_id": "tenant-1",
            "role": "doctor",
            "email": "user2@test.com",
            "plan": "pro",
        }
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            first_user_1 = await client.post(
                "/api/v1/ai/query",
                json={"query": "hi"},
                headers={"Authorization": f"Bearer {token_user_1}"},
            )
            assert first_user_1.status_code == 501

            first_user_2 = await client.post(
                "/api/v1/ai/query",
                json={"query": "hi"},
                headers={"Authorization": f"Bearer {token_user_2}"},
            )
            assert first_user_2.status_code == 501

            second_user_1 = await client.post(
                "/api/v1/ai/query",
                json={"query": "hi"},
                headers={"Authorization": f"Bearer {token_user_1}"},
            )
            assert second_user_1.status_code == 429
            assert second_user_1.json().get("scope") == "ai_query"
    finally:
        settings.RATE_LIMIT_KEY_PREFIX = original_prefix
        settings.RATE_LIMIT_PER_MINUTE = original_limit
        settings.RATE_LIMIT_WINDOW_SECONDS = original_window
        settings.RATE_LIMIT_AI_PER_HOUR = original_ai_limit


@pytest.mark.asyncio
async def test_ai_query_rate_limit_enforced_with_dedicated_scope() -> None:
    """AI query endpoint should enforce its own hourly quota scope."""
    prefix = f"test-ai-scope-{uuid.uuid4()}"
    original_prefix = settings.RATE_LIMIT_KEY_PREFIX
    original_ai_limit = settings.RATE_LIMIT_AI_PER_HOUR
    original_ai_window = settings.RATE_LIMIT_AI_WINDOW_SECONDS

    settings.RATE_LIMIT_KEY_PREFIX = prefix
    settings.RATE_LIMIT_AI_PER_HOUR = 1
    settings.RATE_LIMIT_AI_WINDOW_SECONDS = 3600

    token_user = create_access_token(
        {
            "sub": "ai-user-1",
            "tenant_id": "tenant-1",
            "role": "doctor",
            "email": "ai1@test.com",
            "plan": "pro",
        }
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            first = await client.post(
                "/api/v1/ai/query",
                json={"query": "hello"},
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert first.status_code == 501

            second = await client.post(
                "/api/v1/ai/query",
                json={"query": "hello again"},
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert second.status_code == 429
            assert second.json().get("scope") == "ai_query"
    finally:
        settings.RATE_LIMIT_KEY_PREFIX = original_prefix
        settings.RATE_LIMIT_AI_PER_HOUR = original_ai_limit
        settings.RATE_LIMIT_AI_WINDOW_SECONDS = original_ai_window


@pytest.mark.asyncio
async def test_ai_query_scope_independent_from_general_api_scope() -> None:
    """AI quota and general API quota should not consume each other."""
    prefix = f"test-ai-independence-{uuid.uuid4()}"
    original_prefix = settings.RATE_LIMIT_KEY_PREFIX
    original_api_limit = settings.RATE_LIMIT_PER_MINUTE
    original_ai_limit = settings.RATE_LIMIT_AI_PER_HOUR
    original_window = settings.RATE_LIMIT_WINDOW_SECONDS
    original_ai_window = settings.RATE_LIMIT_AI_WINDOW_SECONDS

    settings.RATE_LIMIT_KEY_PREFIX = prefix
    settings.RATE_LIMIT_PER_MINUTE = 1
    settings.RATE_LIMIT_AI_PER_HOUR = 1
    settings.RATE_LIMIT_WINDOW_SECONDS = 60
    settings.RATE_LIMIT_AI_WINDOW_SECONDS = 3600

    token_user = create_access_token(
        {
            "sub": "ai-user-2",
            "tenant_id": "tenant-1",
            "role": "doctor",
            "email": "ai2@test.com",
            "plan": "pro",
        }
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            ai_first = await client.post(
                "/api/v1/ai/query",
                json={"query": "q1"},
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert ai_first.status_code == 501

            # Different scope should still have its own allowance.
            api_first = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert api_first.status_code in [200, 401, 403, 404]

            ai_second = await client.post(
                "/api/v1/ai/query",
                json={"query": "q2"},
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert ai_second.status_code == 429
            assert ai_second.json().get("scope") == "ai_query"

            api_second = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token_user}"},
            )
            assert api_second.status_code == 429
            assert api_second.json().get("scope") == "api"
    finally:
        settings.RATE_LIMIT_KEY_PREFIX = original_prefix
        settings.RATE_LIMIT_PER_MINUTE = original_api_limit
        settings.RATE_LIMIT_AI_PER_HOUR = original_ai_limit
        settings.RATE_LIMIT_WINDOW_SECONDS = original_window
        settings.RATE_LIMIT_AI_WINDOW_SECONDS = original_ai_window


@pytest.mark.asyncio
async def test_rate_limit_429_increments_prometheus_counter(monkeypatch) -> None:
    """Rate-limit blocks should increment per-scope Prometheus counters."""
    from app import main as main_module

    async def always_limited(
        request, scope: str, limit: int, window_seconds: int | None = None
    ) -> RateLimitResult:
        return RateLimitResult(
            allowed=False,
            limit=limit,
            remaining=0,
            retry_after=5,
            identifier="user:test",
        )

    monkeypatch.setattr(main_module, "enforce_rate_limit", always_limited)
    before = main_module.rate_limit_block_total.labels(scope="api")._value.get()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    after = main_module.rate_limit_block_total.labels(scope="api")._value.get()
    assert response.status_code == 429
    assert after == before + 1


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_rate_limit_counter(monkeypatch) -> None:
    """Metrics endpoint should expose throttling counter after a blocked request."""
    from app import main as main_module

    async def always_limited(
        request, scope: str, limit: int, window_seconds: int | None = None
    ) -> RateLimitResult:
        return RateLimitResult(
            allowed=False,
            limit=limit,
            remaining=0,
            retry_after=5,
            identifier="user:test",
        )

    monkeypatch.setattr(main_module, "enforce_rate_limit", always_limited)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        blocked = await client.get("/api/v1/auth/me")
        assert blocked.status_code == 429

        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200
        assert "altcare_rate_limit_block_total" in metrics_response.text
        assert 'scope="api"' in metrics_response.text
