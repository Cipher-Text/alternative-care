"""Schemas for patient identity (ADR 009, Phase 1)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.phone import normalize_bd_mobile

Relationship = Literal["self", "child", "spouse", "parent", "other"]


def _phone(v: str) -> str:
    try:
        return normalize_bd_mobile(v)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


class VerifyRequest(BaseModel):
    phone: str

    _norm = field_validator("phone")(_phone)


class VerifyRequestResponse(BaseModel):
    challenge_id: str
    expires_at: datetime
    resend_after_seconds: int
    phone_masked: str


class VerifyConfirm(BaseModel):
    challenge_id: str = Field(..., max_length=36)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
    # The staff member confirms they read the consent script to the patient (recorded)
    script_confirmed: bool

    @model_validator(mode="after")
    def _told(self):
        if not self.script_confirmed:
            raise ValueError("Read the consent script to the patient before verifying")
        return self


class VerifyConfirmResponse(BaseModel):
    verification_token: str
    expires_at: datetime
    # Deliberately only a flag: names are shown only after staff search by the visitor's name
    has_profiles: bool


class ProfileSearch(BaseModel):
    verification_token: str
    name: str = Field(..., min_length=2, max_length=120)


class ProfileSummary(BaseModel):
    id: str
    display_name: str
    age_years: int | None
    gender: str | None
    relationship: Relationship
    is_dependent: bool
    # True when this person already has a record at the searching clinic
    linked_here: bool


class ProfilePrefillRequest(BaseModel):
    verification_token: str
    profile_id: str


class BasicDetails(BaseModel):
    """What a link shares: basic details only, never anything clinical."""

    profile_id: str
    display_name: str
    date_of_birth: date | None
    approx_birth_year: int | None
    gender: str | None
    division_id: int | None
    district_id: int | None
    upazila_id: int | None
    relationship: Relationship
    is_dependent: bool
    phone: str  # the verified phone


class NewProfile(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date | None = None
    approx_birth_year: int | None = Field(None, ge=1900, le=2100)
    gender: str | None = Field(None, max_length=20)
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None
    relationship: Relationship = "self"
    is_dependent: bool | None = None  # defaults to true for a child


class LinkRequest(BaseModel):
    verification_token: str
    patient_id: str
    profile_id: str | None = None
    new_profile: NewProfile | None = None

    @model_validator(mode="after")
    def _one_of(self):
        if bool(self.profile_id) == bool(self.new_profile):
            raise ValueError("Give either profile_id or new_profile")
        return self


class LinkResponse(BaseModel):
    link_id: str
    patient_id: str
    profile_id: str
    profile_display_name: str
    linked_at: datetime
    profile_reused: bool  # an existing profile (same name and date of birth) was used


class PatientIdentityStatus(BaseModel):
    """Level 0 (clinic-entered) or level 1 (phone-verified) for one of this clinic's patients."""

    patient_id: str
    level: Literal[0, 1]
    linked: bool
    linked_at: datetime | None
    method: str | None
    profile_display_name: str | None
    # The patient can see this clinic's records in their own portal account
    portal_access: bool = False


class RevokeRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class ClaimCodeResponse(BaseModel):
    code: str  # shown once; only a hash is stored
    expires_at: datetime


class ClaimRequest(BaseModel):
    phone: str
    claim_code: str = Field(..., min_length=8, max_length=12)

    _norm = field_validator("phone")(_phone)


class ClaimConfirm(BaseModel):
    challenge_id: str = Field(..., max_length=36)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
    relationship: Relationship = "self"
    consent: bool

    @model_validator(mode="after")
    def _consent(self):
        if not self.consent:
            raise ValueError("Consent is required to link your record")
        return self


class ClaimResult(BaseModel):
    linked: bool
    clinic_name: str
    profile_display_name: str


# ===== Patient portal (phase 2) =====


class PortalAuthRequest(BaseModel):
    phone: str

    _norm = field_validator("phone")(_phone)


class PortalAuthVerify(BaseModel):
    challenge_id: str = Field(..., max_length=36)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


class PortalToken(BaseModel):
    access_token: str
    expires_at: datetime


class PortalClinic(BaseModel):
    link_id: str
    clinic_name: str
    linked_at: datetime


class PortalProfile(BaseModel):
    id: str
    display_name: str
    age_years: int | None
    gender: str | None
    relationship: Relationship
    is_dependent: bool
    clinics: list[PortalClinic]


class PortalMe(BaseModel):
    phone_masked: str
    profiles: list[PortalProfile]


class PortalActivate(BaseModel):
    code: str = Field(..., min_length=8, max_length=12)


class PortalAppointment(BaseModel):
    clinic_name: str
    doctor_name: str | None
    date: date
    time: str
    duration_minutes: int
    status: str
    reason: str | None


class PortalPrescriptionItem(BaseModel):
    medicine: str
    dosage: str
    frequency: str
    duration: str | None
    instructions: str | None


class PortalPrescription(BaseModel):
    id: str
    link_id: str
    clinic_name: str
    doctor_name: str | None
    date: date
    diagnosis: str | None
    advice: str | None
    items: list[PortalPrescriptionItem]


class PortalReceipt(BaseModel):
    clinic_name: str
    date: date
    amount: float
    currency: str
    method: str
    description: str | None
    invoice_number: str | None


class PortalRecords(BaseModel):
    """Read-only. Doctor's private notes, visit examination notes and unissued drafts are never included."""

    appointments: list[PortalAppointment]
    prescriptions: list[PortalPrescription]
    receipts: list[PortalReceipt]
