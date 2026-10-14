"""Read access to a clinic's message log."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import MessageLog


class MessageLogService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def list_logs(
        self, transaction_type: str | None = None, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[MessageLog]:
        query = select(MessageLog).where(MessageLog.tenant_id == self.tenant_id)
        if transaction_type:
            query = query.where(MessageLog.transaction_type == transaction_type)
        if status:
            query = query.where(MessageLog.status == status)
        rows = await self.db.execute(query.order_by(MessageLog.created_at.desc()).limit(limit).offset(offset))
        return list(rows.scalars().all())
