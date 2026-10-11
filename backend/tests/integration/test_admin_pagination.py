"""Pagination and search on the admin list endpoints."""

import uuid

import pytest

from app.core.security import get_password_hash
from app.shared.models import Tenant, User


async def _tenants(db, n):
    rows = []
    for i in range(n):
        t = Tenant(
            id=str(uuid.uuid4()),
            name=f"Clinic Owner {i:02d}",
            email=f"owner{i:02d}@pg.test",
            clinic_name=f"Pagination Clinic {i:02d}",
            plan="free",
            is_active=True,
            is_approved=False,
        )
        db.add(t)
        rows.append(t)
    await db.commit()
    return rows


@pytest.mark.asyncio
class TestAdminTenantPagination:
    async def test_limit_and_offset_walk_through_all_tenants_without_overlap(
        self, admin_client, db_session
    ):
        await _tenants(db_session, 7)

        seen = []
        for offset in (0, 3, 6, 9):
            r = await admin_client.get(
                "/api/v1/admin/tenants", params={"limit": 3, "offset": offset, "search": "Pagination"}
            )
            assert r.status_code == 200
            page = [item["tenant"]["id"] for item in r.json()]
            assert len(page) <= 3
            seen.extend(page)

        assert len(seen) == 7 and len(set(seen)) == 7

    async def test_search_narrows_results(self, admin_client, db_session):
        await _tenants(db_session, 4)
        r = await admin_client.get("/api/v1/admin/tenants", params={"search": "Clinic 03"})
        assert [i["tenant"]["clinic_name"] for i in r.json()] == ["Pagination Clinic 03"]

    async def test_pending_list_is_paginated(self, admin_client, db_session):
        await _tenants(db_session, 5)
        r = await admin_client.get("/api/v1/admin/tenants/pending", params={"limit": 2})
        assert len(r.json()) == 2
        r2 = await admin_client.get("/api/v1/admin/tenants/pending", params={"limit": 2, "offset": 4})
        assert len(r2.json()) >= 1

    async def test_rejects_out_of_range_paging(self, admin_client):
        assert (await admin_client.get("/api/v1/admin/tenants", params={"limit": 0})).status_code == 422
        assert (await admin_client.get("/api/v1/admin/tenants", params={"limit": 501})).status_code == 422
        assert (await admin_client.get("/api/v1/admin/tenants", params={"offset": -1})).status_code == 422


@pytest.mark.asyncio
class TestAdminUserPagination:
    async def _users(self, db, tenant, n):
        for i in range(n):
            db.add(
                User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    email=f"staff{i:02d}@pg.test",
                    password_hash=get_password_hash("Staff12345"),
                    role="receptionist",
                    full_name=f"Staff Member {i:02d}",
                    is_active=True,
                    is_email_verified=True,
                )
            )
        await db.commit()

    async def test_summary_counts_cover_every_role_not_just_the_page_or_selected_role(
        self, admin_client, db_session, test_tenant, test_user
    ):
        await self._users(db_session, test_tenant, 6)

        r = await admin_client.get(
            "/api/v1/admin/users", params={"role": "receptionist", "limit": 2, "offset": 0}
        )
        body = r.json()
        assert len(body["users"]) == 2
        assert body["summary"]["by_role"]["receptionist"] == 6
        # the other roles are still counted (test_tenant's doctor exists)
        assert body["summary"]["by_role"]["doctor"] >= 1
        assert body["summary"]["total"] == sum(body["summary"]["by_role"].values()) >= 7

    async def test_pages_do_not_overlap(self, admin_client, db_session, test_tenant):
        await self._users(db_session, test_tenant, 5)
        ids = []
        for offset in (0, 2, 4):
            r = await admin_client.get(
                "/api/v1/admin/users",
                params={"role": "receptionist", "limit": 2, "offset": offset},
            )
            ids.extend(u["id"] for u in r.json()["users"])
        assert len(ids) == 5 and len(set(ids)) == 5

    async def test_search_matches_name_email_and_clinic(
        self, admin_client, db_session, test_tenant
    ):
        await self._users(db_session, test_tenant, 3)
        by_name = await admin_client.get("/api/v1/admin/users", params={"search": "Member 02"})
        assert [u["email"] for u in by_name.json()["users"]] == ["staff02@pg.test"]
        by_email = await admin_client.get("/api/v1/admin/users", params={"search": "staff01@"})
        assert len(by_email.json()["users"]) == 1
        by_clinic = await admin_client.get(
            "/api/v1/admin/users", params={"search": test_tenant.name[:6], "role": "receptionist"}
        )
        assert len(by_clinic.json()["users"]) == 3
