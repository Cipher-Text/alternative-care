"""Log of SMS and email sent for a clinic through the platform's own providers."""

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel


class MessageLog(TenantScopedModel):
    """One message sent on a clinic's behalf: what was sent, to whom, and what the provider answered."""

    __tablename__ = "message_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # sms_sent or email_sent
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # success, failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The provider's message id
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Phone number or email address
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
