"""
Multi-tenant isolation tests for authentication module.

CRITICAL: These tests ensure complete data isolation between tenants.
According to CLAUDE.md: "Target: 100% coverage for multi-tenant queries"
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.shared.models import User, UserSession


@pytest.mark.asyncio
class TestTenantIsolation:
    """Test that tenants cannot access each other's data."""

    async def test_login_creates_tenant_scoped_session(
        self, client: AsyncClient, test_user, test_user_2, db_session
    ):
        """Test that login creates session scoped to correct tenant."""
        # Login as user 1
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        assert login1.status_code == 200

        # Login as user 2
        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user_2.email, "password": "TestPass456"},
        )
        assert login2.status_code == 200

        # Verify each user has their own session
        sessions1 = await db_session.execute(
            select(UserSession).where(UserSession.user_id == test_user.id)
        )
        assert len(sessions1.scalars().all()) == 1

        sessions2 = await db_session.execute(
            select(UserSession).where(UserSession.user_id == test_user_2.id)
        )
        assert len(sessions2.scalars().all()) == 1

    async def test_profile_returns_only_own_tenant_data(
        self, authenticated_client: AsyncClient, authenticated_client_2: AsyncClient, test_tenant, test_tenant_2
    ):
        """Test that users can only see their own tenant data."""
        # User 1 gets their profile
        profile1 = await authenticated_client.get("/api/v1/auth/me")
        assert profile1.status_code == 200
        data1 = profile1.json()
        assert data1["tenant"]["id"] == test_tenant.id
        assert data1["tenant"]["clinic_name"] == test_tenant.clinic_name

        # User 2 gets their profile
        profile2 = await authenticated_client_2.get("/api/v1/auth/me")
        assert profile2.status_code == 200
        data2 = profile2.json()
        assert data2["tenant"]["id"] == test_tenant_2.id
        assert data2["tenant"]["clinic_name"] == test_tenant_2.clinic_name

        # Verify they see different tenants
        assert data1["tenant"]["id"] != data2["tenant"]["id"]
        assert data1["tenant"]["clinic_name"] != data2["tenant"]["clinic_name"]

    async def test_refresh_token_scoped_to_user(
        self, client: AsyncClient, test_user, test_user_2
    ):
        """Test that refresh tokens are scoped to correct user."""
        # Login as both users
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        refresh1 = login1.json()["tokens"]["refresh_token"]

        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user_2.email, "password": "TestPass456"},
        )
        refresh2 = login2.json()["tokens"]["refresh_token"]

        # Refresh token 1
        new_tokens1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh1},
        )
        assert new_tokens1.status_code == 200

        # Refresh token 2
        new_tokens2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh2},
        )
        assert new_tokens2.status_code == 200

        # Tokens should be different
        assert new_tokens1.json()["access_token"] != new_tokens2.json()["access_token"]

    async def test_logout_only_affects_own_sessions(
        self, client: AsyncClient, test_user, test_user_2, db_session
    ):
        """Test that logout only revokes own sessions, not other tenants'."""
        # Both users login
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        access1 = login1.json()["tokens"]["access_token"]
        refresh1 = login1.json()["tokens"]["refresh_token"]

        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user_2.email, "password": "TestPass456"},
        )
        refresh2 = login2.json()["tokens"]["refresh_token"]

        # User 1 logs out
        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh1},
            headers={"Authorization": f"Bearer {access1}"},
        )

        # User 1's token should be revoked
        refresh_attempt1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh1},
        )
        assert refresh_attempt1.status_code == 401

        # User 2's token should still work
        refresh_attempt2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh2},
        )
        assert refresh_attempt2.status_code == 200

    async def test_jwt_token_contains_correct_tenant_id(
        self, client: AsyncClient, test_user, test_tenant
    ):
        """Test that JWT tokens contain correct tenant_id claim."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        access_token = login.json()["tokens"]["access_token"]

        # Decode token manually (in real app, use decode_token from security.py)
        from app.core.security import decode_token

        payload = decode_token(access_token)

        assert payload["tenant_id"] == test_tenant.id
        assert payload["sub"] == test_user.id
        assert payload["role"] == test_user.role
        assert payload["email"] == test_user.email

    async def test_platform_user_has_no_tenant_id(
        self, client: AsyncClient, platform_admin
    ):
        """Test that platform admins have tenant_id=None in JWT."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": platform_admin.email, "password": "AdminPass123"},
        )
        access_token = login.json()["tokens"]["access_token"]

        from app.core.security import decode_token

        payload = decode_token(access_token)

        assert payload["tenant_id"] is None
        assert payload["role"] == "admin"

    async def test_cannot_access_other_tenant_user_profile(
        self, authenticated_client: AsyncClient, test_user_2
    ):
        """Test that user cannot access another tenant's user profile."""
        # authenticated_client is logged in as test_user (tenant 1)
        # Try to access test_user_2's profile (tenant 2)

        # Note: The /auth/me endpoint only returns current user's profile
        # This test verifies that the returned data is for the authenticated user only
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()

        # Should get own data, not test_user_2
        assert data["user"]["id"] != test_user_2.id
        assert data["user"]["email"] != test_user_2.email


