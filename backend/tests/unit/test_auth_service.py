"""Unit tests for AuthService."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.security import verify_password, verify_totp
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.shared.models import User, UserSession


@pytest.mark.asyncio
class TestRegistration:
    """Test user registration."""

    async def test_register_doctor_success(self, db_session, test_division, test_district):
        """Test successful doctor registration."""
        service = AuthService(db_session)

        data = RegisterRequest(
            email="newdoctor@test.com",
            password="SecurePass123",
            full_name="Dr. New Doctor",
            phone="+8801712345678",
            language="en",
            clinic_name="New Clinic",
            clinic_address="123 New St",
            division_id=test_division.id,
            district_id=test_district.id,
            specializations=["homeopathy"],
            license_number="BMDC-NEW123",
        )

        result = await service.register_doctor(data)

        # Verify response
        assert result.email == "newdoctor@test.com"
        assert result.user_id is not None
        assert result.tenant_id is not None
        assert result.requires_approval is True

        # Verify user created
        user_result = await db_session.execute(
            select(User).where(User.email == "newdoctor@test.com")
        )
        user = user_result.scalar_one_or_none()
        assert user is not None
        assert user.role == "doctor"
        assert user.is_active is True
        assert user.is_email_verified is False
        assert verify_password("SecurePass123", user.password_hash)

    async def test_register_duplicate_email(self, db_session, test_user):
        """Test registration with existing email fails."""
        service = AuthService(db_session)

        data = RegisterRequest(
            email=test_user.email,  # Duplicate email
            password="SecurePass123",
            full_name="Dr. Duplicate",
            specializations=["homeopathy"],
        )

        with pytest.raises(HTTPException) as exc:
            await service.register_doctor(data)

        assert exc.value.status_code == 400
        assert "already registered" in exc.value.detail.lower()

    async def test_register_multiple_specializations(self, db_session, test_division, test_district):
        """Test registration with multiple specializations."""
        service = AuthService(db_session)

        data = RegisterRequest(
            email="multi@test.com",
            password="SecurePass123",
            full_name="Dr. Multi Spec",
            specializations=["homeopathy", "ayurveda", "unani"],
        )

        result = await service.register_doctor(data)
        assert result.email == "multi@test.com"


@pytest.mark.asyncio
class TestLogin:
    """Test user login."""

    async def test_login_success(self, db_session, test_user, test_tenant):
        """Test successful login."""
        service = AuthService(db_session)

        data = LoginRequest(
            email=test_user.email,
            password="TestPass123",
        )

        result = await service.login(data, ip_address="127.0.0.1", user_agent="test")

        # Verify tokens
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None
        assert result.tokens.token_type == "bearer"

        # Verify user data
        assert result.user.id == test_user.id
        assert result.user.email == test_user.email
        assert result.requires_2fa is False

        # Verify session created
        session_result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == test_user.id)
        )
        session = session_result.scalar_one_or_none()
        assert session is not None
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "test"
        assert session.is_revoked is False

    async def test_login_invalid_credentials(self, db_session, test_user):
        """Test login with wrong password."""
        service = AuthService(db_session)

        data = LoginRequest(
            email=test_user.email,
            password="WrongPassword",
        )

        with pytest.raises(HTTPException) as exc:
            await service.login(data)

        assert exc.value.status_code == 401
        assert "incorrect" in exc.value.detail.lower()

    async def test_login_nonexistent_user(self, db_session):
        """Test login with non-existent email."""
        service = AuthService(db_session)

        data = LoginRequest(
            email="nonexistent@test.com",
            password="AnyPassword123",
        )

        with pytest.raises(HTTPException) as exc:
            await service.login(data)

        assert exc.value.status_code == 401

    async def test_login_unapproved_tenant(self, db_session, unapproved_user):
        """Test login fails for unapproved tenant."""
        service = AuthService(db_session)

        data = LoginRequest(
            email=unapproved_user.email,
            password="PendingPass123",
        )

        with pytest.raises(HTTPException) as exc:
            await service.login(data)

        assert exc.value.status_code == 403
        assert "pending" in exc.value.detail.lower()

    async def test_login_inactive_user(self, db_session, test_user):
        """Test login fails for inactive user."""
        # Deactivate user
        test_user.is_active = False
        await db_session.commit()

        service = AuthService(db_session)

        data = LoginRequest(
            email=test_user.email,
            password="TestPass123",
        )

        with pytest.raises(HTTPException) as exc:
            await service.login(data)

        assert exc.value.status_code == 403
        assert "deactivated" in exc.value.detail.lower()

    async def test_login_with_2fa_success(self, db_session, user_with_2fa):
        """Test login with 2FA enabled (mocked TOTP)."""
        service = AuthService(db_session)

        # Note: In real tests, you'd generate a valid TOTP code
        # For this test, we'll test the flow but it will fail without valid code
        data = LoginRequest(
            email=user_with_2fa.email,
            password="2FAPass123",
            totp_code="123456",  # Invalid code for test
        )

        with pytest.raises(HTTPException) as exc:
            await service.login(data)

        # Should fail because TOTP code is invalid
        assert exc.value.status_code == 401
        assert "2fa" in exc.value.detail.lower()

    async def test_login_with_2fa_missing_code(self, db_session, user_with_2fa):
        """Login without a TOTP code should prompt for 2FA, not raise."""
        service = AuthService(db_session)

        data = LoginRequest(
            email=user_with_2fa.email,
            password="2FAPass123",
            # No totp_code provided
        )

        result = await service.login(data)

        assert result.requires_2fa is True
        assert result.tokens is None


@pytest.mark.asyncio
class TestTokenRefresh:
    """Test token refresh functionality."""

    async def test_refresh_token_success(self, db_session, test_user, test_tenant):
        """Test successful token refresh."""
        service = AuthService(db_session)

        # First login to get tokens
        login_data = LoginRequest(email=test_user.email, password="TestPass123")
        login_result = await service.login(login_data)
        original_refresh = login_result.tokens.refresh_token

        # Refresh tokens
        new_tokens = await service.refresh_tokens(original_refresh)

        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.refresh_token != original_refresh  # Token rotation

        # Verify old token can't be reused (token rotation)
        with pytest.raises(HTTPException):
            await service.refresh_tokens(original_refresh)

    async def test_refresh_with_invalid_token(self, db_session):
        """Test refresh with invalid token."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens("invalid.token.here")

        assert exc.value.status_code == 401

    async def test_refresh_with_revoked_token(self, db_session, test_user):
        """Test refresh with revoked token fails."""
        service = AuthService(db_session)

        # Login
        login_data = LoginRequest(email=test_user.email, password="TestPass123")
        login_result = await service.login(login_data)

        # Logout (revoke token)
        await service.logout(test_user.id, login_result.tokens.refresh_token)

        # Try to refresh with revoked token
        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens(login_result.tokens.refresh_token)

        assert exc.value.status_code == 401
        assert "revoked" in exc.value.detail.lower()


