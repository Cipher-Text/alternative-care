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
    amount: float
    payment_method: str
    status: str
    payment_date: date
    created_at: datetime


# ===== bKash Payment Schemas =====

class BkashPaymentCreate(BaseModel):
    """Create bKash payment request."""

    patient_id: str
    visit_id: str | None = None
    amount: float = Field(..., gt=0, le=25000, description="Amount in BDT (max 25,000)")
    description: str | None = Field(None, max_length=500)
    callback_url: str | None = Field(None, description="URL to redirect after payment")


class BkashPaymentExecute(BaseModel):
    """Execute bKash payment request."""

    payment_id: str = Field(..., description="bKash payment ID from create response")


class BkashPaymentQuery(BaseModel):
    """Query bKash payment status."""

    payment_id: str


class BkashRefundRequest(BaseModel):
    """bKash refund request."""

    payment_id: str
    amount: float = Field(..., gt=0, description="Refund amount in BDT")
    transaction_id: str = Field(..., description="bKash transaction ID (trxID)")
    reason: str = Field(..., min_length=1, max_length=500)


class BkashPaymentResponse(BaseModel):
    """bKash payment response."""

    payment_id: str | None = None
    bkash_url: str | None = Field(None, description="URL to redirect user for payment")
    transaction_id: str | None = None
    transaction_status: str | None = None
    amount: float | None = None
    merchant_invoice_number: str | None = None
    customer_msisdn: str | None = None
    status_code: str | None = None
    status_message: str | None = None


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


class InvoiceResponse(InvoiceBase):
    """Invoice response with all fields."""

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


class InvoiceListItem(BaseModel):
    """Lightweight invoice list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    payment_id: str
    status: str
    created_at: datetime


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
