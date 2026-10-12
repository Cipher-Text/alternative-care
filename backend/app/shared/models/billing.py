"""Checkout: credit packs for sale and the orders clinics pay AltCare for.

`billing_orders` is AltCare's own revenue (plan subscriptions and credit top-ups). It is separate
from `payments`/`invoices`, which are a clinic collecting money from its patients.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseAuditModel

ORDER_KINDS = ("subscription", "credit_pack")
ORDER_STATUSES = ("pending", "paid", "failed", "cancelled", "expired")
BILLING_PERIODS = ("monthly", "yearly")


class CreditPack(BaseAuditModel):
    """A top-up pack an admin sells, e.g. 500 SMS for a price. Prices are admin-editable."""

    __tablename__ = "credit_packs"
    __table_args__ = (
        CheckConstraint("channel IN ('sms','email')", name="ck_credit_pack_channel"),
        CheckConstraint("quantity > 0", name="ck_credit_pack_quantity"),
        CheckConstraint("price > 0", name="ck_credit_pack_price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BDT")
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BillingOrder(BaseAuditModel):
    """One checkout attempt. Fulfilled (plan activated or credits added) exactly once, on a
    confirmed payment, under a row lock — see `app/modules/billing/orders.py`."""

    __tablename__ = "billing_orders"
    __table_args__ = (
        CheckConstraint("kind IN ('subscription','credit_pack')", name="ck_billing_order_kind"),
        CheckConstraint(
            "status IN ('pending','paid','failed','cancelled','expired')", name="ck_billing_order_status"
        ),
        Index("ix_billing_orders_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    receipt_no: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Who at the clinic paid (recorded for support and receipts)
    payer_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    kind: Mapped[str] = mapped_column(String(15), nullable=False)
    # subscription
    plan_key: Mapped[str | None] = mapped_column(String(20), nullable=True)
    period: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # credit pack (snapshotted so later edits to the pack never change a past order)
    pack_id: Mapped[int | None] = mapped_column(
        ForeignKey("credit_packs.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BDT")

    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending", index=True)
    gateway: Mapped[str] = mapped_column(String(20), nullable=False)
    gateway_txn_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gateway_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # What fulfilment did, e.g. {"plan_expires_at": "..."} or {"balance": 700}
    fulfilment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
