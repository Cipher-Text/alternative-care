"""Patient Pydantic schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===== Patient Schemas =====

class PatientBase(BaseModel):
    """Base patient fields."""

    full_name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: Literal["male", "female", "other"] | None = None
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None

    # Contact
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    whatsapp: str | None = Field(None, max_length=20)

    # Address
    address: str | None = None
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    # Medical
    chief_complaint: str | None = None
    medical_history: str | None = None

    # Photo
    photo_url: str | None = Field(None, max_length=500)

    # Follow-up
    next_visit_date: date | None = None


class PatientCreate(PatientBase):
    """Create patient request."""
    pass


class PatientUpdate(BaseModel):
    """Update patient request (all fields optional)."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: Literal["male", "female", "other"] | None = None
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None

    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    whatsapp: str | None = Field(None, max_length=20)

    address: str | None = None
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    chief_complaint: str | None = None
    medical_history: str | None = None
    photo_url: str | None = Field(None, max_length=500)
    next_visit_date: date | None = None
    is_active: bool | None = None


class PatientResponse(PatientBase):
    """Patient response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    created_by: str | None
    updated_by: str | None


class PatientListItem(BaseModel):
    """Lightweight patient list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    phone: str | None
    date_of_birth: date | None
    gender: str | None
    next_visit_date: date | None
    is_active: bool


class PatientSearchResult(PatientListItem):
    """Patient search result with additional context."""

    model_config = ConfigDict(from_attributes=True)

    email: str | None
    chief_complaint: str | None
    created_at: datetime


# ===== Patient Tag Schemas =====

class PatientTagBase(BaseModel):
    """Base patient tag fields."""

    tag_type: Literal["special_case", "chronic", "treatment", "allergy"]
    tag_value: str = Field(..., min_length=1, max_length=255)
    notes: str | None = None


class PatientTagCreate(PatientTagBase):
    """Create patient tag request."""
    patient_id: str | None = None  # Optional - will be set from URL path in route handler


class PatientTagUpdate(BaseModel):
    """Update patient tag request."""

    tag_type: Literal["special_case", "chronic", "treatment", "allergy"] | None = None
    tag_value: str | None = Field(None, min_length=1, max_length=255)
    notes: str | None = None


class PatientTagResponse(PatientTagBase):
    """Patient tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime | None


# ===== Patient Diagnosis Schemas =====

class PatientDiagnosisBase(BaseModel):
    """Base patient diagnosis fields."""

    description: str = Field(..., min_length=1)
    icd_code: str | None = Field(None, max_length=20)
    diagnosed_at: date


class PatientDiagnosisCreate(PatientDiagnosisBase):
    """Create patient diagnosis request."""

    patient_id: str | None = None  # Optional - will be set from URL path in route handler
    visit_id: str | None = None


class PatientDiagnosisUpdate(BaseModel):
    """Update patient diagnosis request."""

    description: str | None = Field(None, min_length=1)
    icd_code: str | None = Field(None, max_length=20)
    diagnosed_at: date | None = None
    is_active: bool | None = None


class PatientDiagnosisResponse(PatientDiagnosisBase):
    """Patient diagnosis response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    visit_id: str | None
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
