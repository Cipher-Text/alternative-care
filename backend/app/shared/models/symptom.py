"""Symptom models with normalization and alias support."""

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import GlobalCatalogModel


class Symptom(GlobalCatalogModel):
    """
    Normalized symptom table.
    Master list of symptoms used across all medical systems.
    """

    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Null for global (admin-curated) symptoms, set for tenant-owned ones —
    # see the CHECK constraint below, which is the only thing enforcing that.
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

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
        Index(
            "ix_symptoms_name_en_trgm",
            "name_en",
            postgresql_using="gin",
            postgresql_ops={"name_en": "gin_trgm_ops"},
        ),
        Index(
            "ix_symptoms_name_bn_trgm",
            "name_bn",
            postgresql_using="gin",
            postgresql_ops={"name_bn": "gin_trgm_ops"},
        ),
        CheckConstraint(
            "(is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL)",
            name="ck_symptoms_tenant_global",
        ),
    )


class SymptomAlias(GlobalCatalogModel):
    """
    Symptom aliases for search (handles transliteration, common names, variations).
    CRITICAL for Bangladesh context: "মাথা ব্যথা" → "matha byatha" → "headache"
    """

    __tablename__ = "symptom_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Null when the alias was added to a global symptom by a platform admin
    # (admins have tenant_id = NULL); no CHECK here since this table has no
    # is_global of its own — it just mirrors whatever creator/symptom it's on.
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
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
        Index(
            "ix_symptom_aliases_alias_en_trgm",
            "alias_en",
            postgresql_using="gin",
            postgresql_ops={"alias_en": "gin_trgm_ops"},
        ),
        Index(
            "ix_symptom_aliases_alias_bn_trgm",
            "alias_bn",
            postgresql_using="gin",
            postgresql_ops={"alias_bn": "gin_trgm_ops"},
        ),
    )


class MedicineSymptomMapping(GlobalCatalogModel):
    """
    Updated medicine-to-symptom mapping using normalized symptom references.
    Replaces the old MedicineSymptom table's text-based approach.
    """

    __tablename__ = "medicine_symptom_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Null when the mapping was created by a platform admin (tenant_id = NULL)
    # linking two global rows; no CHECK here, same reasoning as the aliases.
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

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
