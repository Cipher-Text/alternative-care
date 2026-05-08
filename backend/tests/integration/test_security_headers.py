"""Integration tests for baseline HTTP security headers."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_security_headers_present_on_health() -> None:
    """Health endpoint should include baseline security headers."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Content-Security-Policy") == settings.SECURITY_CSP_POLICY


@pytest.mark.asyncio
async def test_security_headers_present_on_auth_route_without_token() -> None:
    """Auth endpoints should include headers even on auth failures."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code in [401, 403]
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Content-Security-Policy") == settings.SECURITY_CSP_POLICY


@pytest.mark.asyncio
async def test_hsts_enabled_in_production_only(monkeypatch) -> None:
    """HSTS should be emitted only when environment is production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        prod_response = await client.get("/health")
    assert "Strict-Transport-Security" in prod_response.headers

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        dev_response = await client.get("/health")
    assert "Strict-Transport-Security" not in dev_response.headers

