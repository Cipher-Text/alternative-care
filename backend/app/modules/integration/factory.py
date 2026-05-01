"""Integration provider service factory."""

from typing import Type

from app.modules.integration.providers.base import BaseProviderService
from app.modules.integration.providers.bkash_service import BkashIntegrationService
from app.modules.integration.providers.bulksmsbd_service import BulkSMSBDService
from app.modules.integration.providers.smtp_service import SMTPService


# Provider registry mapping provider names to service classes
PROVIDER_REGISTRY: dict[str, Type[BaseProviderService]] = {
    # Payment providers
    "bkash": BkashIntegrationService,
    # SMS providers
    "bulksmsbd": BulkSMSBDService,
    # Can add more: "twilio": TwilioService, "banglalink": BanglalinkService, etc.
    # Email providers
    "smtp": SMTPService,
    # Can add more: "sendgrid": SendGridService, "aws_ses": AWSSESService, etc.
}


class IntegrationProviderFactory:
    """Factory for creating provider service instances."""

    @staticmethod
    def create_provider(
        provider_name: str,
        credentials: dict,
        config: dict | None = None,
    ) -> BaseProviderService:
        """Create provider service instance.

        Args:
            provider_name: Provider name (e.g., "bkash", "bulksmsbd", "smtp")
            credentials: Decrypted credentials dict
            config: Optional provider configuration

        Returns:
            Provider service instance

        Raises:
            ValueError: If provider not found in registry
        """
        provider_class = PROVIDER_REGISTRY.get(provider_name.lower())

        if not provider_class:
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Available providers: {list(PROVIDER_REGISTRY.keys())}"
            )

        return provider_class(credentials=credentials, config=config)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider names."""
        return list(PROVIDER_REGISTRY.keys())
