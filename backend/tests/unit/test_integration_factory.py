"""Unit tests for integration provider factory."""

import pytest

from app.modules.integration.factory import IntegrationProviderFactory
from app.modules.integration.providers.bkash_service import BkashIntegrationService
from app.modules.integration.providers.bulksmsbd_service import BulkSMSBDService
from app.modules.integration.providers.smtp_service import SMTPService



def test_create_provider_bulksmsbd_success() -> None:
    service = IntegrationProviderFactory.create_provider(
        provider_name="bulksmsbd",
        credentials={"api_key": "k", "sender_id": "ALTCARE"},
    )
    assert isinstance(service, BulkSMSBDService)



def test_create_provider_smtp_case_insensitive_success() -> None:
    service = IntegrationProviderFactory.create_provider(
        provider_name="SMTP",
        credentials={
            "host": "smtp.example.com",
            "port": 587,
            "username": "u",
            "password": "p",
            "from_email": "noreply@example.com",
        },
    )
    assert isinstance(service, SMTPService)



def test_create_provider_bkash_success() -> None:
    service = IntegrationProviderFactory.create_provider(
        provider_name="bkash",
        credentials={
            "app_key": "k",
            "app_secret": "s",
            "username": "u",
            "password": "p",
            "environment": "sandbox",
        },
    )
    assert isinstance(service, BkashIntegrationService)



def test_create_provider_unknown_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Provider 'unknown' not found"):
        IntegrationProviderFactory.create_provider(
            provider_name="unknown",
            credentials={},
        )



def test_get_available_providers_contains_expected_entries() -> None:
    providers = IntegrationProviderFactory.get_available_providers()
    assert "bkash" in providers
    assert "bulksmsbd" in providers
    assert "smtp" in providers
