"""Schemas for sending SMS and email through the platform's providers, and the message log."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageLogListItem(BaseModel):
    """One sent message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    status: str
    recipient: str | None
    external_reference: str | None
    error_message: str | None = None
    created_at: datetime


class SendSMSRequest(BaseModel):
    """Send SMS request."""

    recipient: str = Field(..., description="Phone number (E.164 format recommended)")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message text")


class SendEmailRequest(BaseModel):
    """Send email request."""

    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=255)
    body_html: str | None = Field(None, description="HTML email body")
    body_text: str | None = Field(None, description="Plain text email body")


class SendOperationResponse(BaseModel):
    """Send operation response."""

    success: bool
    message: str
    transaction_id: str | None = None
    queued: bool = False
