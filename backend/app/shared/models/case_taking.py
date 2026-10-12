"""Stored answers for system-specific case-taking (see app/shared/case_taking)."""

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel


class PatientCaseProfile(TenantScopedModel):
    """What stays true about the patient for one system: constitution, generals, history. One row per
    patient and system."""

    __tablename__ = "patient_case_profiles"
    __table_args__ = (UniqueConstraint("patient_id", "system", name="uq_patient_case_profile"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    system: Mapped[str] = mapped_column(String(20), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class VisitAssessment(TenantScopedModel):
    """What was taken at one visit for one system: the complaint in detail, the prescription, the response."""

    __tablename__ = "visit_assessments"
    __table_args__ = (UniqueConstraint("visit_id", "system", name="uq_visit_assessment"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    visit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    system: Mapped[str] = mapped_column(String(20), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
