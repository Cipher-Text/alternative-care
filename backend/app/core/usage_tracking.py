"""Per-tenant daily usage counters (Stage 1 "Billing enforcement").

Records what happened (prescriptions issued, SMS sent, AI queries made) so
Stage 4's quota enforcement and the admin usage view have real data to work
from. Does not itself enforce any limit.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import UsageTracking


class UsageService:
    """Writes and reads UsageTracking rows for a single tenant."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _get_today_row(self, today: date) -> UsageTracking | None:
        result = await self.db.execute(
            select(UsageTracking).where(
                UsageTracking.tenant_id == self.tenant_id,
                UsageTracking.usage_date == today,
            )
        )
        return result.scalar_one_or_none()

    async def increment(self, field: str, amount: int = 1) -> UsageTracking:
        """Increment one of today's counters, creating the day's row if needed."""
        today = date.today()
        row = await self._get_today_row(today)

        if row is None:
            row = UsageTracking(tenant_id=self.tenant_id, usage_date=today)
            self.db.add(row)
            try:
                await self.db.flush()
            except IntegrityError:
                # Concurrent request for the same tenant/day created it first.
                await self.db.rollback()
                row = await self._get_today_row(today)

        setattr(row, field, getattr(row, field) + amount)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_month_to_date(self) -> dict:
        """Sum this tenant's counters across the current calendar month."""
        today = date.today()
        month_start = today.replace(day=1)

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(UsageTracking.prescriptions_created), 0),
                func.coalesce(func.sum(UsageTracking.ai_queries_made), 0),
                func.coalesce(func.sum(UsageTracking.sms_sent), 0),
                func.coalesce(func.sum(UsageTracking.pdfs_generated), 0),
            ).where(
                UsageTracking.tenant_id == self.tenant_id,
                UsageTracking.usage_date >= month_start,
                UsageTracking.usage_date <= today,
            )
        )
        prescriptions_created, ai_queries_made, sms_sent, pdfs_generated = result.one()
        return {
            "prescriptions_created": prescriptions_created,
            "ai_queries_made": ai_queries_made,
            "sms_sent": sms_sent,
            "pdfs_generated": pdfs_generated,
        }
