"""Symptom models with normalization and alias support."""

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import TenantScopedModel


class Symptom(TenantScopedModel):
    """
    Normalized symptom table.
    Master list of symptoms used across all medical systems.
    """

    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Symptom name (bilingual)
    name_en: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Description (bilingual)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Category for organization
    # e.g., "respiratory", "digestive", "neurological", "skin", "mental"
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Global vs tenant-specific
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    medicine_symptoms: Mapped[list["MedicineSymptomMapping"]] = relationship(
        "MedicineSymptomMapping",
        back_populates="symptom",
        cascade="all, delete-orphan",
    )
    aliases: Mapped[list["SymptomAlias"]] = relationship(
        "SymptomAlias",
        back_populates="symptom",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_symptoms_name_en_trgm", "name_en", postgresql_using="gin"),
        Index("ix_symptoms_name_bn_trgm", "name_bn", postgresql_using="gin"),
    )


class SymptomAlias(TenantScopedModel):
    """
    Symptom aliases for search (handles transliteration, common names, variations).
    CRITICAL for Bangladesh context: "মাথা ব্যথা" → "matha byatha" → "headache"
    """

    __tablename__ = "symptom_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symptom_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("symptoms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alias text (bilingual)
    alias_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alias_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Alias type
    # transliteration: "matha byatha"
    # common_name: "severe headache", "migraine"
    # regional: regional variations
    # colloquial: everyday terms
    alias_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="common_name",
    )

    # Match priority (higher = better match)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    symptom: Mapped["Symptom"] = relationship("Symptom", back_populates="aliases")

    __table_args__ = (
        Index("ix_symptom_aliases_alias_en_trgm", "alias_en", postgresql_using="gin"),
        Index("ix_symptom_aliases_alias_bn_trgm", "alias_bn", postgresql_using="gin"),
    )


class MedicineSymptomMapping(TenantScopedModel):
    """
    Updated medicine-to-symptom mapping using normalized symptom references.
    Replaces the old MedicineSymptom table's text-based approach.
    """

    __tablename__ = "medicine_symptom_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    medicine_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    symptom_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("symptoms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Modality notes (e.g., "worse at night", "better from warmth")
    modality_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    modality_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Match strength (1-10, for ranking)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    medicine: Mapped["Medicine"] = relationship(
        "Medicine",
        back_populates="symptom_mappings",
    )
    symptom: Mapped["Symptom"] = relationship(
        "Symptom",
        back_populates="medicine_symptoms",
    )

    __table_args__ = (
        # Ensure unique medicine-symptom pairs
        Index("ix_medicine_symptom_unique", "medicine_id", "symptom_id", unique=True),
    )
