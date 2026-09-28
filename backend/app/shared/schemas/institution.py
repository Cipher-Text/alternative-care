"""College/institution catalog Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DisciplineType = Literal["homeopathy", "ayurveda", "unani", "herbal"]


class CollegeBase(BaseModel):
    """Base college fields."""

    name_en: str = Field(..., min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    college_type: Literal["government", "private"]
    disciplines: list[DisciplineType] = Field(..., min_length=1)
    courses_offered: str | None = None
    location: str | None = Field(None, max_length=500)
    district_id: int | None = None
    website_url: str | None = Field(None, max_length=500)
    registration_code: str | None = Field(None, max_length=50)
    source_url: str | None = Field(None, max_length=500)
    is_active: bool = True


class CollegeCreate(CollegeBase):
    """Create college request."""

    pass


class CollegeUpdate(BaseModel):
    """Update college request (all fields optional)."""

    name_en: str | None = Field(None, min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    college_type: Literal["government", "private"] | None = None
    disciplines: list[DisciplineType] | None = Field(None, min_length=1)
    courses_offered: str | None = None
    location: str | None = Field(None, max_length=500)
    district_id: int | None = None
    website_url: str | None = Field(None, max_length=500)
    registration_code: str | None = Field(None, max_length=50)
    source_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    is_verified: bool | None = None


class CollegeResponse(CollegeBase):
    """College response with metadata — authenticated (admin/doctor) view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_verified: bool
    verified_at: datetime | None
    verified_by: str | None
    created_at: datetime
    updated_at: datetime | None


class CollegeListItem(BaseModel):
    """Lightweight college list item — also used for the public directory (no verified_by)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str | None
    college_type: str
    disciplines: list[str]
    courses_offered: str | None
    location: str | None
    district_id: int | None
    website_url: str | None
    registration_code: str | None
    source_url: str | None
    is_verified: bool
    is_active: bool
