"""Integration tests for integration module routes."""

from types import SimpleNamespace

import pytest

from app.core.security import create_access_token
from app.shared.models import IntegrationLog, IntegrationProvider, TenantIntegration, User


@pytest.fixture
async def integration_providers(db_session):
    sms = IntegrationProvider(
        name="bulksmsbd",
        display_name="BulkSMSBD",
        provider_type="sms",
        is_active=True,
    )
    email = IntegrationProvider(
        name="smtp",
        display_name="SMTP",
        provider_type="email",
        is_active=True,
    )
    payment = IntegrationProvider(
        name="bkash",
        display_name="bKash",
        provider_type="payment",
        is_active=True,
    )
    db_session.add_all([sms, email, payment])
    await db_session.commit()
    await db_session.refresh(sms)
    await db_session.refresh(email)
    await db_session.refresh(payment)
    return {"sms": sms, "email": email, "payment": payment}


@pytest.fixture
async def receptionist_user(db_session, test_tenant):
    user = User(
        tenant_id=test_tenant.id,
        email="integration.reception@test.com",
        password_hash="unused",
        role="receptionist",
        full_name="Reception",
        phone="+8801700009999",
        language="en",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def receptionist_headers(receptionist_user, test_tenant):
    token = create_access_token(
        {
            "sub": receptionist_user.id,
            "tenant_id": test_tenant.id,
            "role": receptionist_user.role,
            "email": receptionist_user.email,
            "plan": test_tenant.plan,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_list_integrations(authenticated_client, integration_providers):
    response = await authenticated_client.post(
        "/api/v1/integrations/",
        json={
            "provider_id": integration_providers["sms"].id,
            "display_name": "Clinic SMS",
            "credentials": {"api_key": "secret", "sender_id": "ALTCARE"},
            "is_active": True,
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["provider_id"] == integration_providers["sms"].id
    assert created["display_name"] == "Clinic SMS"
    assert "encrypted_credentials" not in created

    list_response = await authenticated_client.get("/api/v1/integrations/")
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) == 1
    assert data[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_update_and_set_primary_integration(authenticated_client, integration_providers):
    create_response = await authenticated_client.post(
        "/api/v1/integrations/",
        json={
            "provider_id": integration_providers["sms"].id,
            "display_name": "SMS One",
            "credentials": {"api_key": "k1", "sender_id": "S1"},
            "is_active": True,
        },
    )
    integration_id = create_response.json()["id"]

    update_response = await authenticated_client.patch(
        f"/api/v1/integrations/{integration_id}",
        json={"display_name": "SMS Updated", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == "SMS Updated"
    assert update_response.json()["is_active"] is False

    primary_response = await authenticated_client.post(
        f"/api/v1/integrations/{integration_id}/set-primary"
    )
    assert primary_response.status_code == 200
    assert primary_response.json()["is_primary"] is True


@pytest.mark.asyncio
async def test_tenant_isolation_for_get_and_update(
    authenticated_client, authenticated_client_2, integration_providers
):
    create_response = await authenticated_client_2.post(
        "/api/v1/integrations/",
        json={
            "provider_id": integration_providers["sms"].id,
            "display_name": "Tenant2 SMS",
            "credentials": {"api_key": "k2", "sender_id": "S2"},
            "is_active": True,
        },
    )
    integration_id = create_response.json()["id"]

    forbidden_get = await authenticated_client.get(f"/api/v1/integrations/{integration_id}")
    assert forbidden_get.status_code == 404

    forbidden_update = await authenticated_client.patch(
        f"/api/v1/integrations/{integration_id}",
        json={"display_name": "hijack"},
    )
    assert forbidden_update.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_for_logs(
    authenticated_client, authenticated_client_2, db_session, integration_providers, test_tenant, test_tenant_2
):
    int_1 = TenantIntegration(
        tenant_id=test_tenant.id,
        provider_id=integration_providers["sms"].id,
        display_name="T1 SMS",
        encrypted_credentials="gAAAAABpA",
        is_active=True,
        is_primary=True,
        created_by="u1",
        updated_by="u1",
    )
    int_2 = TenantIntegration(
        tenant_id=test_tenant_2.id,
        provider_id=integration_providers["sms"].id,
        display_name="T2 SMS",
        encrypted_credentials="gAAAAABpB",
        is_active=True,
        is_primary=True,
        created_by="u2",
        updated_by="u2",
    )
    db_session.add_all([int_1, int_2])
    await db_session.commit()
    await db_session.refresh(int_1)
    await db_session.refresh(int_2)

    db_session.add_all(
        [
            IntegrationLog(
                tenant_id=test_tenant.id,
                tenant_integration_id=int_1.id,
                transaction_type="sms_sent",
                status="success",
                recipient="+8801700011111",
            ),
            IntegrationLog(
                tenant_id=test_tenant_2.id,
                tenant_integration_id=int_2.id,
                transaction_type="sms_sent",
                status="success",
                recipient="+8801700022222",
            ),
        ]
    )
    await db_session.commit()

    logs_t1 = await authenticated_client.get("/api/v1/integrations/logs")
    logs_t2 = await authenticated_client_2.get("/api/v1/integrations/logs")

    assert logs_t1.status_code == 200
    assert logs_t2.status_code == 200
    assert len(logs_t1.json()) == 1
    assert len(logs_t2.json()) == 1
    assert logs_t1.json()[0]["recipient"] == "+8801700011111"
    assert logs_t2.json()[0]["recipient"] == "+8801700022222"


@pytest.mark.asyncio
async def test_send_sms_requires_primary_provider(authenticated_client):
    response = await authenticated_client.post(
        "/api/v1/integrations/send/sms",
        json={"recipient": "+8801700000000", "message": "hello"},
    )
    assert response.status_code == 400
    assert "No primary SMS provider configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_send_sms_with_primary_provider_queues_task(
    authenticated_client, integration_providers, test_user, monkeypatch
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
    payload = response.json()
    assert payload["queued"] is True
    assert payload["transaction_id"] == "task-123"


@pytest.mark.asyncio
async def test_test_integration_payment_updates_status(
    authenticated_client, integration_providers, monkeypatch
):
    create_response = await authenticated_client.post(
        "/api/v1/integrations/",
        json={
            "provider_id": integration_providers["payment"].id,
            "display_name": "bKash Prod",
            "credentials": {
                "app_key": "ak",
                "app_secret": "as",
                "username": "u",
                "password": "p",
                "environment": "sandbox",
            },
            "is_active": True,
        },
    )
    integration_id = create_response.json()["id"]

    class DummyProvider:
        async def test_connection(self):
            return {"success": True, "message": "ok"}

    monkeypatch.setattr(
        "app.modules.integration.routes.IntegrationProviderFactory.create_provider",
        lambda provider_name, credentials, config=None: DummyProvider(),
    )

    response = await authenticated_client.post(
        f"/api/v1/integrations/{integration_id}/test",
        json={"test_amount": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["test_type"] == "payment"
