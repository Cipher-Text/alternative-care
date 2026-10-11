"""Pharmacy directory Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

DisciplineType = Literal["homeopathy", "ayurveda", "unani", "herbal"]
PharmacyType = Literal["retail", "wholesale", "manufacturer", "depot"]


def _check_pin(latitude: float | None, longitude: float | None) -> None:
    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be provided together")


class PharmacyBase(BaseModel):
    """Editable pharmacy fields."""

    name_en: str = Field(..., min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    pharmacy_type: PharmacyType
    disciplines: list[DisciplineType] = Field(..., min_length=1)
    notes_en: str | None = None
    notes_bn: str | None = None
    address: str | None = Field(None, max_length=500)
    district_id: int | None = None
    upazila_id: int | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    phone: str | None = Field(None, max_length=30)
    whatsapp: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    website_url: str | None = Field(None, max_length=500)
    opening_hours: str | None = Field(None, max_length=500)
    delivers: bool = False
    source_url: str | None = Field(None, max_length=500)
    is_active: bool = True

    @model_validator(mode="after")
    def _pin_is_complete(self):
        _check_pin(self.latitude, self.longitude)
        return self


class PharmacyCreate(PharmacyBase):
    """Create pharmacy request."""


class PharmacyUpdate(BaseModel):
    """Update pharmacy request (all fields optional)."""

    name_en: str | None = Field(None, min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    pharmacy_type: PharmacyType | None = None
    disciplines: list[DisciplineType] | None = Field(None, min_length=1)
    notes_en: str | None = None
    notes_bn: str | None = None
    address: str | None = Field(None, max_length=500)
    district_id: int | None = None
    upazila_id: int | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    phone: str | None = Field(None, max_length=30)
    whatsapp: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    website_url: str | None = Field(None, max_length=500)
    opening_hours: str | None = Field(None, max_length=500)
    delivers: bool | None = None
    source_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    is_verified: bool | None = None
    # Not stored: "an admin re-checked this listing today" — stamps last_confirmed_at
    mark_confirmed: bool | None = None


class PharmacyResponse(PharmacyBase):
    """Full pharmacy record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_verified: bool
    verified_at: datetime | None
    verified_by: str | None
    last_confirmed_at: datetime | None
    distance_km: float | None = None
    created_at: datetime
    updated_at: datetime | None


class PharmacyListItem(BaseModel):
    """List/map row; `distance_km` is set only for near-me searches."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str | None
    pharmacy_type: str
    disciplines: list[str]
    address: str | None
    district_id: int | None
    upazila_id: int | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    whatsapp: str | None
    opening_hours: str | None
    delivers: bool
    is_verified: bool
    last_confirmed_at: datetime | None
    is_active: bool
    distance_km: float | None = None


class PharmacyImportRowError(BaseModel):
    row: int  # 1-based CSV line number (the header is line 1)
    message: str


class PharmacyImportResult(BaseModel):
    created: int
    skipped: int  # rows that already exist (same name in the same district)
    errors: list[PharmacyImportRowError]
