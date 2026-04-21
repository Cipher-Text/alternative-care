"""Doctor credentials models (degrees and training)."""

from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel


class DoctorDegree(TenantScopedModel):
    """
    Doctor's academic degrees (MBBS, BHMS, BAMS, BUMS, etc.).
    """

    __tablename__ = "doctor_degrees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Degree information
    degree_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g., "Bachelor", "Master", "Diploma", "Fellowship"

    degree_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g., "BHMS", "BAMS", "MD (Homeopathy)"

    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # e.g., "Pediatrics", "Dermatology"

    # Institution
    institution_name: Mapped[str] = mapped_column(String(500), nullable=False)
    institution_location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Dates
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Certificate
    certificate_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Display order (for UI sorting)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DoctorTraining(TenantScopedModel):
    """
    Doctor's professional training, certifications, and workshops.
    """

    __tablename__ = "doctor_trainings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Training information
    training_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g., "Certification", "Workshop", "Conference", "Continuing Education"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # e.g., "Advanced Homeopathic Prescribing", "Ayurvedic Panchakarma Certification"

    provider: Mapped[str] = mapped_column(String(500), nullable=False)
    # Organization/institution that provided the training

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Skills gained
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Comma-separated or JSON array

    # Dates
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    completion_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    # For certifications that expire

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Certificate
    certificate_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Unique ID from issuing organization

    # Display order
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
