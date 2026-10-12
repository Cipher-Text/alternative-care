"""Messages sent through the public contact form (general questions, Enterprise enquiries,
billing help, reports about a practitioner's profile)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseAuditModel

CONTACT_TOPICS = ("general", "enterprise", "billing", "report_profile", "other")
CONTACT_STATUSES = ("new", "handled")


class ContactMessage(BaseAuditModel):
    __tablename__ = "contact_messages"
    __table_args__ = (
        CheckConstraint(
            "topic IN ('general','enterprise','billing','report_profile','other')",
            name="ck_contact_message_topic",
        ),
        CheckConstraint("status IN ('new','handled')", name="ck_contact_message_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    topic: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # At least one of email / phone is required (enforced in the schema)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    organisation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="new", index=True)
    handled_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
