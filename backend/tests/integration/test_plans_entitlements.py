"""Plan configuration (admin) and entitlement enforcement."""

import pytest
from httpx import AsyncClient

PATIENT = {"full_name": "Limit Patient", "date_of_birth": "1990-01-15", "gender": "female"}


@pytest.fixture
def doctor(client_2: AsyncClient, test_access_token: str) -> AsyncClient:
    """A doctor of `test_tenant` (free plan) on its own HTTP client, so an admin client can be
    used in the same test (the shared `client` fixture carries only one Authorization header)."""
    client_2.headers["Authorization"] = f"Bearer {test_access_token}"
    return client_2


def _plan_payload(plan: dict, **entitlement_changes) -> dict:
    """Turn a GET /admin/plans plan into a PUT body, applying {key: (enabled, limit)} changes."""
    ents = []
    for e in plan["entitlements"]:
        enabled, limit = entitlement_changes.get(e["key"], (e["enabled"], e["limit"]))
        ents.append({"key": e["key"], "enabled": enabled, "limit": limit})
    return {
        "name_en": plan["name_en"],
        "name_bn": plan["name_bn"],
        "description_en": plan["description_en"],
        "description_bn": plan["description_bn"],
        "price_monthly": plan["price_monthly"],
        "price_yearly": plan["price_yearly"],
        "currency": plan["currency"],
        "is_public": plan["is_public"],
        "entitlements": ents,
    }


async def _plan(admin: AsyncClient, key: str) -> dict:
    body = (await admin.get("/api/v1/admin/plans")).json()
    return next(p for p in body["plans"] if p["key"] == key)


@pytest.mark.asyncio
class TestPublicPlans:
    async def test_public_plans_need_no_auth_and_are_ordered(self, client: AsyncClient):
        response = await client.get("/api/v1/plans")
        assert response.status_code == 200
        body = response.json()
        assert [p["key"] for p in body["plans"]] == ["free", "plus", "pro"]
        assert {c["key"] for c in body["catalog"]} >= {"max_patients", "feature_invoicing"}
        # no price has been approved yet
        assert all(p["price_monthly"] is None for p in body["plans"])


@pytest.mark.asyncio
class TestAdminPlanEditor:
    async def test_doctor_cannot_read_or_edit_plans(self, doctor: AsyncClient):
        assert (await doctor.get("/api/v1/admin/plans")).status_code == 403
        assert (await doctor.put("/api/v1/admin/plans/free", json={})).status_code == 403

    async def test_defaults_are_permissive_except_ai(self, admin_client: AsyncClient):
        free = await _plan(admin_client, "free")
        values = {e["key"]: e for e in free["entitlements"]}
        assert values["max_patients"]["limit"] is None
        assert values["feature_invoicing"]["enabled"] is True
        assert values["feature_ai_assistant"]["enabled"] is False
        assert (await _plan(admin_client, "pro"))["entitlements"][-1]["enabled"] is True

    async def test_update_records_audit_trail(self, admin_client: AsyncClient):
        free = await _plan(admin_client, "free")
        payload = _plan_payload(free, max_patients=(True, 25))
        payload["price_monthly"] = "0"
        response = await admin_client.put("/api/v1/admin/plans/free", json=payload)
        assert response.status_code == 200

        audit = (await admin_client.get("/api/v1/admin/plans/audit?plan_key=free")).json()
        changed = {(a["entitlement_key"], a["field"]): a for a in audit}
        entry = changed[("max_patients", "limit")]
        assert entry["old_value"] is None and entry["new_value"] == "25"
        assert entry["changed_by"] is not None

    async def test_higher_plan_cannot_offer_less(self, admin_client: AsyncClient):
        plus = await _plan(admin_client, "plus")
        response = await admin_client.put(
            "/api/v1/admin/plans/plus", json=_plan_payload(plus, max_patients=(True, 10))
        )
        # free is unlimited by default, so a 10-patient plus plan would offer less
        assert response.status_code == 422
        assert "cannot offer less" in response.json()["detail"]

    async def test_unknown_plan_and_entitlement_rejected(self, admin_client: AsyncClient):
        free = await _plan(admin_client, "free")
        assert (
            await admin_client.put("/api/v1/admin/plans/gold", json=_plan_payload(free))
        ).status_code == 404
        bad = _plan_payload(free)
        bad["entitlements"].append({"key": "made_up", "enabled": True, "limit": None})
        assert (await admin_client.put("/api/v1/admin/plans/free", json=bad)).status_code == 422


