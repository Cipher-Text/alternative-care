"""Appointment and Visit models."""

from datetime import datetime, date, time

from sqlalchemy import Boolean, Date, Integer, String, Text, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import TenantScopedModel


class Appointment(TenantScopedModel):
    """Patient appointment scheduling."""

    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # References
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Appointment timing
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Status: scheduled, confirmed, in_progress, completed, cancelled, no_show
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        index=True,
    )

    # Appointment details
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reminder sent
    reminder_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    visit: Mapped["Visit | None"] = relationship(
        "Visit",
        back_populates="appointment",
        uselist=False,
    )


class Visit(TenantScopedModel):
    """Patient visit record - created when appointment is completed."""

    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # References
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Optional link to appointment (walk-ins won't have appointment)
    appointment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Visit details
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    visit_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="consultation",
    )
    # consultation, follow_up, emergency, routine_checkup

    # Clinical information
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_of_present_illness: Mapped[str | None] = mapped_column(Text, nullable=True)
    examination_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vitals
    temperature: Mapped[str | None] = mapped_column(String(10), nullable=True)
    blood_pressure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pulse_rate: Mapped[str | None] = mapped_column(String(10), nullable=True)
    weight: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Diagnosis and plan
    provisional_diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Follow-up
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status: in_progress, completed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
    )

    # Relationships
    appointment: Mapped["Appointment | None"] = relationship(
        "Appointment",
        back_populates="visit",
    )
