"""Patient management models."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import TenantScopedModel

if TYPE_CHECKING:
    from app.shared.models.tenant import Tenant


class Patient(TenantScopedModel):
    """Patient model with comprehensive medical and contact information."""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Demographics
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # male, female, other

    blood_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # A+, A-, B+, B-, AB+, AB-, O+, O-

    # Contact
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    division_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    upazila_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Medical information
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Photo
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Follow-up
    next_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="patients")
    tags: Mapped[list["PatientTag"]] = relationship("PatientTag", back_populates="patient")
    diagnoses: Mapped[list["PatientDiagnosis"]] = relationship(
        "PatientDiagnosis", back_populates="patient"
    )


class PatientTag(TenantScopedModel):
    """
    Patient tags for categorization (special case, chronic, treatment, allergy).
    """

    __tablename__ = "patient_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tag type: special_case, chronic, treatment, allergy
    tag_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Tag value/label
    tag_value: Mapped[str] = mapped_column(String(255), nullable=False)

    # Additional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="tags")


class PatientDiagnosis(TenantScopedModel):
    """
    Patient diagnosis records with optional ICD codes.
    """

    __tablename__ = "patient_diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Visit reference (optional - links to visit if available)
    visit_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Diagnosis
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # When diagnosed
    diagnosed_at: Mapped[datetime] = mapped_column(Date, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="diagnoses")
