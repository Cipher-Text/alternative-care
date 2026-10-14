"""Schemas for the public practitioner directory."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Availability = Literal["in_person", "online", "both"]
RequestStatus = Literal["new", "contacted", "closed"]

_PHONE = re.compile(r"^\+?[0-9]{7,15}$")


class ListingUpdate(BaseModel):
    """Everything is optional so the doctor can save a partial draft; listing needs a name and a bio."""

    is_listed: bool | None = None
    headline_en: str | None = Field(None, max_length=200)
    headline_bn: str | None = Field(None, max_length=200)
    bio_en: str | None = Field(None, max_length=3000)
    bio_bn: str | None = Field(None, max_length=3000)
    languages: list[str] | None = Field(None, max_length=8)
    consultation_hours: str | None = Field(None, max_length=500)
    availability: Availability | None = None
    show_fee: bool | None = None
    show_phone: bool | None = None
    show_whatsapp: bool | None = None
    accepts_requests: bool | None = None

    @field_validator("languages")
    @classmethod
    def _clean_languages(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [x.strip()[:30] for x in v if x and x.strip()]


class Eligibility(BaseModel):
    """Why a listing is or isn't public right now. Verification is free; the plan is a separate gate."""

    is_listed: bool
    verified: bool
    approved: bool
    in_plan: bool
    has_profile_text: bool
    public: bool
    # machine-readable reasons, e.g. ["not_verified", "not_in_plan"]
    blockers: list[str]


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exists: bool = True
    id: str | None = None
    slug: str | None = None
    is_listed: bool = False
    listed_at: datetime | None = None
    headline_en: str | None = None
    headline_bn: str | None = None
    bio_en: str | None = None
    bio_bn: str | None = None
    languages: list[str] = []
    consultation_hours: str | None = None
    availability: Availability = "in_person"
    show_fee: bool = False
    show_phone: bool = True
    show_whatsapp: bool = True
    accepts_requests: bool = True
    eligibility: Eligibility | None = None


class DirectoryStats(BaseModel):
    """Month-to-date contact numbers shown to the doctor — what listing earns."""

    month: str
    requests: int
    calls: int
    whatsapp: int
    open_requests: int


class ContactRequestCreate(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=120)
    patient_phone: str
    message: str | None = Field(None, max_length=1000)
    preferred_time: str | None = Field(None, max_length=120)
    consent: bool
    # Honeypot: real people never fill this; bots do.
    website: str | None = Field(None, max_length=200)

    @field_validator("patient_phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = re.sub(r"[\s\-()]", "", v)
        if not _PHONE.match(v):
            raise ValueError("Enter a valid phone number")
        return v

    @field_validator("patient_name")
    @classmethod
    def _name(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def _consent(self):
        if not self.consent:
            raise ValueError("Consent is required to send a request")
        return self


class ContactRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_name: str
    patient_phone: str
    message: str | None
    preferred_time: str | None
    status: RequestStatus
    created_at: datetime


class ContactRequestUpdate(BaseModel):
    status: RequestStatus


class ListingEventCreate(BaseModel):
    event_type: Literal["call", "whatsapp"]


class DirectoryVerification(BaseModel):
    """Admin decision about a tenant's credentials. Free, and required to appear publicly."""

    verified: bool
    note: str | None = Field(None, max_length=1000)


class PublicDegree(BaseModel):
    degree_name: str
    institution_name: str
    completion_year: int
    is_verified: bool


class PublicPractitionerItem(BaseModel):
    slug: str
    display_name: str
    clinic_name: str | None
    headline_en: str | None
    headline_bn: str | None
    disciplines: list[str]
    registration_body: str | None
    years_of_experience: int | None
    district_en: str | None
    district_bn: str | None
    languages: list[str]
    availability: Availability
    fee_bdt: int | None
    verified_at: datetime | None
    logo_url: str | None


class PublicPractitioner(PublicPractitionerItem):
    bio_en: str | None
    bio_bn: str | None
    consultation_hours: str | None
    follow_up_fee_bdt: int | None
    address_line_1: str | None
    address_line_2: str | None
    landmark: str | None
    upazila_en: str | None
    upazila_bn: str | None
    division_en: str | None
    division_bn: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    whatsapp: str | None
    accepts_requests: bool
    degrees: list[PublicDegree]


class PublicPractitionerList(BaseModel):
    """Every visible profile, however many there are: one profile shows one, a hundred show a hundred."""

    total: int
    items: list[PublicPractitionerItem]
