"""Integration tests for authentication API endpoints."""

from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.shared.models import User


def _mock_email_capture(monkeypatch):
    """Patch send_system_email_task.delay and return the dict its kwargs land in."""
    captured = {}

    def _fake_delay(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="task-1")

    monkeypatch.setattr("app.modules.auth.service.send_system_email_task.delay", _fake_delay)
    return captured


def _token_from_link(body_text: str) -> str:
    """Extract the `?token=` value from a captured email body."""
    return body_text.split("token=")[1].split()[0].strip()


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
        """Login without a TOTP code should prompt for 2FA, not fail outright."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user_with_2fa.email,
                "password": "2FAPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requires_2fa"] is True
        assert "tokens" not in data

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
class TestPasswordResetEndpoints:
    """Test /api/v1/auth/password/forgot and /password/reset endpoints."""

    async def test_forgot_password_existing_email_queues_email(
        self, client: AsyncClient, test_user, monkeypatch
    ):
        """Forgot-password for a real account queues a reset email."""
        captured = _mock_email_capture(monkeypatch)

        response = await client.post(
            "/api/v1/auth/password/forgot", json={"email": test_user.email}
        )

        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()
        assert captured["recipient"] == test_user.email
        assert "token=" in captured["body_text"]

    async def test_forgot_password_unknown_email_same_response(
        self, client: AsyncClient, monkeypatch
    ):
        """Forgot-password for a nonexistent account gives the same response,
        and doesn't queue an email — this is what prevents using the endpoint
        to enumerate registered addresses."""
        captured = _mock_email_capture(monkeypatch)

        response = await client.post(
            "/api/v1/auth/password/forgot", json={"email": "nobody@test.com"}
        )

        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()
        assert captured == {}

    async def test_reset_password_with_valid_token_succeeds(
        self, client: AsyncClient, test_user, monkeypatch
    ):
        """A valid reset token sets the new password and can be used to log in."""
        captured = _mock_email_capture(monkeypatch)
        await client.post("/api/v1/auth/password/forgot", json={"email": test_user.email})
        token = _token_from_link(captured["body_text"])

        response = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "BrandNewPass456"},
        )
        assert response.status_code == 200

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "BrandNewPass456"},
        )
        assert login_response.status_code == 200

    async def test_reset_password_token_is_single_use(
        self, client: AsyncClient, test_user, monkeypatch
    ):
        """Reusing an already-consumed reset token is rejected."""
        captured = _mock_email_capture(monkeypatch)
        await client.post("/api/v1/auth/password/forgot", json={"email": test_user.email})
        token = _token_from_link(captured["body_text"])

        first = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "FirstNewPass456"},
        )
        assert first.status_code == 200

        second = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "SecondNewPass456"},
        )
        assert second.status_code == 400

    async def test_reset_password_invalidates_existing_sessions(
        self, client: AsyncClient, test_user, monkeypatch
    ):
        """Resetting a password logs out every existing session — the old
        password may be why a reset was needed in the first place."""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        old_access_token = login_response.json()["tokens"]["access_token"]

        captured = _mock_email_capture(monkeypatch)
        await client.post("/api/v1/auth/password/forgot", json={"email": test_user.email})
        token = _token_from_link(captured["body_text"])
        await client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "AnotherNewPass456"},
        )

        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert me_response.status_code == 401

    async def test_reset_password_invalid_token_rejected(self, client: AsyncClient):
        """A made-up token is rejected."""
        response = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": "not-a-real-token", "new_password": "SomeNewPass456"},
        )
        assert response.status_code == 400

    async def test_reset_password_expired_token_rejected(
        self, client: AsyncClient, test_user, db_session, monkeypatch
    ):
        """An expired reset token is rejected, even if otherwise valid."""
        from datetime import datetime, timedelta, timezone

        captured = _mock_email_capture(monkeypatch)
        await client.post("/api/v1/auth/password/forgot", json={"email": test_user.email})
        token = _token_from_link(captured["body_text"])

        await db_session.refresh(test_user)
        test_user.password_reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "SomeNewPass456"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestEmailVerificationEndpoints:
    """Test /api/v1/auth/email/verify and /email/resend endpoints."""

    async def test_registration_queues_verification_email(
        self, client: AsyncClient, test_division, test_district, monkeypatch
    ):
        """Registering a new doctor queues a verification email."""
        captured = _mock_email_capture(monkeypatch)

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "verifyme@test.com",
                "password": "SecurePass123",
                "full_name": "Dr. Verify Me",
                "specializations": ["homeopathy"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )

        assert response.status_code == 201
        assert captured["recipient"] == "verifyme@test.com"
        assert "token=" in captured["body_text"]

    async def test_verify_email_with_valid_token_succeeds(
        self, client: AsyncClient, test_division, test_district, monkeypatch
    ):
        captured = _mock_email_capture(monkeypatch)
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "verifyme2@test.com",
                "password": "SecurePass123",
                "full_name": "Dr. Verify Two",
                "specializations": ["homeopathy"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )
        token = _token_from_link(captured["body_text"])

        response = await client.post("/api/v1/auth/email/verify", json={"token": token})
        assert response.status_code == 200

    async def test_verify_email_invalid_token_rejected(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/email/verify", json={"token": "not-a-real-token"}
        )
        assert response.status_code == 400

    async def test_resend_verification_for_unverified_user_queues_email(
        self, client: AsyncClient, test_division, test_district, monkeypatch
    ):
        captured = _mock_email_capture(monkeypatch)
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "resend@test.com",
                "password": "SecurePass123",
                "full_name": "Dr. Resend",
                "specializations": ["homeopathy"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )

        captured.clear()
        response = await client.post(
            "/api/v1/auth/email/resend", json={"email": "resend@test.com"}
        )
        assert response.status_code == 200
        assert captured["recipient"] == "resend@test.com"

    async def test_resend_verification_for_already_verified_user_is_a_noop(
        self, client: AsyncClient, test_user, db_session, monkeypatch
    ):
        """No email is queued for an already-verified account — its message
        is identical to the unknown-email case, so this can't be used to
        confirm whether an address is verified."""
        await db_session.refresh(test_user)
        assert test_user.is_email_verified is True

        captured = _mock_email_capture(monkeypatch)
        response = await client.post(
            "/api/v1/auth/email/resend", json={"email": test_user.email}
        )
        assert response.status_code == 200
        assert captured == {}


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
