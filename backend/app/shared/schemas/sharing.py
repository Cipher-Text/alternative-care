"""Schemas for patient-controlled sharing between clinics (ADR 009, Phase 4)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ShareCategory = Literal["prescriptions", "diagnoses"]
ShareStatus = Literal["active", "expired", "revoked", "ended"]


class ShareCreate(BaseModel):
    source_link_id: str = Field(..., max_length=36)  # the clinic whose records are shared
    recipient_link_id: str = Field(..., max_length=36)  # the clinic that may read them
    categories: list[ShareCategory] = Field(..., min_length=1)
    days: Literal[7, 30, 90]
    consent: bool

    @field_validator("categories")
    @classmethod
    def _unique(cls, v: list[str]) -> list[str]:
        return sorted(set(v))

    @model_validator(mode="after")
    def _consent(self):
        if not self.consent:
            raise ValueError("Consent is required to share your records")
        return self


class PortalShare(BaseModel):
    id: str
    profile_id: str
    profile_name: str
    source_clinic: str
    recipient_clinic: str
    categories: list[str]
    # active | expired | revoked | ended (a clinic was removed from the account, so the share stopped)
    status: ShareStatus
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    access_count: int
    last_accessed_at: datetime | None


class ShareSummary(BaseModel):
    """What a clinic sees about a share (never the records themselves)."""

    share_id: str
    clinic_name: str  # the other clinic
    categories: list[str]
    status: ShareStatus
    expires_at: datetime
    access_count: int
    last_accessed_at: datetime | None


class PatientSharing(BaseModel):
    incoming: list[ShareSummary]  # shared WITH this clinic about this patient
    outgoing: list[ShareSummary]  # this clinic's records shared with others


class SharedPrescriptionItem(BaseModel):
    medicine: str
    dosage: str
    frequency: str
    duration: str | None
    instructions: str | None


class SharedPrescription(BaseModel):
    source_clinic: str
    shared_until: datetime
    date: date
    doctor_name: str | None
    diagnosis: str | None
    advice: str | None
    items: list[SharedPrescriptionItem]


class SharedDiagnosis(BaseModel):
    source_clinic: str
    shared_until: datetime
    description: str
    icd_code: str | None
    diagnosed_at: date
    is_active: bool


class SharedRecords(BaseModel):
    """Read-only, read live from the source clinic, and only what the patient chose to share."""

    prescriptions: list[SharedPrescription]
    diagnoses: list[SharedDiagnosis]
    shares: list[ShareSummary]
