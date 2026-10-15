"""Patient management models."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Date, Integer, String, Text, ForeignKey, UniqueConstraint
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

    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)

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


class PatientHealthProfile(TenantScopedModel):
    """Long-lived health background and safety flags for one patient (one row per patient).

    Closed lists are stored as codes from `app/shared/health_options.py`. Visit-time findings (vitals, red
    flags) live on the visit instead; this is what stays true between visits."""

    __tablename__ = "patient_health_profiles"
    __table_args__ = (UniqueConstraint("patient_id", name="uq_patient_health_profile_patient"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chronic_conditions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # [{"type": "drug", "substance": "Penicillin", "severity": "severe"}]
    allergies: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    family_history: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    smoking: Mapped[str | None] = mapped_column(String(10), nullable=True)
    alcohol: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # Paan, jorda or gul
    betel_tobacco: Mapped[str | None] = mapped_column(String(10), nullable=True)
    diet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    pregnant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lmp_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    breastfeeding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    on_allopathic_medicines: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    on_blood_thinners: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recent_surgery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_medicines_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_surgeries_note: Mapped[str | None] = mapped_column(Text, nullable=True)
