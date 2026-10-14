"""Payment and Invoice Pydantic schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ===== Payment Schemas =====

class PaymentBase(BaseModel):
    """Base payment fields."""

    patient_id: str
    visit_id: str | None = None
    amount: float = Field(..., gt=0, description="Payment amount in BDT")
    payment_method: Literal["cash", "bkash"] = Field(default="cash")
    description: str | None = Field(None, max_length=500)
    payment_date: date = Field(default_factory=date.today)


class PaymentCreate(PaymentBase):
    """Create payment request."""
    pass


class PaymentUpdate(BaseModel):
    """Update payment request (limited fields)."""

    description: str | None = None
    status: Literal["paid", "pending", "failed", "refunded"] | None = None


class PaymentResponse(PaymentBase):
    """Payment response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    currency: str
    transaction_id: str | None
    status: str
    integration_log_id: int | None
    received_by: str
    created_at: datetime
    updated_at: datetime | None
    created_by: str | None
    updated_by: str | None


class PaymentListItem(BaseModel):
    """Lightweight payment list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    patient_name: str | None = None
    patient_phone: str | None = None
    amount: float
    currency: str = "BDT"
    payment_method: str
    status: str
    payment_date: date
    description: str | None = None
    created_at: datetime

# ===== Invoice Schemas =====

class InvoiceBase(BaseModel):
    """Base invoice fields."""

    payment_id: str


class InvoiceCreate(InvoiceBase):
    """Create invoice request."""

    due_date: date | None = None


class InvoiceUpdate(BaseModel):
    """Update invoice request."""

    status: Literal["draft", "sent", "paid", "overdue", "cancelled"] | None = None
    due_date: date | None = None


class InvoiceItemOut(BaseModel):
    """One billed line (an invoice bills exactly one payment, so there is one)."""

    description: str
    quantity: int = 1
    unit_price: float
    total: float


class InvoiceResponse(InvoiceBase):
    """Invoice response with all fields.

    The `patient_*`, `amount`, `issue_date`, `items` and `notes` fields are derived from the
    invoiced payment (an invoice is a document for one payment, not a standalone bill).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    invoice_number: str
    pdf_url: str | None
    status: str
    due_date: date | None
    created_at: datetime
    updated_at: datetime | None
    created_by: str | None
    updated_by: str | None
    patient_id: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    amount: float = 0
    currency: str = "BDT"
    issue_date: date | None = None
    items: list[InvoiceItemOut] = []
    notes: str | None = None


class InvoiceListItem(BaseModel):
    """Lightweight invoice list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    payment_id: str
    status: str
    created_at: datetime
    due_date: date | None = None
    patient_id: str | None = None
    patient_name: str | None = None
    amount: float = 0
    currency: str = "BDT"
    issue_date: date | None = None


# ===== Payment Summary Schemas =====

class PaymentSummary(BaseModel):
    """Payment summary statistics."""

    total_payments: int
    total_amount: float
    paid_amount: float
    pending_amount: float
    cash_amount: float
    bkash_amount: float
    period_start: date | None = None
    period_end: date | None = None
