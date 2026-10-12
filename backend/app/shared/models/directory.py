"""Public practitioner directory (Phase 2 of the public-site strategy).

A listing is an opt-in public view over a tenant's real data (ADR-008): the clinic's address, fees,
credentials and specializations stay on `Tenant`/`DoctorDegree`; the listing only adds what a patient
needs and the doctor chooses to publish.
"""

from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseAuditModel, TenantScopedModel

AVAILABILITY_MODES = ("in_person", "online", "both")
REQUEST_STATUSES = ("new", "contacted", "closed")
EVENT_TYPES = ("call", "whatsapp")


class PractitionerListing(TenantScopedModel):
    """One public listing per tenant. Visible only when listed, verified, approved and in plan."""

    __tablename__ = "practitioner_listings"
    __table_args__ = (
        CheckConstraint("availability IN ('in_person','online','both')", name="ck_listing_availability"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # The doctor the listing represents (credentials and name come from this user)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)

    is_listed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    headline_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    headline_bn: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bio_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(30)), nullable=False, server_default="{}")
    consultation_hours: Mapped[str | None] = mapped_column(String(500), nullable=True)
    availability: Mapped[str] = mapped_column(String(10), nullable=False, default="in_person")

    # What the doctor chooses to show (name, credentials and clinic address always show when listed)
    show_fee: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_phone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    accepts_requests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ContactRequest(TenantScopedModel):
    """A patient's "request an appointment" message. Not a booking: the clinic calls back."""

    __tablename__ = "contact_requests"
    __table_args__ = (
        CheckConstraint("status IN ('new','contacted','closed')", name="ck_contact_request_status"),
        Index("ix_contact_requests_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    listing_id: Mapped[str] = mapped_column(
        ForeignKey("practitioner_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="new", index=True)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ListingEvent(BaseAuditModel):
    """A call or WhatsApp tap on a public profile — counted so the doctor can see what listing earns."""

    __tablename__ = "listing_events"
    __table_args__ = (Index("ix_listing_events_listing_created", "listing_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    listing_id: Mapped[str] = mapped_column(
        ForeignKey("practitioner_listings.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)
