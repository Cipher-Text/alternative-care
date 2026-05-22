"""Medicine Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.schemas.symptom import SymptomListItem


# ===== Medicine Schemas =====


class MedicineBase(BaseModel):
    """Base medicine fields."""

    name_en: str = Field(..., min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    system: Literal["homeopathy", "ayurveda", "unani", "herbal"]
    category: str | None = Field(None, max_length=255)
    description_en: str | None = None
    description_bn: str | None = None
    potency: str | None = Field(None, max_length=50)
    dosage_guidance_en: str | None = None
    dosage_guidance_bn: str | None = None
    indications_en: str | None = None
    indications_bn: str | None = None
    contraindications_en: str | None = None
    contraindications_bn: str | None = None
    is_global: bool = False
    is_active: bool = True


class MedicineCreate(MedicineBase):
    """Create medicine request."""

    pass


class MedicineUpdate(BaseModel):
    """Update medicine request."""

    name_en: str | None = Field(None, min_length=1, max_length=500)
    name_bn: str | None = Field(None, max_length=500)
    system: Literal["homeopathy", "ayurveda", "unani", "herbal"] | None = None
    category: str | None = Field(None, max_length=255)
    description_en: str | None = None
    description_bn: str | None = None
    potency: str | None = Field(None, max_length=50)
    dosage_guidance_en: str | None = None
    dosage_guidance_bn: str | None = None
    indications_en: str | None = None
    indications_bn: str | None = None
    contraindications_en: str | None = None
    contraindications_bn: str | None = None
    is_active: bool | None = None


class MedicineResponse(MedicineBase):
    """Medicine response with metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None = None


class MedicineListItem(BaseModel):
    """Lightweight medicine list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str | None
    system: str
    category: str | None
    potency: str | None
    is_global: bool
    is_active: bool


class MedicineSearchResult(BaseModel):
    """Medicine search/autocomplete result."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str | None
    system: str
    potency: str | None
    category: str | None
    matched_alias: str | None = None  # If matched via alias
    rank: float = 0.0  # Search ranking score


# ===== Medicine Alias Schemas =====


class MedicineAliasBase(BaseModel):
    """Base medicine alias fields."""

    alias_en: str | None = Field(None, max_length=500)
    alias_bn: str | None = Field(None, max_length=500)
    alias_type: Literal[
        "transliteration", "common_name", "brand_name", "regional", "abbreviation"
    ] = "common_name"
    priority: int = Field(5, ge=1, le=10)
    is_active: bool = True


class MedicineAliasCreate(MedicineAliasBase):
    """Create medicine alias request."""

    medicine_id: int


class MedicineAliasUpdate(BaseModel):
    """Update medicine alias request."""

    alias_en: str | None = Field(None, max_length=500)
    alias_bn: str | None = Field(None, max_length=500)
    alias_type: Literal[
        "transliteration", "common_name", "brand_name", "regional", "abbreviation"
    ] | None = None
    priority: int | None = Field(None, ge=1, le=10)
    is_active: bool | None = None


class MedicineAliasResponse(MedicineAliasBase):
    """Medicine alias response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    medicine_id: int
    tenant_id: str | None
    created_at: datetime


# ===== Combined Schemas =====


class MedicineWithSymptoms(MedicineResponse):
    """Medicine with its symptom mappings."""

    symptoms: list["SymptomListItem"] = []
