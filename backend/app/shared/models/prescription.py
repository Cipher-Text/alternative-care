"""Prescription models."""

from sqlalchemy import Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import TenantScopedModel


class Prescription(TenantScopedModel):
    """Prescription model - one per patient visit."""

    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    visit_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Doctor who prescribed
    prescribed_by: Mapped[str] = mapped_column(String(36), nullable=False)

    # Notes
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctors_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    advice: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PDF
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_generated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status: draft, issued, voided
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # Relationships
    items: Mapped[list["PrescriptionItem"]] = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
    )


class PrescriptionItem(TenantScopedModel):
    """Individual medicine items in a prescription."""

    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Medicine reference (nullable - allows free-text entry)
    medicine_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Free-text medicine name (if not in database)
    medicine_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Dosage and frequency
    dosage: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g., "30C", "200C", "1M", "2 tablets", "5ml"

    frequency: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g., "3 times daily", "Morning & Evening", "Before meals"

    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g., "7 days", "2 weeks", "1 month"

    # Quantity
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Special instructions
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Display order
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")
