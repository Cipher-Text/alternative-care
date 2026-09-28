"""College/institution catalog model (Track D, docs/planning/future-scope-2026-09.md)."""

from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import GlobalCatalogModel


class College(GlobalCatalogModel):
    """
    Admin-curated directory of institutions teaching alternative-medicine
    disciplines (homeopathy, ayurveda, unani, herbal).

    Always global, never tenant-owned — colleges aren't tenants, so unlike
    Medicine/Symptom this is a genuinely new catalog table, not a hybrid
    global-or-tenant one (no tenant_id column at all; see ADR-008 and
    future-scope-2026-09.md, Track D).
    """

    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name_en: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    college_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "government" | "private"

    disciplines: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        server_default="{}",
    )
    # subset of: homeopathy, ayurveda, unani, herbal

    courses_offered: Mapped[str | None] = mapped_column(Text, nullable=True)
    # free text (e.g. "DHMS", "DUMS, DAMS") — Bangladesh's own diploma
    # naming isn't modeled as its own enum/table here; future-scope-2026-09.md
    # explicitly defers that level of taxonomy detail until a stage needs it

    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Free-text as typed/scraped (e.g. "Green Road, Farmgate, Dhaka") —
    # district_id below is the structured cross-reference derived from it,
    # not a replacement for it (the free text carries detail — ward, road,
    # town — a district can't).
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # The issuing board's own registration/code number for this institution
    # (e.g. Bangladesh Homeopathic Medical Education Council's 3-digit
    # college code) — not unique in this column: the source register itself
    # has been observed to reuse a code across two differently named
    # colleges, so this is provenance, not a candidate key.
    registration_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Provenance — every row seeded from a web search starts here, not from
    # an official board register (docs/planning/future-scope-2026-09.md
    # addendum). is_verified/verified_at/verified_by is how an admin later
    # marks a row cross-checked against the real Bangladesh Homeopathic
    # Board / Board of Unani and Ayurvedic Systems of Medicine — the same
    # verification shape already used on DoctorDegree/DoctorTraining/Tenant.
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
