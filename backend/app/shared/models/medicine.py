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
    system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

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
    symptoms: Mapped[list["MedicineSymptom"]] = relationship(
        "MedicineSymptom",
        back_populates="medicine",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_medicines_name_en_trgm", "name_en", postgresql_using="gin"),
        Index("ix_medicines_system", "system"),
    )


class MedicineSymptom(TenantScopedModel):
    """
    Symptom-to-medicine mapping for symptom-based search.
    """

    __tablename__ = "medicine_symptoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Symptom text (bilingual)
    symptom_en: Mapped[str] = mapped_column(String(500), nullable=False)
    symptom_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Modality notes (e.g., "worse at night", "better from warmth")
    modality_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    modality_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Match strength (1-10, for ranking)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Relationships
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="symptoms")

    __table_args__ = (
        Index("ix_medicine_symptoms_symptom_en_trgm", "symptom_en", postgresql_using="gin"),
    )