@pytest.mark.asyncio
class TestTenantRegistrationIsolation:
    """Test tenant isolation during registration."""

    async def test_duplicate_email_across_tenants_rejected(
        self, client: AsyncClient, test_user, test_division, test_district
    ):
        """Test that same email cannot be used across different tenants."""
        # Try to register with same email as existing user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists for tenant 1
                "password": "DifferentPass123",
                "full_name": "Dr. Different Person",
                "specializations": ["ayurveda"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_each_registration_creates_separate_tenant(
        self, client: AsyncClient, db_session, test_division, test_district
    ):
        """Test that each registration creates a separate tenant."""
        # Register first user
        response1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "clinic1@test.com",
                "password": "Pass123",
                "full_name": "Dr. Clinic 1",
                "clinic_name": "Clinic One",
                "specializations": ["homeopathy"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )
        tenant1_id = response1.json()["tenant_id"]

        # Register second user
        response2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "clinic2@test.com",
                "password": "Pass456",
                "full_name": "Dr. Clinic 2",
                "clinic_name": "Clinic Two",
                "specializations": ["ayurveda"],
                "division_id": test_division.id,
                "district_id": test_district.id,
            },
        )
        tenant2_id = response2.json()["tenant_id"]

        # Verify different tenants created
        assert tenant1_id != tenant2_id

        # Verify each tenant has their own data
        from app.shared.models import Tenant

        tenant1 = await db_session.get(Tenant, tenant1_id)
        tenant2 = await db_session.get(Tenant, tenant2_id)

        assert tenant1.clinic_name == "Clinic One"
        assert tenant2.clinic_name == "Clinic Two"
        assert tenant1.specializations == ["homeopathy"]
        assert tenant2.specializations == ["ayurveda"]


@pytest.mark.asyncio
class TestSessionIsolation:
    """Test session management isolation between tenants."""

    async def test_multiple_sessions_per_user_isolated(
        self, client: AsyncClient, test_user, db_session
    ):
        """Test that user can have multiple sessions, all isolated."""
        # Create 3 sessions for same user
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
            headers={"User-Agent": "Browser 1"},
        )

        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
            headers={"User-Agent": "Browser 2"},
        )

        login3 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
            headers={"User-Agent": "Mobile App"},
        )

        # All should succeed
        assert login1.status_code == 200
        assert login2.status_code == 200
        assert login3.status_code == 200

        # Verify 3 active sessions
        sessions = await db_session.execute(
            select(UserSession).where(
                UserSession.user_id == test_user.id, UserSession.is_revoked == False
            )
        )
        active_sessions = sessions.scalars().all()
        assert len(active_sessions) == 3

        # Logout from one session
        refresh1 = login1.json()["tokens"]["refresh_token"]
        access1 = login1.json()["tokens"]["access_token"]

        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh1},
            headers={"Authorization": f"Bearer {access1}"},
        )

        # Verify only 2 active sessions remain
        await db_session.expire_all()
        sessions = await db_session.execute(
            select(UserSession).where(
                UserSession.user_id == test_user.id, UserSession.is_revoked == False
            )
        )
        active_sessions = sessions.scalars().all()
        assert len(active_sessions) == 2

        # Other sessions should still work
        refresh2 = login2.json()["tokens"]["refresh_token"]
        refresh_attempt = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh2},
        )
        assert refresh_attempt.status_code == 200

    async def test_logout_all_sessions_tenant_isolated(
        self, client: AsyncClient, test_user, test_user_2, db_session
    ):
        """Test logout all sessions only affects current user's sessions."""
        # Create multiple sessions for both users
        login1a = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )

        login2a = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user_2.email, "password": "TestPass456"},
        )

        # User 1 logs out all sessions (no specific refresh token)
        access1 = login1a.json()["tokens"]["access_token"]
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access1}"},
        )

        # User 1's sessions should all be revoked
        await db_session.expire_all()
        sessions1 = await db_session.execute(
            select(UserSession).where(
                UserSession.user_id == test_user.id, UserSession.is_revoked == False
            )
        )
        assert len(sessions1.scalars().all()) == 0

        # User 2's sessions should still be active
        sessions2 = await db_session.execute(
            select(UserSession).where(
                UserSession.user_id == test_user_2.id, UserSession.is_revoked == False
            )
        )
        assert len(sessions2.scalars().all()) == 1

        # User 2 can still refresh
        refresh2 = login2a.json()["tokens"]["refresh_token"]
        refresh_attempt = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh2},
        )
        assert refresh_attempt.status_code == 200


@pytest.mark.asyncio
class TestPasswordAndSecurityIsolation:
    """Test password changes and 2FA are tenant-isolated."""

    async def test_password_change_only_affects_own_account(
        self, client: AsyncClient, test_user, test_user_2
    ):
        """Test password change only affects the authenticated user."""
        # Login as user 1
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        access1 = login1.json()["tokens"]["access_token"]

        # User 1 changes password
        await client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "TestPass123",
                "new_password": "NewTestPass123",
            },
            headers={"Authorization": f"Bearer {access1}"},
        )

        # User 1 can login with new password
        login1_new = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "NewTestPass123"},
        )
        assert login1_new.status_code == 200

        # User 2 can still login with their original password
        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user_2.email, "password": "TestPass456"},
        )
        assert login2.status_code == 200

    async def test_2fa_setup_only_affects_own_account(
        self, authenticated_client: AsyncClient, authenticated_client_2: AsyncClient, test_user, test_user_2, db_session
    ):
        """Test 2FA setup only affects the authenticated user."""
        # User 1 sets up 2FA
        setup1 = await authenticated_client.post("/api/v1/auth/2fa/setup")
        assert setup1.status_code == 200

        # Verify user 1 has totp_secret
        await db_session.refresh(test_user)
        assert test_user.totp_secret is not None

        # Verify user 2 does not have totp_secret
        await db_session.refresh(test_user_2)
        assert test_user_2.totp_secret is None

        # User 2 can still login normally (no 2FA)
        # Note: Need to use fresh client for login test
