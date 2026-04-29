"""Prescription Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ===== Prescription Item Schemas =====

class PrescriptionItemBase(BaseModel):
    """Base prescription item fields."""

    medicine_id: int | None = None
    medicine_name: str | None = Field(None, max_length=500, description="Free-text medicine name if not in database")
    dosage: str = Field(..., max_length=255, description="e.g., '30C', '200C', '2 tablets'")
    frequency: str = Field(..., max_length=255, description="e.g., '3 times daily', 'Morning & Evening'")
    duration: str | None = Field(None, max_length=100, description="e.g., '7 days', '2 weeks'")
    quantity: float | None = Field(None, ge=0, description="Quantity to dispense")
    instructions: str | None = Field(None, description="Special instructions")
    display_order: int = Field(default=0, ge=0)


class PrescriptionItemCreate(PrescriptionItemBase):
    """Create prescription item request."""
    pass


class PrescriptionItemUpdate(BaseModel):
    """Update prescription item request (all fields optional)."""

    medicine_id: int | None = None
    medicine_name: str | None = Field(None, max_length=500)
    dosage: str | None = Field(None, max_length=255)
    frequency: str | None = Field(None, max_length=255)
    duration: str | None = Field(None, max_length=100)
    quantity: float | None = Field(None, ge=0)
    instructions: str | None = None
    display_order: int | None = Field(None, ge=0)


class PrescriptionItemResponse(PrescriptionItemBase):
    """Prescription item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime | None


# ===== Prescription Schemas =====

class PrescriptionBase(BaseModel):
    """Base prescription fields."""

    patient_id: str
    visit_id: str | None = None
    diagnosis: str | None = Field(None, description="Clinical diagnosis")
    doctors_notes: str | None = Field(None, description="Doctor's clinical notes")
    advice: str | None = Field(None, description="General advice for patient")


class PrescriptionCreate(PrescriptionBase):
    """Create prescription request."""

    items: list[PrescriptionItemCreate] = Field(default_factory=list, description="Prescription items (medicines)")
    status: Literal["draft", "issued"] = Field(default="draft", description="Initial status")


class PrescriptionUpdate(BaseModel):
    """Update prescription request (all fields optional).

    Note: Prescriptions are immutable once issued. Only draft prescriptions can be updated.
    """

    diagnosis: str | None = None
    doctors_notes: str | None = None
    advice: str | None = None
    status: Literal["draft", "issued", "voided"] | None = None


class PrescriptionResponse(PrescriptionBase):
    """Prescription response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    prescribed_by: str
    status: str
    pdf_url: str | None
    pdf_generated_at: str | None
    created_at: datetime
    updated_at: datetime | None
    created_by: str | None
    updated_by: str | None

    # Include items in response
    items: list[PrescriptionItemResponse] = Field(default_factory=list)


class PrescriptionListItem(BaseModel):
    """Lightweight prescription list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    visit_id: str | None
    prescribed_by: str
    diagnosis: str | None
    status: str
    pdf_url: str | None
    created_at: datetime


class PrescriptionWithItemsCreate(PrescriptionCreate):
    """Extended create schema for prescriptions with items."""
    pass
