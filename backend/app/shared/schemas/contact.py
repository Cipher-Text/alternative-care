"""Schemas for the public contact form and the staff inbox."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ContactTopic = Literal["general", "enterprise", "billing", "report_profile", "other"]
_PHONE = re.compile(r"^\+?[0-9]{7,15}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ContactMessageCreate(BaseModel):
    topic: ContactTopic = "general"
    name: str = Field(..., min_length=2, max_length=120)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=30)
    organisation: str | None = Field(None, max_length=150)
    message: str = Field(..., min_length=10, max_length=2000)
    consent: bool
    # Honeypot: real people never fill this; bots do.
    website: str | None = Field(None, max_length=200)

    @field_validator("name", "message")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        if not v:
            return None
        if not _EMAIL.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str | None) -> str | None:
        v = re.sub(r"[\s\-()]", "", v or "")
        if not v:
            return None
        if not _PHONE.match(v):
            raise ValueError("Enter a valid phone number")
        return v

    @model_validator(mode="after")
    def _checks(self):
        if not (self.email or self.phone):
            raise ValueError("Give an email address or a phone number so we can reply")
        if not self.consent:
            raise ValueError("Consent is required to send a message")
        return self


class ContactMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    name: str
    email: str | None
    phone: str | None
    organisation: str | None
    message: str
    status: Literal["new", "handled"]
    created_at: datetime
    handled_at: datetime | None


class ContactMessageUpdate(BaseModel):
    status: Literal["new", "handled"]
