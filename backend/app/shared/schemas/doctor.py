"""Doctor profile Pydantic schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===== Doctor Profile Schemas =====

class DoctorProfileResponse(BaseModel):
    """Doctor profile response (combines User + Tenant data)."""

    model_config = ConfigDict(from_attributes=True)

    # User fields
    id: str
    email: EmailStr
    full_name: str
    phone: str | None
    avatar_url: str | None
    language: str
    is_active: bool

    # Tenant/Clinic fields
    tenant_id: str
    clinic_name: str | None
    clinic_address: str | None
    division_id: int | None
    district_id: int | None
    upazila_id: int | None
    specializations: list[str]
    license_number: str | None
    is_verified: bool
    verified_at: datetime | None

    # Subscription
    plan: str
    plan_started_at: datetime
    plan_expires_at: datetime | None


class DoctorProfileUpdate(BaseModel):
    """Update doctor profile."""

    # User fields
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = Field(None, max_length=500)
    language: Literal["en", "bn"] | None = None

    # Clinic fields
    clinic_name: str | None = Field(None, max_length=255)
    clinic_address: str | None = None
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None
    license_number: str | None = Field(None, max_length=100)


# ===== Doctor Degree Schemas =====

class DoctorDegreeBase(BaseModel):
    """Base doctor degree fields."""

    degree_type: str = Field(..., max_length=100)
    # e.g., "Bachelor", "Master", "Diploma", "Fellowship"

    degree_name: str = Field(..., max_length=255)
    # e.g., "BHMS", "BAMS", "MD (Homeopathy)"

    specialization: str | None = Field(None, max_length=255)
    # e.g., "Pediatrics", "Dermatology"

    institution_name: str = Field(..., max_length=500)
    institution_location: str | None = Field(None, max_length=255)

    start_year: int | None = Field(None, ge=1900, le=2100)
    completion_year: int = Field(..., ge=1900, le=2100)

    certificate_url: str | None = Field(None, max_length=500)
    display_order: int = Field(0, ge=0)


class DoctorDegreeCreate(DoctorDegreeBase):
    """Create doctor degree request."""
    pass


class DoctorDegreeUpdate(BaseModel):
    """Update doctor degree request."""

    degree_type: str | None = Field(None, max_length=100)
    degree_name: str | None = Field(None, max_length=255)
    specialization: str | None = Field(None, max_length=255)
    institution_name: str | None = Field(None, max_length=500)
    institution_location: str | None = Field(None, max_length=255)
    start_year: int | None = Field(None, ge=1900, le=2100)
    completion_year: int | None = Field(None, ge=1900, le=2100)
    certificate_url: str | None = Field(None, max_length=500)
    display_order: int | None = Field(None, ge=0)


class DoctorDegreeResponse(DoctorDegreeBase):
    """Doctor degree response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    tenant_id: str
    is_verified: bool
    verified_at: datetime | None
    verified_by: str | None
    created_at: datetime
    updated_at: datetime | None


# ===== Doctor Training Schemas =====

class DoctorTrainingBase(BaseModel):
    """Base doctor training fields."""

    training_type: str = Field(..., max_length=100)
    # e.g., "Certification", "Workshop", "Conference", "Continuing Education"

    title: str = Field(..., max_length=500)
    # e.g., "Advanced Homeopathic Prescribing"

    provider: str = Field(..., max_length=500)
    # Organization that provided the training

    description: str | None = None
    skills: str | None = None
    # Comma-separated skills gained

    start_date: date | None = None
    completion_date: date
    expiry_date: date | None = None
    # For certifications that expire

    certificate_url: str | None = Field(None, max_length=500)
    credential_id: str | None = Field(None, max_length=255)
    # Unique ID from issuing organization

    display_order: int = Field(0, ge=0)


class DoctorTrainingCreate(DoctorTrainingBase):
    """Create doctor training request."""
    pass


class DoctorTrainingUpdate(BaseModel):
    """Update doctor training request."""

    training_type: str | None = Field(None, max_length=100)
    title: str | None = Field(None, max_length=500)
    provider: str | None = Field(None, max_length=500)
    description: str | None = None
    skills: str | None = None
    start_date: date | None = None
    completion_date: date | None = None
    expiry_date: date | None = None
    certificate_url: str | None = Field(None, max_length=500)
    credential_id: str | None = Field(None, max_length=255)
    display_order: int | None = Field(None, ge=0)


class DoctorTrainingResponse(DoctorTrainingBase):
    """Doctor training response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    tenant_id: str
    is_verified: bool
    verified_at: datetime | None
    verified_by: str | None
    created_at: datetime
    updated_at: datetime | None
