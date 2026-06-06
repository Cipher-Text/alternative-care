"""Tenant/Clinic Pydantic schemas for Phase 1."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator, ConfigDict


# ============================================================================
# Tenant Profile Schemas (Phase 1: Essential Fields)
# ============================================================================


class TenantProfileUpdate(BaseModel):
    """Update clinic profile information (Phase 1 essential fields)."""

    # Basic
    name: str | None = Field(None, max_length=255)
    clinic_name: str | None = Field(None, max_length=255)

    # Contact (separate clinic contact from owner)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    clinic_phone: str | None = Field(None, max_length=20)
    clinic_email: EmailStr | None = None
    clinic_whatsapp: str | None = Field(None, max_length=20)

    # Structured address
    address_line_1: str | None = Field(None, max_length=255)
    address_line_2: str | None = Field(None, max_length=255)
    clinic_address: str | None = None  # Legacy field - keep for backward compatibility
    postal_code: str | None = Field(None, max_length=10)
    landmark: str | None = Field(None, max_length=255)
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    # Geolocation (for Google Maps)
    latitude: float | None = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: float | None = Field(None, ge=-180, le=180, description="Longitude coordinate")

    # Professional credentials
    license_number: str | None = Field(None, max_length=100)
    registration_body: str | None = Field(
        None,
        max_length=100,
        description="e.g., BMDC, Bangladesh Homeopathic Board"
    )
    registration_number: str | None = Field(None, max_length=100)
    years_of_experience: int | None = Field(None, ge=0, le=100)
    specializations: list[str] | None = Field(None, min_length=1, max_length=4)

    # Branding
    logo_url: str | None = Field(None, max_length=500)
    description_en: str | None = None
    description_bn: str | None = None

    # Fees (in paisa: 100 paisa = 1 BDT)
    consultation_fee: int | None = Field(
        None,
        ge=0,
        description="Consultation fee in paisa (100 paisa = 1 BDT)"
    )
    follow_up_fee: int | None = Field(
        None,
        ge=0,
        description="Follow-up fee in paisa (100 paisa = 1 BDT)"
    )

    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, v: list[str] | None) -> list[str] | None:
        """Validate specializations are from allowed list."""
        if v is None:
            return v
        allowed = {"homeopathy", "ayurveda", "unani", "herbal"}
        for spec in v:
            if spec not in allowed:
                raise ValueError(f"Invalid specialization '{spec}'. Allowed: {allowed}")
        return list(set(v))


class TenantResponse(BaseModel):
    """Complete tenant/clinic profile response (Phase 1 fields)."""

    # Basic
    id: str
    name: str
    clinic_name: str | None

    # Contact
    email: str
    phone: str | None
    clinic_phone: str | None
    clinic_email: str | None
    clinic_whatsapp: str | None

    # Address
    address_line_1: str | None
    address_line_2: str | None
    clinic_address: str | None  # Legacy
    postal_code: str | None
    landmark: str | None
    division_id: int | None
    district_id: int | None
    upazila_id: int | None

    # Geolocation
    latitude: float | None
    longitude: float | None

    # Professional
    specializations: list[str]
    license_number: str | None
    registration_body: str | None
    registration_number: str | None
    years_of_experience: int | None
    is_verified: bool
    verified_at: datetime | None

    # Branding
    logo_url: str | None
    description_en: str | None
    description_bn: str | None

    # Fees
    consultation_fee: int | None
    follow_up_fee: int | None

    # Subscription
    plan: str
    plan_started_at: datetime
    plan_expires_at: datetime | None

    # Status
    is_active: bool
    is_approved: bool
    approved_at: datetime | None

    # Audit
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TenantListItem(BaseModel):
    """Minimal tenant info for listings."""

    id: str
    name: str
    clinic_name: str | None
    specializations: list[str]
    division_id: int | None
    district_id: int | None
    is_verified: bool
    plan: str
    logo_url: str | None

    model_config = ConfigDict(from_attributes=True)


class TenantPublicProfile(BaseModel):
    """Public clinic profile (for patient-facing views)."""

    id: str
    clinic_name: str | None
    description_en: str | None
    description_bn: str | None

    # Contact (public)
    clinic_phone: str | None
    clinic_email: str | None
    clinic_whatsapp: str | None

    # Address
    address_line_1: str | None
    address_line_2: str | None
    landmark: str | None
    division_id: int | None
    district_id: int | None
    postal_code: str | None

    # Location
    latitude: float | None
    longitude: float | None

    # Professional
    specializations: list[str]
    registration_body: str | None
    registration_number: str | None
    years_of_experience: int | None
    is_verified: bool

    # Branding
    logo_url: str | None

    # Fees (in BDT for display)
    consultation_fee_bdt: float | None = None
    follow_up_fee_bdt: float | None = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        """Convert paisa to BDT for display."""
        if 'consultation_fee' in data and data['consultation_fee']:
            data['consultation_fee_bdt'] = data['consultation_fee'] / 100
        if 'follow_up_fee' in data and data['follow_up_fee']:
            data['follow_up_fee_bdt'] = data['follow_up_fee'] / 100
        super().__init__(**data)
