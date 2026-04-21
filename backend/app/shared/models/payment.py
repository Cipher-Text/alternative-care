"""Payment and invoice models."""

from datetime import date

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import TenantScopedModel


class Payment(TenantScopedModel):
    """Payment records for consultations and services."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    visit_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Amount
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BDT")

    # Payment method: cash, bkash, nagad, rocket, card, other
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)

    # Integration reference (if digital payment)
    integration_log_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Transaction reference from payment gateway
    transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status: paid, pending, failed, refunded
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="paid")

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment date (can differ from created_at for manual entry)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Received by
    received_by: Mapped[str] = mapped_column(String(36), nullable=False)


class Invoice(TenantScopedModel):
    """Invoice generation for payments."""

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Invoice number (auto-generated, tenant-scoped)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # PDF
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status: draft, sent, paid, overdue, cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # Due date (for pending payments)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
