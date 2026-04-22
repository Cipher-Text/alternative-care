"""Appointment and Visit Pydantic schemas."""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ===== Appointment Schemas =====

class AppointmentBase(BaseModel):
    """Base appointment fields."""

    patient_id: str
    doctor_id: str
    appointment_date: date
    appointment_time: time
    duration_minutes: int = Field(default=30, ge=15, le=240)
    reason: str | None = None
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    """Create appointment request."""

    pass


class AppointmentUpdate(BaseModel):
    """Update appointment request (all fields optional)."""

    appointment_date: date | None = None
    appointment_time: time | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=240)
    reason: str | None = None
    notes: str | None = None
    status: Literal[
        "scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"
    ] | None = None


class AppointmentCancel(BaseModel):
    """Cancel appointment request."""

    cancellation_reason: str | None = None


class AppointmentResponse(AppointmentBase):
    """Appointment response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    status: str
    cancelled_at: date | None = None
    cancellation_reason: str | None = None
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime | None


class AppointmentListItem(BaseModel):
    """Lightweight appointment list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    appointment_date: date
    appointment_time: time
    duration_minutes: int
    status: str
    reason: str | None


# ===== Visit Schemas =====

class VisitBase(BaseModel):
    """Base visit fields."""

    patient_id: str
    doctor_id: str
    visit_date: date
    visit_type: Literal["consultation", "follow_up", "emergency", "routine_checkup"] = "consultation"

    # Clinical information
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    examination_notes: str | None = None

    # Vitals
    temperature: str | None = Field(default=None, description="e.g., '98.6°F' or '37°C'")
    blood_pressure: str | None = Field(default=None, description="e.g., '120/80'")
    pulse_rate: str | None = Field(default=None, description="e.g., '72 bpm'")
    weight: str | None = Field(default=None, description="e.g., '70 kg'")

    # Diagnosis and plan
    provisional_diagnosis: str | None = None
    treatment_plan: str | None = None

    # Follow-up
    follow_up_date: date | None = None
    follow_up_notes: str | None = None


class VisitCreate(VisitBase):
    """Create visit request."""

    appointment_id: str | None = None


class VisitUpdate(BaseModel):
    """Update visit request (all fields optional)."""

    visit_type: Literal["consultation", "follow_up", "emergency", "routine_checkup"] | None = None
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    examination_notes: str | None = None
    temperature: str | None = None
    blood_pressure: str | None = None
    pulse_rate: str | None = None
    weight: str | None = None
    provisional_diagnosis: str | None = None
    treatment_plan: str | None = None
    follow_up_date: date | None = None
    follow_up_notes: str | None = None
    status: Literal["in_progress", "completed"] | None = None


class VisitResponse(VisitBase):
    """Visit response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    appointment_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime | None


class VisitListItem(BaseModel):
    """Lightweight visit list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    visit_date: date
    visit_type: str
    chief_complaint: str | None
    status: str
