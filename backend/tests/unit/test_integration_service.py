"""Unit tests for integration service layer."""

import pytest

from app.core.security import decrypt_credentials
from app.modules.integration.service import IntegrationService
from app.shared.models import IntegrationProvider
from app.shared.schemas.integration import TenantIntegrationCreate, TenantIntegrationUpdate


@pytest.fixture
async def sms_provider(db_session):
    provider = IntegrationProvider(
        name="bulksmsbd",
        display_name="BulkSMSBD",
        provider_type="sms",
        is_active=True,
        config_schema={"api_key": "string", "sender_id": "string"},
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    return provider


@pytest.mark.asyncio
async def test_create_integration_encrypts_credentials(db_session, test_tenant, test_user, sms_provider):
    service = IntegrationService(db=db_session, tenant_id=test_tenant.id)

    data = TenantIntegrationCreate(
        provider_id=sms_provider.id,
        display_name="Primary SMS",
        credentials={"api_key": "secret-key", "sender_id": "ALTCARE"},
        is_active=True,
    )
    integration = await service.create_integration(data, created_by=test_user.id)

    assert integration.tenant_id == test_tenant.id
    assert integration.display_name == "Primary SMS"
    assert integration.encrypted_credentials != "secret-key"
    decrypted = decrypt_credentials(integration.encrypted_credentials)
    assert decrypted["api_key"] == "secret-key"
    assert decrypted["sender_id"] == "ALTCARE"


@pytest.mark.asyncio
async def test_update_integration_reencrypts_credentials(db_session, test_tenant, test_user, sms_provider):
    service = IntegrationService(db=db_session, tenant_id=test_tenant.id)

    created = await service.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            credentials={"api_key": "old-key", "sender_id": "OLD"},
            is_active=True,
        ),
        created_by=test_user.id,
    )
    previous_cipher = created.encrypted_credentials

    updated = await service.update_integration(
        created.id,
        TenantIntegrationUpdate(credentials={"api_key": "new-key", "sender_id": "NEW"}),
        updated_by=test_user.id,
    )

    assert updated.encrypted_credentials != previous_cipher
    decrypted = decrypt_credentials(updated.encrypted_credentials)
    assert decrypted["api_key"] == "new-key"
    assert decrypted["sender_id"] == "NEW"


@pytest.mark.asyncio
async def test_set_primary_unsets_existing_for_same_provider_type(
    db_session, test_tenant, test_user, sms_provider
):
    service = IntegrationService(db=db_session, tenant_id=test_tenant.id)

    first = await service.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            display_name="SMS One",
            credentials={"api_key": "k1", "sender_id": "S1"},
            is_active=True,
        ),
        created_by=test_user.id,
    )
    second = await service.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            display_name="SMS Two",
            credentials={"api_key": "k2", "sender_id": "S2"},
            is_active=True,
        ),
        created_by=test_user.id,
    )

    await service.set_primary(first.id, updated_by=test_user.id)
    switched = await service.set_primary(second.id, updated_by=test_user.id)

    first_fresh = await service.get_integration(first.id)
    assert first_fresh.is_primary is False
    assert switched.is_primary is True


@pytest.mark.asyncio
async def test_get_integration_is_tenant_scoped(
    db_session, test_tenant, test_tenant_2, test_user, test_user_2, sms_provider
):
    service_tenant_1 = IntegrationService(db=db_session, tenant_id=test_tenant.id)
    service_tenant_2 = IntegrationService(db=db_session, tenant_id=test_tenant_2.id)

    created = await service_tenant_2.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            display_name="Tenant2 SMS",
            credentials={"api_key": "k2", "sender_id": "T2"},
            is_active=True,
        ),
        created_by=test_user_2.id,
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await service_tenant_1.get_integration(created.id)


@pytest.mark.asyncio
async def test_list_logs_is_tenant_scoped(db_session, test_tenant, test_tenant_2, test_user, test_user_2, sms_provider):
    service_1 = IntegrationService(db=db_session, tenant_id=test_tenant.id)
    service_2 = IntegrationService(db=db_session, tenant_id=test_tenant_2.id)

    integration_1 = await service_1.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            credentials={"api_key": "k1", "sender_id": "S1"},
            is_active=True,
        ),
        created_by=test_user.id,
    )
    integration_2 = await service_2.create_integration(
        TenantIntegrationCreate(
            provider_id=sms_provider.id,
            credentials={"api_key": "k2", "sender_id": "S2"},
            is_active=True,
        ),
        created_by=test_user_2.id,
    )

    await service_1.create_log(
        tenant_integration_id=integration_1.id,
        transaction_type="sms_sent",
        status="success",
        recipient="+8801700000001",
    )
    await service_2.create_log(
        tenant_integration_id=integration_2.id,
        transaction_type="sms_sent",
        status="success",
        recipient="+8801700000002",
    )

    logs_1 = await service_1.list_logs()
    logs_2 = await service_2.list_logs()

    assert len(logs_1) == 1
    assert len(logs_2) == 1
    assert logs_1[0].recipient == "+8801700000001"
    assert logs_2[0].recipient == "+8801700000002"
