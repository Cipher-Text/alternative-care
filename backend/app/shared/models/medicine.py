"""Medicine database models."""

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import TenantScopedModel


class Medicine(TenantScopedModel):
    """
    Medicine database - curated global medicines + tenant-specific additions.
    Filtered by doctor's specializations.
    """

    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Medicine name (bilingual)
    name_en: Mapped[str] = mapped_column(String(500), nullable=False)
    name_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Medical system: homeopathy, ayurveda, unani, herbal
    system: Mapped[str] = mapped_column(String(50), nullable=False)

    # Category (system-specific)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Homeopathy: Mineral, Plant, Animal, Nosode
    # Ayurveda: Rasayana, Panchakarma, Shamana
    # Unani: Mushil, Muhallil, Musakkin
    # Herbal: Anti-inflammatory, Adaptogen, Digestive

    # Description (bilingual)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Potency/strength (for homeopathy: 6C, 30C, 200C, 1M, etc.)
    potency: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Dosage guidance (bilingual)
    dosage_guidance_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    dosage_guidance_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Indications (bilingual)
    indications_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    indications_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Contraindications (bilingual)
    contraindications_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    contraindications_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Global vs tenant-specific
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Global medicines curated by admins, tenant-specific added by doctors

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    symptom_mappings: Mapped[list["MedicineSymptomMapping"]] = relationship(
        "MedicineSymptomMapping",
        back_populates="medicine",
        cascade="all, delete-orphan",
    )
    aliases: Mapped[list["MedicineAlias"]] = relationship(
        "MedicineAlias",
        back_populates="medicine",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_medicines_name_en_trgm",
            "name_en",
            postgresql_using="gin",
            postgresql_ops={"name_en": "gin_trgm_ops"},
        ),
        Index(
            "ix_medicines_name_bn_trgm",
            "name_bn",
            postgresql_using="gin",
            postgresql_ops={"name_bn": "gin_trgm_ops"},
        ),
        Index("ix_medicines_system", "system"),
    )


class MedicineAlias(TenantScopedModel):
    """
    Medicine aliases for search (handles transliteration, brand names, common names).
    CRITICAL for Bangladesh context: Different spellings, local names, brand variations.
    """

    __tablename__ = "medicine_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alias text (bilingual)
    alias_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alias_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Alias type
    # transliteration: "arnika" for "Arnica"
    # common_name: "Indian ginseng" for "Ashwagandha"
    # brand_name: brand/manufacturer specific names
    # regional: regional variations
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
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="aliases")

    __table_args__ = (
        Index(
            "ix_medicine_aliases_alias_en_trgm",
            "alias_en",
            postgresql_using="gin",
            postgresql_ops={"alias_en": "gin_trgm_ops"},
        ),
        Index(
            "ix_medicine_aliases_alias_bn_trgm",
            "alias_bn",
            postgresql_using="gin",
            postgresql_ops={"alias_bn": "gin_trgm_ops"},
        ),
    )
