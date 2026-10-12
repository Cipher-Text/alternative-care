"""Public contact messages: store, notify staff, and let an admin mark them handled."""

import html
from datetime import datetime, timezone
from uuid import uuid4

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.models import ContactMessage, User
from app.shared.schemas import ContactMessageCreate

logger = structlog.get_logger()

TOPIC_LABEL = {
    "general": "General question",
    "enterprise": "Enterprise enquiry",
    "billing": "Billing help",
    "report_profile": "Report a practitioner profile",
    "other": "Other",
}


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ContactMessageCreate) -> None:
        if data.website:  # honeypot tripped: look successful to the bot, store nothing
            return
        message = ContactMessage(
            id=str(uuid4()),
            topic=data.topic,
            name=data.name,
            email=data.email,
            phone=data.phone,
            organisation=(data.organisation or "").strip() or None,
            message=data.message,
            consented_at=datetime.now(timezone.utc),
        )
        self.db.add(message)
        await self.db.commit()
        await self._notify_staff(message)

    async def _notify_staff(self, m: ContactMessage) -> None:
        """Best-effort email to active admins; the message is already saved."""
        try:
            from app.core.system_email import send_system_email_task

            admins = (
                await self.db.execute(select(User.email).where(User.role == "admin", User.is_active.is_(True)))
            ).scalars().all()
            e = html.escape
            label = TOPIC_LABEL.get(m.topic, m.topic)
            facts = [
                f"Topic: {label}",
                f"Name: {m.name}",
                f"Email: {m.email or '-'}",
                f"Phone: {m.phone or '-'}",
                f"Organisation: {m.organisation or '-'}",
                f"Message: {m.message}",
            ]
            link = f"{settings.FRONTEND_URL}/admin/contact"
            for address in admins:
                send_system_email_task.delay(
                    recipient=address,
                    subject=f"AltCare contact: {label} from {m.name}",
                    body_text="\n".join(facts) + f"\n\n{link}",
                    body_html="".join(f"<p>{e(f)}</p>" for f in facts) + f'<p><a href="{e(link)}">{e(link)}</a></p>',
                )
        except Exception:  # noqa: BLE001 — a mail failure must never lose or fail the message
            logger.warning("contact_notify_failed", message_id=m.id)

    async def list(self, status_filter: str | None, limit: int, offset: int):
        q = select(ContactMessage)
        if status_filter:
            q = q.where(ContactMessage.status == status_filter)
        rows = await self.db.execute(q.order_by(ContactMessage.created_at.desc()).limit(limit).offset(offset))
        return rows.scalars().all()

    async def set_status(self, message_id: str, new_status: str, admin_id: str) -> ContactMessage:
        m = (await self.db.execute(select(ContactMessage).where(ContactMessage.id == message_id))).scalar_one_or_none()
        if m is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
        m.status = new_status
        m.handled_by = admin_id if new_status == "handled" else None
        m.handled_at = datetime.now(timezone.utc) if new_status == "handled" else None
        m.updated_by = admin_id
        await self.db.commit()
        await self.db.refresh(m)
        return m