@pytest.mark.asyncio
class TestPatientLimit:
    async def test_limit_blocks_with_structured_error_then_override_unblocks(
        self, admin_client: AsyncClient, doctor: AsyncClient, test_tenant
    ):
        free = await _plan(admin_client, "free")
        await admin_client.put(
            "/api/v1/admin/plans/free", json=_plan_payload(free, max_patients=(True, 1))
        )

        assert (await doctor.post("/api/v1/patients", json=PATIENT)).status_code == 201

        blocked = await doctor.post("/api/v1/patients", json=PATIENT)
        assert blocked.status_code == 403
        detail = blocked.json()["detail"]
        assert detail["code"] == "plan_limit_reached"
        assert detail["limit"] == 1 and detail["used"] == 1 and detail["plan"] == "free"
        assert "Upgrade" in detail["message"]

        # per-tenant override lifts it
        url = f"/api/v1/admin/tenants/{test_tenant.id}/entitlements/max_patients"
        override = await admin_client.put(url, json={"enabled": True, "limit": 5, "note": "founder"})
        assert override.status_code == 200
        item = next(e for e in override.json()["entitlements"] if e["key"] == "max_patients")
        assert item["source"] == "override" and item["limit"] == 5
        assert (await doctor.post("/api/v1/patients", json=PATIENT)).status_code == 201

        # removing it restores the plan limit
        await admin_client.delete(url)
        assert (await doctor.post("/api/v1/patients", json=PATIENT)).status_code == 403

    async def test_my_entitlements_shows_usage(
        self, admin_client: AsyncClient, doctor: AsyncClient
    ):
        free = await _plan(admin_client, "free")
        await admin_client.put(
            "/api/v1/admin/plans/free", json=_plan_payload(free, max_patients=(True, 3))
        )
        await doctor.post("/api/v1/patients", json=PATIENT)

        body = (await doctor.get("/api/v1/entitlements/me")).json()
        assert body["plan"] == "free" and body["expired"] is False
        item = next(e for e in body["entitlements"] if e["key"] == "max_patients")
        assert item["limit"] == 3 and item["used"] == 1


@pytest.mark.asyncio
class TestFeatureGates:
    async def test_invoicing_can_be_switched_off_for_a_plan(
        self, admin_client: AsyncClient, doctor: AsyncClient
    ):
        free = await _plan(admin_client, "free")
        # off on free only; plus/pro stay on, so the "higher plan offers no less" rule holds
        await admin_client.put(
            "/api/v1/admin/plans/free",
            json=_plan_payload(free, feature_invoicing=(False, None)),
        )

        response = await doctor.post(
            "/api/v1/payments/invoices", json={"payment_id": "x", "due_date": "2030-01-01"}
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "feature_not_in_plan"

    async def test_ai_quota_enforced_for_pro(
        self, authenticated_client_2: AsyncClient, test_tenant_2, db_session
    ):
        from app.shared.models import TenantEntitlementOverride

        db_session.add(
            TenantEntitlementOverride(
                tenant_id=test_tenant_2.id,
                entitlement_key="monthly_ai_queries",
                enabled=True,
                limit_value=1,
            )
        )
        await db_session.commit()

        first = await authenticated_client_2.post("/api/v1/ai/query", json={"query": "q"})
        assert first.status_code == 501  # access granted; stub endpoint

        second = await authenticated_client_2.post("/api/v1/ai/query", json={"query": "q"})
        assert second.status_code == 403
        assert second.json()["detail"]["code"] == "plan_limit_reached"


@pytest.mark.asyncio
class TestSeatsAndMonthlyLimits:
    async def test_seat_limit_blocks_adding_a_doctor(
        self, admin_client: AsyncClient, test_tenant, test_user
    ):
        url = f"/api/v1/admin/tenants/{test_tenant.id}/entitlements/max_seats"
        assert (await admin_client.put(url, json={"enabled": True, "limit": 1})).status_code == 200

        response = await admin_client.post(
            f"/api/v1/admin/tenants/{test_tenant.id}/doctors",
            json={
                "email": "seat.two@test.com",
                "password": "SecondPass123",
                "full_name": "Dr. Seat Two",
                "language": "en",
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "plan_limit_reached"

    async def test_monthly_sms_limit_counts_usage_rows(self, db_session, test_tenant):
        from fastapi import HTTPException

        from app.core.entitlements import EntitlementService
        from app.core.usage_tracking import UsageService
        from app.shared.models import TenantEntitlementOverride

        db_session.add(
            TenantEntitlementOverride(
                tenant_id=test_tenant.id, entitlement_key="monthly_sms", enabled=True, limit_value=2
            )
        )
        await db_session.commit()

        service = EntitlementService(db_session)
        await service.check_limit(test_tenant.id, "monthly_sms")  # 0 of 2
        await UsageService(db_session, test_tenant.id).increment("sms_sent", 2)
        with pytest.raises(HTTPException) as exc:
            await service.check_limit(test_tenant.id, "monthly_sms")
        assert exc.value.detail["code"] == "plan_limit_reached"
        assert exc.value.detail["used"] == 2

    async def test_expired_plan_falls_back_to_free_entitlements(self, db_session, test_tenant_2):
        from datetime import datetime, timedelta, timezone

        from fastapi import HTTPException

        from app.core.entitlements import EntitlementService

        test_tenant_2.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()
        with pytest.raises(HTTPException) as exc:
            await EntitlementService(db_session).check_feature(
                test_tenant_2.id, "feature_ai_assistant"
            )
        assert exc.value.detail["code"] == "plan_expired"
