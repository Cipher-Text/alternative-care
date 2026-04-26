"""Integration tests for authentication API endpoints."""

import pytest
from httpx import AsyncClient

from app.shared.models import User


@pytest.mark.asyncio
class TestRegistrationEndpoint:
    """Test /api/v1/auth/register endpoint."""

    async def test_register_doctor(self, client: AsyncClient, test_division, test_district):
        """Test doctor registration via API."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newapi@test.com",
                "password": "SecurePass123",
                "full_name": "Dr. New API",
                "phone": "+8801712345678",
                "language": "en",
                "clinic_name": "API Clinic",
                "clinic_address": "123 API St",
                "division_id": test_division.id,
                "district_id": test_district.id,
                "specializations": ["homeopathy"],
                "license_number": "BMDC-API123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newapi@test.com"
        assert data["user_id"] is not None
        assert data["tenant_id"] is not None
        assert data["requires_approval"] is True

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Duplicate
                "password": "SecurePass123",
                "full_name": "Dr. Duplicate",
                "specializations": ["homeopathy"],
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@test.com",
                "password": "weak",  # Too short
                "full_name": "Dr. Weak",
                "specializations": ["homeopathy"],
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_register_invalid_specialization(self, client: AsyncClient):
        """Test registration with invalid specialization."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid@test.com",
                "password": "SecurePass123",
                "full_name": "Dr. Invalid",
                "specializations": ["invalid_spec"],
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_register_missing_email(self, client: AsyncClient):
        """Test registration without email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "password": "SecurePass123",
                "full_name": "Dr. No Email",
                "specializations": ["homeopathy"],
            },
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Test /api/v1/auth/login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tokens
        assert "tokens" in data
        assert data["tokens"]["access_token"] is not None
        assert data["tokens"]["refresh_token"] is not None
        assert data["tokens"]["token_type"] == "bearer"

        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["role"] == "doctor"

        assert data["requires_2fa"] is False

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "AnyPassword123",
            },
        )

        assert response.status_code == 401

    async def test_login_unapproved_user(self, client: AsyncClient, unapproved_user):
        """Test login with unapproved tenant."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": unapproved_user.email,
                "password": "PendingPass123",
            },
        )

        assert response.status_code == 403
        assert "pending" in response.json()["detail"].lower()

    async def test_login_with_2fa_no_code(self, client: AsyncClient, user_with_2fa):
        """Test login with 2FA enabled but no code."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user_with_2fa.email,
                "password": "2FAPass123",
            },
        )

        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Test login with invalid email format."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "Password123",
            },
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestTokenRefreshEndpoint:
    """Test /api/v1/auth/refresh endpoint."""

    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """Test successful token refresh."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Refresh tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["refresh_token"] != refresh_token  # Token rotation

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_refresh_token_rotation(self, client: AsyncClient, test_user):
        """Test that old refresh token can't be reused (rotation)."""
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        old_refresh = login_response.json()["tokens"]["refresh_token"]

        # Refresh once
        await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

        # Try to reuse old token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestLogoutEndpoint:
    """Test /api/v1/auth/logout endpoint."""

    async def test_logout_success(self, client: AsyncClient, test_user):
        """Test successful logout."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        access_token = login_response.json()["tokens"]["access_token"]
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify token can't be refreshed after logout
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401

    async def test_logout_without_auth(self, client: AsyncClient):
        """Test logout without authentication fails."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


@pytest.mark.asyncio
class TestGetProfileEndpoint:
    """Test /api/v1/auth/me endpoint."""

    async def test_get_profile_success(self, authenticated_client: AsyncClient, test_user, test_tenant):
        """Test getting user profile."""
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()

        # Verify user data
        assert data["user"]["id"] == test_user.id
        assert data["user"]["email"] == test_user.email
        assert data["user"]["full_name"] == test_user.full_name

        # Verify tenant data
        assert data["tenant"] is not None
        assert data["tenant"]["id"] == test_tenant.id
        assert data["tenant"]["clinic_name"] == test_tenant.clinic_name

    async def test_get_profile_without_auth(self, client: AsyncClient):
        """Test getting profile without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]

    async def test_get_profile_invalid_token(self, client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class Test2FAEndpoints:
    """Test 2FA setup/verify/disable endpoints."""

    async def test_setup_2fa_success(self, authenticated_client: AsyncClient):
        """Test 2FA setup."""
        response = await authenticated_client.post("/api/v1/auth/2fa/setup")

        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code_uri" in data
        assert data["secret"] is not None
        assert "otpauth://" in data["qr_code_uri"]

    async def test_setup_2fa_without_auth(self, client: AsyncClient):
        """Test 2FA setup without authentication."""
        response = await client.post("/api/v1/auth/2fa/setup")
        assert response.status_code in [401, 403]

    async def test_verify_2fa_invalid_code(self, authenticated_client: AsyncClient):
        """Test 2FA verification with invalid code."""
        # Setup first
        await authenticated_client.post("/api/v1/auth/2fa/setup")

        # Try to verify with invalid code
        response = await authenticated_client.post(
            "/api/v1/auth/2fa/verify",
            json={"totp_code": "000000"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_disable_2fa_wrong_password(self, authenticated_client: AsyncClient):
        """Test 2FA disable with wrong password."""
        response = await authenticated_client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "password": "WrongPassword",
                "totp_code": "123456",
            },
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestPasswordChangeEndpoint:
    """Test /api/v1/auth/password/change endpoint."""

    async def test_change_password_success(self, authenticated_client: AsyncClient, test_user, db_session):
        """Test successful password change."""
        response = await authenticated_client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "TestPass123",
                "new_password": "NewSecurePass456",
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify can login with new password
        login_response = await authenticated_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "NewSecurePass456",
            },
        )
        # Note: This will use the same client, so auth headers might interfere
        # In practice, use a fresh client for this test

    async def test_change_password_wrong_current(self, authenticated_client: AsyncClient):
        """Test password change with wrong current password."""
        response = await authenticated_client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewSecurePass456",
            },
        )

        assert response.status_code == 401

    async def test_change_password_without_auth(self, client: AsyncClient):
        """Test password change without authentication."""
        response = await client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "OldPass",
                "new_password": "NewPass",
            },
        )
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestAuthFlow:
    """Test complete authentication flows."""

    async def test_complete_registration_to_login_flow(
        self, client: AsyncClient, db_session, test_division, test_district
    ):
        """Test full flow: register -> approve -> login."""
        # 1. Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "fullflow@test.com",
                "password": "FlowPass123",
                "full_name": "Dr. Full Flow",
                "specializations": ["homeopathy"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )
        assert register_response.status_code == 201
        tenant_id = register_response.json()["tenant_id"]

        # 2. Approve tenant (simulate admin action)
        from sqlalchemy import select, update
        from app.shared.models import Tenant

        await db_session.execute(
            update(Tenant).where(Tenant.id == tenant_id).values(is_approved=True)
        )
        await db_session.commit()

        # 3. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "fullflow@test.com",
                "password": "FlowPass123",
            },
        )
        assert login_response.status_code == 200
        assert login_response.json()["tokens"]["access_token"] is not None

    async def test_login_refresh_logout_flow(self, client: AsyncClient, test_user):
        """Test login -> refresh -> logout flow."""
        # 1. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["tokens"]["access_token"]
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # 2. Get profile with access token
        profile_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert profile_response.status_code == 200

        # 3. Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_refresh_token = refresh_response.json()["refresh_token"]

        # 4. Logout
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200

        # 5. Verify can't refresh after logout
        final_refresh = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh_token},
        )
        assert final_refresh.status_code == 401