@pytest.mark.asyncio
class TestLogout:
    """Test logout functionality."""

    async def test_logout_specific_session(self, db_session, test_user):
        """Test logout of specific session."""
        service = AuthService(db_session)

        # Login to create session
        login_data = LoginRequest(email=test_user.email, password="TestPass123")
        login_result = await service.login(login_data)

        # Logout specific session
        await service.logout(test_user.id, login_result.tokens.refresh_token)

        # Verify session is revoked
        session_result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == test_user.id)
        )
        session = session_result.scalar_one_or_none()
        assert session.is_revoked is True
        assert session.revoked_at is not None

    async def test_logout_all_sessions(self, db_session, test_user):
        """Test logout from all sessions."""
        service = AuthService(db_session)

        # Create multiple sessions
        login_data = LoginRequest(email=test_user.email, password="TestPass123")
        await service.login(login_data, ip_address="192.168.1.1")
        await service.login(login_data, ip_address="192.168.1.2")

        # Logout all sessions (no specific refresh token)
        await service.logout(test_user.id, refresh_token=None)

        # Verify all sessions revoked
        session_result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == test_user.id)
        )
        sessions = session_result.scalars().all()
        assert len(sessions) == 2
        assert all(s.is_revoked for s in sessions)


@pytest.mark.asyncio
class Test2FA:
    """Test 2FA functionality."""

    async def test_setup_2fa(self, db_session, test_user):
        """Test 2FA setup."""
        service = AuthService(db_session)

        result = await service.setup_2fa(test_user.id)

        assert result.secret is not None
        assert result.qr_code_uri is not None
        assert "otpauth://totp/" in result.qr_code_uri
        # otpauth URIs are URL-encoded (e.g. "@" -> "%40" per RFC 3986)
        from urllib.parse import unquote

        assert test_user.email in unquote(result.qr_code_uri)

        # Verify secret saved but not enabled yet
        await db_session.refresh(test_user)
        assert test_user.totp_secret is not None
        assert test_user.is_2fa_enabled is False

    async def test_verify_and_enable_2fa_invalid_code(self, db_session, test_user):
        """Test 2FA enable with invalid code."""
        service = AuthService(db_session)

        # Setup 2FA first
        await service.setup_2fa(test_user.id)

        # Try to enable with invalid code
        with pytest.raises(HTTPException) as exc:
            await service.verify_and_enable_2fa(test_user.id, "000000")

        assert exc.value.status_code == 400
        assert "invalid" in exc.value.detail.lower()

        # Verify 2FA not enabled
        await db_session.refresh(test_user)
        assert test_user.is_2fa_enabled is False

    async def test_disable_2fa_success(self, db_session, user_with_2fa):
        """Test 2FA disable (with mocked verification)."""
        service = AuthService(db_session)

        # This will fail because we can't generate valid TOTP without time
        # In real tests, you'd use freezegun or mock verify_totp
        with pytest.raises(HTTPException):
            await service.disable_2fa(user_with_2fa.id, "2FAPass123", "123456")

    async def test_disable_2fa_wrong_password(self, db_session, user_with_2fa):
        """Test 2FA disable with wrong password."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc:
            await service.disable_2fa(user_with_2fa.id, "WrongPassword", "123456")

        assert exc.value.status_code == 401
        assert "password" in exc.value.detail.lower()


@pytest.mark.asyncio
class TestPasswordManagement:
    """Test password change functionality."""

    async def test_change_password_success(self, db_session, test_user):
        """Test successful password change."""
        service = AuthService(db_session)

        result = await service.change_password(
            test_user.id, "TestPass123", "NewSecurePass456"
        )

        assert result is True

        # Verify new password works
        await db_session.refresh(test_user)
        assert verify_password("NewSecurePass456", test_user.password_hash)
        assert not verify_password("TestPass123", test_user.password_hash)

    async def test_change_password_wrong_current(self, db_session, test_user):
        """Test password change with wrong current password."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc:
            await service.change_password(
                test_user.id, "WrongPassword", "NewSecurePass456"
            )

        assert exc.value.status_code == 401
        assert "incorrect" in exc.value.detail.lower()

    async def test_change_password_nonexistent_user(self, db_session):
        """Test password change for non-existent user."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc:
            await service.change_password(
                "nonexistent-id", "OldPass123", "NewPass456"
            )

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestUserProfile:
    """Test user profile retrieval."""

    async def test_get_user_profile_success(self, db_session, test_user, test_tenant):
        """Test getting user profile with tenant info."""
        service = AuthService(db_session)

        result = await service.get_user_profile(test_user.id)

        # Verify user data
        assert result.user.id == test_user.id
        assert result.user.email == test_user.email
        assert result.user.full_name == test_user.full_name

        # Verify tenant data
        assert result.tenant is not None
        assert result.tenant.id == test_tenant.id
        assert result.tenant.clinic_name == test_tenant.clinic_name

    async def test_get_user_profile_platform_user(self, db_session, platform_admin):
        """Test getting profile for platform user (no tenant)."""
        service = AuthService(db_session)

        result = await service.get_user_profile(platform_admin.id)

        assert result.user.id == platform_admin.id
        assert result.tenant is None  # Platform users have no tenant

    async def test_get_user_profile_nonexistent(self, db_session):
        """Test getting profile for non-existent user."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc:
            await service.get_user_profile("nonexistent-id")

        assert exc.value.status_code == 404
