"""Facebook profile promotion: a plan benefit (Pro and Enterprise) delivered by AltCare staff.

A clinic asks to be featured on the AltCare Facebook page. Staff draft the post from the public
profile; the doctor approves the exact text; only then can staff mark it posted. Posting itself is
manual (no Facebook API), so `post_url` is the link staff paste afterwards.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel

FB_STATUSES = ("requested", "drafted", "approved", "posted", "rejected", "cancelled")
# A request that still needs someone to act; a clinic may have only one at a time
FB_OPEN = ("requested", "drafted", "approved")
# Requests that use up the quarterly quota (cancelled and rejected ones give it back)
FB_COUNTED = ("requested", "drafted", "approved", "posted")


class FacebookFeatureRequest(TenantScopedModel):
    __tablename__ = "facebook_feature_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested','drafted','approved','posted','rejected','cancelled')",
            name="ck_fb_request_status",
        ),
        # At most one open request per clinic, enforced by the database
        Index(
            "uq_fb_request_one_open",
            "tenant_id",
            unique=True,
            postgresql_where=text("status IN ('requested','drafted','approved')"),
        ),
        Index("ix_fb_requests_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    listing_id: Mapped[str | None] = mapped_column(
        ForeignKey("practitioner_listings.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="requested", index=True)
    requested_by: Mapped[str] = mapped_column(String(36), nullable=False)
    # What the doctor wants highlighted, or preferred timing
    doctor_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    draft_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    drafted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    drafted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # The doctor's reply when asking for changes
    doctor_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The exact text the doctor approved; staff cannot change it after approval
    approved_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
