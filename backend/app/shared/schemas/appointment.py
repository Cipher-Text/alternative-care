"""Appointment and Visit Pydantic schemas."""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


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

class VitalsFields(BaseModel):
    """Vitals taken at a visit. All optional; numbers in the units named by the field."""

    temperature_c: float | None = Field(default=None, ge=30, le=45, description="Degrees Celsius")
    pulse_bpm: int | None = Field(default=None, ge=20, le=250)
    bp_systolic: int | None = Field(default=None, ge=40, le=300)
    bp_diastolic: int | None = Field(default=None, ge=20, le=200)
    respiratory_rate: int | None = Field(default=None, ge=4, le=80, description="Breaths per minute")
    spo2_percent: int | None = Field(default=None, ge=50, le=100)
    weight_kg: float | None = Field(default=None, ge=0.3, le=500)
    height_cm: float | None = Field(default=None, ge=30, le=260)
    blood_sugar_mmol: float | None = Field(default=None, ge=1, le=60, description="mmol/L")
    blood_sugar_type: Literal["fasting", "random", "postprandial"] | None = None
    pain_score: int | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="after")
    def _check_pairs(self):
        if (self.bp_systolic is None) != (self.bp_diastolic is None):
            raise ValueError("Give both systolic and diastolic blood pressure, or neither.")
        if self.bp_systolic is not None and self.bp_diastolic is not None and self.bp_diastolic >= self.bp_systolic:
            raise ValueError("Diastolic pressure must be lower than systolic.")
        if self.blood_sugar_type is not None and self.blood_sugar_mmol is None:
            raise ValueError("Give the blood sugar value as well as when it was taken.")
        return self


RedFlag = Literal[
    "chest_pain", "breathlessness", "severe_bleeding", "infant_high_fever", "loss_of_consciousness",
    "sudden_severe_headache", "sudden_weakness", "persistent_vomiting",
]
ReferralUrgency = Literal["none", "routine", "urgent", "emergency"]


class VisitBase(VitalsFields):
    """Base visit fields."""

    patient_id: str
    doctor_id: str
    visit_date: date
    visit_type: Literal["consultation", "follow_up", "emergency", "routine_checkup"] = "consultation"

    # Clinical information
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    examination_notes: str | None = None

    # Warning signs and referral
    red_flags: list[RedFlag] | None = Field(default=None, max_length=8)
    referral_urgency: ReferralUrgency | None = None

    # Diagnosis and plan
    provisional_diagnosis: str | None = None
    treatment_plan: str | None = None

    # Follow-up
    follow_up_date: date | None = None
    follow_up_notes: str | None = None


class VisitCreate(VisitBase):
    """Create visit request."""

    appointment_id: str | None = None


class VisitUpdate(VitalsFields):
    """Update visit request (all fields optional)."""

    visit_type: Literal["consultation", "follow_up", "emergency", "routine_checkup"] | None = None
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    examination_notes: str | None = None
    red_flags: list[RedFlag] | None = Field(default=None, max_length=8)
    referral_urgency: ReferralUrgency | None = None
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bmi(self) -> float | None:
        """Weight over height squared, to one decimal. None unless both were recorded."""
        if self.weight_kg is None or self.height_cm is None or self.height_cm <= 0:
            return None
        metres = self.height_cm / 100
        return round(self.weight_kg / (metres * metres), 1)


class VisitListItem(VitalsFields):
    """Visit list item: the summary a history view needs (vitals, diagnosis, warning signs)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    visit_date: date
    visit_type: str
    chief_complaint: str | None
    provisional_diagnosis: str | None = None
    treatment_plan: str | None = None
    appointment_id: str | None = None
    red_flags: list[str] | None = None
    referral_urgency: str | None = None
    status: str
