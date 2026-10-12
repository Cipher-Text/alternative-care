"""Schemas for appointment requests (ADR 009, Phase 3)."""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Window = Literal["morning", "afternoon", "evening", "any"]
RequestStatus = Literal["requested", "confirmed", "declined", "cancelled"]


class PortalProfileCreate(BaseModel):
    """The holder adds themselves or a child. Another adult cannot be added from here: they sign in with
    their own phone (an adult dependent can only be recorded by a clinic)."""

    display_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date | None = None
    approx_birth_year: int | None = Field(None, ge=1900, le=2100)
    gender: Literal["male", "female", "other"] | None = None
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None
    relationship: Literal["self", "child"] = "self"

    @model_validator(mode="after")
    def _child_has_an_age(self):
        if self.relationship == "child" and not (self.date_of_birth or self.approx_birth_year):
            raise ValueError("Give a child's date of birth or birth year")
        return self


class AppointmentRequestCreate(BaseModel):
    practitioner_slug: str = Field(..., min_length=2, max_length=200)
    profile_id: str = Field(..., max_length=36)
    preferred_date: date
    preferred_window: Window = "any"
    # Health information: kept short and optional
    reason: str | None = Field(None, max_length=300)
    # The patient agrees that the clinic receives their basic details and links its record to their profile
    consent: bool

    @field_validator("reason")
    @classmethod
    def _reason(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None

    @model_validator(mode="after")
    def _consent(self):
        if not self.consent:
            raise ValueError("Consent is required to send a request")
        return self


class RequestedAppointment(BaseModel):
    date: date
    time: str
    duration_minutes: int
    status: str


class PatientRequestResponse(BaseModel):
    id: str
    status: RequestStatus
    clinic_name: str
    practitioner_slug: str | None
    doctor_name: str | None
    profile_id: str
    profile_name: str
    preferred_date: date
    preferred_window: Window
    reason: str | None
    created_at: datetime
    appointment: RequestedAppointment | None
    decline_reason: str | None
    cancelled_by: str | None


class Requester(BaseModel):
    """What the clinic sees about the person: the basic details they agreed to share."""

    display_name: str
    age_years: int | None
    gender: str | None
    phone: str
    relationship: str
    is_dependent: bool


class ClinicRequestItem(BaseModel):
    id: str
    status: RequestStatus
    requester: Requester
    preferred_date: date
    preferred_window: Window
    reason: str | None
    doctor_id: str | None
    doctor_name: str | None
    created_at: datetime
    appointment: RequestedAppointment | None
    patient_id: str | None
    # This person already has a record here (linked earlier by consent): confirming reuses it
    existing_patient_id: str | None
    decline_reason: str | None
    cancelled_by: str | None


class ConfirmRequest(BaseModel):
    appointment_date: date
    appointment_time: time
    duration_minutes: int = Field(default=30, ge=15, le=240)
    doctor_id: str | None = Field(None, max_length=36)  # default: the practitioner they asked for
    notify_sms: bool = True  # best effort, from the clinic's own SMS allowance


class DeclineRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
    notify_sms: bool = True
