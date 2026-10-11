"""PATCH /auth/me/language — saving the UI language to the account."""

import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.shared.models import User


@pytest.mark.asyncio
class TestLanguagePreference:
    async def test_user_can_save_bengali_and_it_shows_in_their_profile(
        self, authenticated_client, test_user, db_session
    ):
        r = await authenticated_client.patch("/api/v1/auth/me/language", json={"language": "bn"})
        assert r.status_code == 200 and r.json() == {"language": "bn"}

        await db_session.refresh(test_user)
        assert test_user.language == "bn"
        me = await authenticated_client.get("/api/v1/auth/me")
        assert me.json()["user"]["language"] == "bn"

        back = await authenticated_client.patch("/api/v1/auth/me/language", json={"language": "en"})
        assert back.json() == {"language": "en"}

    async def test_does_not_sign_the_user_out(self, authenticated_client, test_user, db_session):
        before = test_user.token_version
        await authenticated_client.patch("/api/v1/auth/me/language", json={"language": "bn"})
        await db_session.refresh(test_user)
        assert test_user.token_version == before
        # the same token still works
        assert (await authenticated_client.get("/api/v1/auth/me")).status_code == 200

    @pytest.mark.parametrize("bad", ["fr", "", "EN", None, 5])
    async def test_rejects_unsupported_languages(self, authenticated_client, bad):
        r = await authenticated_client.patch("/api/v1/auth/me/language", json={"language": bad})
        assert r.status_code == 422

    async def test_requires_login(self, client):
        client.headers.pop("Authorization", None)
        r = await client.patch("/api/v1/auth/me/language", json={"language": "bn"})
        assert r.status_code in (401, 403)

    async def test_works_for_platform_staff_too(self, client, platform_admin, db_session):
        token = create_access_token(
            {"sub": platform_admin.id, "role": "admin", "email": platform_admin.email, "tenant_id": None}
        )
        r = await client.patch(
            "/api/v1/auth/me/language",
            json={"language": "bn"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        row = (await db_session.execute(select(User).where(User.id == platform_admin.id))).scalar_one()
        assert row.language == "bn"

    async def test_only_changes_the_callers_own_account(
        self, authenticated_client, test_user, platform_admin, db_session
    ):
        await authenticated_client.patch("/api/v1/auth/me/language", json={"language": "bn"})
        await db_session.refresh(platform_admin)
        assert platform_admin.language != "bn"
