"""Messaging credits (SMS and email) a clinic has bought on top of its plan allowance.

The plan allowance is not stored here: it is the plan's `monthly_sms` / `monthly_email` limit
measured against `usage_tracking`. This table holds only *purchased* credits, with an append-only
ledger so every balance can be explained.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CREDIT_CHANNELS = ("sms", "email")
LEDGER_KINDS = ("purchase", "use", "refund", "adjustment")


class CreditBalance(Base):
    __tablename__ = "credit_balances"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_credit_balance_nonneg"),
        CheckConstraint("channel IN ('sms','email')", name="ck_credit_balance_channel"),
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    channel: Mapped[str] = mapped_column(String(10), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )


class CreditLedger(Base):
    """Append-only. `quantity` is signed (+ added, - spent); `balance_after` is the purchased balance."""

    __tablename__ = "credit_ledger"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('purchase','use','refund','adjustment')", name="ck_credit_ledger_kind"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    # e.g. a payment order id, a message id, or an admin note reference
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
