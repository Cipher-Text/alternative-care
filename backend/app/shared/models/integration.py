"""Integration provider models (SMS, Email, Payment)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import TenantScopedModel


class IntegrationProvider(Base):
    """
    Catalog of available integration providers (SMS, Email, Payment).
    Platform-level, no tenant_id.
    """

    __tablename__ = "integration_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Provider info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # e.g., "Twilio", "SendGrid", "SSLCommerz"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Type: sms, email, payment
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Logo
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Configuration schema (JSON schema for required credentials)
    config_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example: {"api_key": "string", "api_secret": "string"}

    # Supported countries (for payment/SMS providers)
    supported_countries: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TenantIntegration(TenantScopedModel):
    """
    Tenant-specific integration configurations.
    Credentials are encrypted before storage.
    """

    __tablename__ = "tenant_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Display name (custom label for this integration)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Encrypted credentials (Fernet encrypted JSON)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)

    # Is this the primary provider for this type?
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Last tested
    last_tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    test_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # success, failed


class IntegrationLog(TenantScopedModel):
    """
    Audit log for all integration transactions (SMS, Email, Payment).
    Full request/response tracking.
    """

    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_integration_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Transaction type: sms_sent, email_sent, payment_initiated, payment_completed
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Request details
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Response details
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status: pending, success, failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Error details (if failed)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # External reference (transaction ID from provider)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Recipient (phone/email) or payer
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Amount (for payment transactions)
    amount: Mapped[float | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
