"""Integration tests for Stage 1 "Billing enforcement" usage_tracking writes.

Covers the three named write points (prescription issue, SMS send, AI
query), the DB-backed plan/expiry check in require_plan(), and the admin
usage read endpoint. See docs/planning/revision-2026-09.md Stage 1.
"""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.shared.models import IntegrationProvider, UsageTracking


async def _usage_row(db_session, tenant_id):
    result = await db_session.execute(
        select(UsageTracking).where(
            UsageTracking.tenant_id == tenant_id,
            UsageTracking.usage_date == date.today(),
        )
    )
    return result.scalar_one_or_none()


@pytest.fixture
async def integration_providers(db_session):
    sms = IntegrationProvider(
        name="bulksmsbd",
        display_name="BulkSMSBD",
        provider_type="sms",
        is_active=True,
    )
    db_session.add(sms)
    await db_session.commit()
    await db_session.refresh(sms)
    return {"sms": sms}


@pytest.mark.asyncio
class TestPrescriptionUsage:
    async def test_creating_issued_prescription_increments_counter(
        self, authenticated_client, test_patient, test_tenant, db_session
    ):
        response = await authenticated_client.post(
            "/api/v1/prescriptions",
            json={
                "patient_id": test_patient.id,
                "diagnosis": "Test diagnosis",
                "status": "issued",
                "items": [
                    {"medicine_name": "Arnica 30C", "dosage": "30C", "frequency": "Daily"}
                ],
            },
        )
        assert response.status_code == 201

        row = await _usage_row(db_session, test_tenant.id)
        assert row is not None
        assert row.prescriptions_created == 1

    async def test_creating_draft_prescription_does_not_increment(
        self, authenticated_client, test_patient, test_tenant, db_session
    ):
        response = await authenticated_client.post(
            "/api/v1/prescriptions",
            json={"patient_id": test_patient.id, "diagnosis": "Test", "status": "draft"},
        )
        assert response.status_code == 201

        row = await _usage_row(db_session, test_tenant.id)
        assert row is None

    async def test_issuing_a_draft_later_increments_counter(
        self, authenticated_client, test_patient, test_tenant, db_session
    ):
        create_response = await authenticated_client.post(
            "/api/v1/prescriptions",
            json={"patient_id": test_patient.id, "diagnosis": "Test", "status": "draft"},
        )
        prescription_id = create_response.json()["id"]

        # Editing a draft without changing its status must not count as an issue.
        await authenticated_client.patch(
            f"/api/v1/prescriptions/{prescription_id}",
            json={"diagnosis": "Updated diagnosis"},
        )
        row = await _usage_row(db_session, test_tenant.id)
        assert row is None

        patch_response = await authenticated_client.patch(
            f"/api/v1/prescriptions/{prescription_id}",
            json={"status": "issued"},
        )
        assert patch_response.status_code == 200

        row = await _usage_row(db_session, test_tenant.id)
        assert row is not None
        assert row.prescriptions_created == 1


@pytest.mark.asyncio
class TestSmsUsage:
    async def test_send_sms_increments_counter(
        self,
        authenticated_client,
        integration_providers,
        test_tenant,
        db_session,
        monkeypatch,
    ):
        create_response = await authenticated_client.post(
            "/api/v1/integrations/",
            json={
                "provider_id": integration_providers["sms"].id,
                "display_name": "SMS Primary",
                "credentials": {"api_key": "key", "sender_id": "ALT"},
                "is_active": True,
            },
        )
        integration_id = create_response.json()["id"]
        await authenticated_client.post(f"/api/v1/integrations/{integration_id}/set-primary")

        monkeypatch.setattr(
            "app.modules.integration.routes.send_sms_task.delay",
            lambda **kwargs: SimpleNamespace(id="task-123"),
        )

        response = await authenticated_client.post(
            "/api/v1/integrations/send/sms",
            json={"recipient": "+8801700000000", "message": "ping"},
        )
        assert response.status_code == 200

        row = await _usage_row(db_session, test_tenant.id)
        assert row is not None
        assert row.sms_sent == 1


@pytest.mark.asyncio
class TestAiQueryUsage:
    async def test_ai_query_increments_counter_even_as_stub(
        self, authenticated_client_2, test_tenant_2, db_session
    ):
        """test_tenant_2 is seeded with plan="pro" (see conftest.py)."""
        response = await authenticated_client_2.post(
            "/api/v1/ai/query", json={"query": "test"}
        )
        assert response.status_code == 501

        row = await _usage_row(db_session, test_tenant_2.id)
        assert row is not None
        assert row.ai_queries_made == 1

    async def test_expired_pro_plan_is_denied(
        self, authenticated_client_2, test_tenant_2, db_session
    ):
        test_tenant_2.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()

        response = await authenticated_client_2.post(
            "/api/v1/ai/query", json={"query": "test"}
        )
        assert response.status_code == 403

        row = await _usage_row(db_session, test_tenant_2.id)
        assert row is None


@pytest.mark.asyncio
class TestAdminUsageEndpoint:
    async def test_get_tenant_usage_reflects_activity(
        self, admin_client, authenticated_client_2, test_tenant_2
    ):
        await authenticated_client_2.post("/api/v1/ai/query", json={"query": "test"})

        response = await admin_client.get(f"/api/v1/admin/tenants/{test_tenant_2.id}/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == test_tenant_2.id
        assert data["plan"] == "pro"
        assert data["ai_queries_made"] == 1
        assert data["prescriptions_created"] == 0
        assert data["sms_sent"] == 0
        assert data["month"] == date.today().strftime("%Y-%m")

    async def test_get_tenant_usage_zero_for_no_activity(self, admin_client, test_tenant):
        response = await admin_client.get(f"/api/v1/admin/tenants/{test_tenant.id}/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["prescriptions_created"] == 0
        assert data["ai_queries_made"] == 0
        assert data["sms_sent"] == 0
        assert data["pdfs_generated"] == 0

    async def test_get_tenant_usage_unknown_tenant_404s(self, admin_client):
        response = await admin_client.get("/api/v1/admin/tenants/does-not-exist/usage")
        assert response.status_code == 404
