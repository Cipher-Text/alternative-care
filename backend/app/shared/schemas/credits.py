"""Schemas for messaging credits."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChannelBalance(BaseModel):
    channel: Literal["sms", "email"]
    allowance_limit: int | None  # None = unlimited
    allowance_used: int
    allowance_remaining: int | None
    purchased: int
    plan: str


class CreditSummary(BaseModel):
    """What a clinic can still send this month: plan allowance first, then purchased credits."""

    channels: list[ChannelBalance]
    # Whether the platform has the provider set up at all (no secrets, just a flag)
    sms_available: bool
    email_available: bool


class LedgerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    kind: str
    quantity: int
    balance_after: int
    reference: str | None
    note: str | None
    created_at: datetime


class CreditAdjustment(BaseModel):
    """Admin grants (+) or removes (-) purchased credits, with a mandatory reason."""

    channel: Literal["sms", "email"]
    quantity: int = Field(..., description="Positive to add, negative to remove")
    note: str = Field(..., min_length=3, max_length=500)

    @model_validator(mode="after")
    def _nonzero(self):
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")
        return self


class MessagingStatus(BaseModel):
    """Admin-only: is each platform provider configured. Never includes credentials."""

    sms: dict
    email: dict
