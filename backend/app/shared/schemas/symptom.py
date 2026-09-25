"""Symptom, SymptomAlias, and MedicineSymptomMapping Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ===== Symptom Schemas =====

class SymptomBase(BaseModel):
    """Base symptom fields."""

    name_en: str = Field(..., max_length=500)
    name_bn: str | None = Field(default=None, max_length=500)
    description_en: str | None = None
    description_bn: str | None = None
    category: str | None = Field(
        default=None,
        description="e.g., respiratory, digestive, neurological, skin, mental"
    )


class SymptomCreate(SymptomBase):
    """Create symptom request."""

    is_global: bool = False


class SymptomUpdate(BaseModel):
    """Update symptom request (all fields optional)."""

    name_en: str | None = Field(default=None, max_length=500)
    name_bn: str | None = Field(default=None, max_length=500)
    description_en: str | None = None
    description_bn: str | None = None
    category: str | None = None
    is_active: bool | None = None


class SymptomResponse(SymptomBase):
    """Symptom response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str | None
    is_global: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class SymptomListItem(BaseModel):
    """Lightweight symptom list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str | None
    category: str | None
    is_global: bool
    is_active: bool


# ===== Symptom Alias Schemas =====

class SymptomAliasBase(BaseModel):
    """Base symptom alias fields."""

    alias_en: str | None = Field(default=None, max_length=500)
    alias_bn: str | None = Field(default=None, max_length=500)
    alias_type: Literal[
        "transliteration",
        "common_name",
        "regional",
        "colloquial"
    ] = "common_name"
    priority: int = Field(default=5, ge=1, le=10)


class SymptomAliasCreate(SymptomAliasBase):
    """Create symptom alias request."""

    symptom_id: int


class SymptomAliasUpdate(BaseModel):
    """Update symptom alias request (all fields optional)."""

    alias_en: str | None = Field(default=None, max_length=500)
    alias_bn: str | None = Field(default=None, max_length=500)
    alias_type: Literal[
        "transliteration",
        "common_name",
        "regional",
        "colloquial"
    ] | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    is_active: bool | None = None


class SymptomAliasResponse(SymptomAliasBase):
    """Symptom alias response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str | None
    symptom_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


# ===== Medicine-Symptom Mapping Schemas =====

class MedicineSymptomMappingBase(BaseModel):
    """Base medicine-symptom mapping fields."""

    medicine_id: int
    symptom_id: int
    modality_en: str | None = Field(
        default=None,
        description="e.g., 'worse at night', 'better from warmth'"
    )
    modality_bn: str | None = None
    strength: int = Field(default=5, ge=1, le=10, description="Match strength for ranking")


class MedicineSymptomMappingCreate(MedicineSymptomMappingBase):
    """Create medicine-symptom mapping request."""

    pass


class MedicineSymptomMappingUpdate(BaseModel):
    """Update medicine-symptom mapping request (all fields optional)."""

    modality_en: str | None = None
    modality_bn: str | None = None
    strength: int | None = Field(default=None, ge=1, le=10)
    is_active: bool | None = None


class MedicineSymptomMappingResponse(MedicineSymptomMappingBase):
    """Medicine-symptom mapping response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


# ===== Combined Schemas (for API responses) =====

class SymptomWithAliases(SymptomResponse):
    """Symptom with its aliases."""

    aliases: list[SymptomAliasResponse] = []


class SymptomSearchResult(BaseModel):
    """Symptom search result with relevance."""

    symptom: SymptomResponse
    matched_term: str  # The term that was matched (could be name or alias)
    match_type: Literal["exact", "alias", "fuzzy"]
    relevance_score: float = Field(ge=0.0, le=1.0)
