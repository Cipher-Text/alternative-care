"""Integration provider and tenant integration Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ===== Integration Provider Schemas =====


class IntegrationProviderBase(BaseModel):
    """Base integration provider fields."""

    name: str
    display_name: str
    provider_type: Literal["sms", "email", "payment"]
    description: str | None = None
    logo_url: str | None = None
    config_schema: dict | None = None
    supported_countries: list[str] | None = None


class IntegrationProviderResponse(IntegrationProviderBase):
    """Integration provider response (public catalog)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class IntegrationProviderListItem(BaseModel):
    """Lightweight provider list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    provider_type: str
    logo_url: str | None
    is_active: bool


# ===== Tenant Integration Schemas =====


class TenantIntegrationBase(BaseModel):
    """Base tenant integration fields."""

    provider_id: int
    display_name: str | None = None
    is_active: bool = True


class TenantIntegrationCreate(TenantIntegrationBase):
    """Create tenant integration request."""

    credentials: dict = Field(
        ..., description="Provider credentials (will be encrypted before storage)"
    )


class TenantIntegrationUpdate(BaseModel):
    """Update tenant integration request."""

    display_name: str | None = None
    credentials: dict | None = Field(
        None, description="Updated credentials (will be re-encrypted)"
    )
    is_active: bool | None = None


class TenantIntegrationResponse(TenantIntegrationBase):
    """Tenant integration response (credentials excluded)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    is_primary: bool
    last_tested_at: datetime | None
    test_status: str | None
    created_at: datetime
    updated_at: datetime | None

    # Include provider details
    provider: IntegrationProviderListItem | None = None


class TenantIntegrationListItem(BaseModel):
    """Lightweight integration list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    display_name: str | None
    is_primary: bool
    is_active: bool
    test_status: str | None
    created_at: datetime


# ===== Integration Test Schemas =====


class IntegrationTestRequest(BaseModel):
    """Test integration request."""

    # For SMS
    test_phone: str | None = Field(None, description="Phone number for SMS test")

    # For Email
    test_email: str | None = Field(None, description="Email address for email test")

    # For Payment
    test_amount: float | None = Field(None, gt=0, description="Test payment amount")


class IntegrationTestResponse(BaseModel):
    """Test integration response."""

    success: bool
    message: str
    test_type: str
    provider_name: str
    details: dict | None = None
    error: str | None = None


# ===== Integration Log Schemas =====


class IntegrationLogResponse(BaseModel):
    """Integration log response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    tenant_integration_id: int
    transaction_type: str
    status: str
    recipient: str | None
    amount: float | None
    currency: str | None
    external_reference: str | None
    error_message: str | None
    response_status_code: int | None
    created_at: datetime


class IntegrationLogListItem(BaseModel):
    """Lightweight log list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    status: str
    recipient: str | None
    external_reference: str | None
    created_at: datetime


# ===== Send Operation Schemas =====


class SendSMSRequest(BaseModel):
    """Send SMS request."""

    recipient: str = Field(..., description="Phone number (E.164 format recommended)")
    message: str = Field(
        ..., min_length=1, max_length=1600, description="SMS message text"
    )
    provider_id: int | None = Field(
        None, description="Specific provider ID (uses primary if not specified)"
    )


class SendEmailRequest(BaseModel):
    """Send email request."""

    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=255)
    body_html: str | None = Field(None, description="HTML email body")
    body_text: str | None = Field(None, description="Plain text email body")
    provider_id: int | None = Field(
        None, description="Specific provider ID (uses primary if not specified)"
    )


class SendOperationResponse(BaseModel):
    """Send operation response."""

    success: bool
    message: str
    transaction_id: str | None = None
    integration_log_id: int | None = None
    queued: bool = False
