"""Usage tracking model for plan limits and analytics."""

from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel


class UsageTracking(TenantScopedModel):
    """
    Daily usage tracking for plan limit enforcement.
    """

    __tablename__ = "usage_tracking"
    __table_args__ = (
        UniqueConstraint("tenant_id", "usage_date", name="uq_usage_tracking_tenant_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Date (one row per tenant per day)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Counters (reset monthly based on plan)
    patients_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prescriptions_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_queries_made: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdfs_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sms_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Current totals (for display)
    total_patients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_prescriptions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_ai_queries_this_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
