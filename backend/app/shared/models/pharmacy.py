from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import GlobalCatalogModel


class Pharmacy(GlobalCatalogModel):
    """
    Admin-curated directory of pharmacies, wholesalers and depots where practitioners buy
    alternative-medicine stock.

    Always global, never tenant-owned — same shape as `Institution`: no `tenant_id`, every row is
    visible to every authenticated user, only platform admins write. Accuracy depends entirely on
    that curation, so every row carries provenance (`source_url`), a verification stamp, and a
    `last_confirmed_at` date that the UI shows so a stale listing is visibly stale.
    """

    __tablename__ = "pharmacies"
    __table_args__ = (
        # A pin needs both coordinates or neither; a half-set location is meaningless
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)", name="ck_pharmacies_lat_lon_pair"
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="ck_pharmacies_lat_lon_range",
        ),
        Index("ix_pharmacies_lat_lon", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name_en: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    pharmacy_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "retail" | "wholesale" | "manufacturer" | "depot"

    disciplines: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, server_default="{}"
    )
    # subset of: homeopathy, ayurveda, unani, herbal — what they stock

    notes_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Free-text address as people write it; district/upazila are the structured cross-reference
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    upazila_id: Mapped[int | None] = mapped_column(
        ForeignKey("upazilas.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # WGS84. Nullable: a listing without a pin still shows in the list, just not on the map or in
    # "near me" results.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    opening_hours: Mapped[str | None] = mapped_column(String(500), nullable=True)
    delivers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Provenance and freshness
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
