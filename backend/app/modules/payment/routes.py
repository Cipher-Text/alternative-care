"""Payment and invoice API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, RequireDoctor
from app.modules.payment.service import PaymentService
from app.shared.schemas import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentListItem,
    BkashPaymentCreate,
    BkashPaymentExecute,
    BkashPaymentQuery,
    BkashPaymentResponse,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListItem,
    PaymentSummary,
)

router = APIRouter()


def get_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PaymentService:
    """Dependency for payment service with tenant context."""
    return PaymentService(db=db, tenant_id=current_user.tenant_id)


# ===== Payment Endpoints =====


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a manual payment (cash).

    - Only authenticated users can create payments
    - Automatically scoped to user's tenant
    - Payment is immediately marked as 'paid'
    - Use this for cash payments or manual entry
    """
    return await service.create_payment(data, received_by=current_user.user_id)


@router.get("", response_model=list[PaymentListItem])
async def list_payments(
    service: Annotated[PaymentService, Depends(get_payment_service)],
    patient_id: str | None = Query(None, description="Filter by patient ID"),
    visit_id: str | None = Query(None, description="Filter by visit ID"),
    payment_method: str | None = Query(None, description="Filter by payment method (cash, bkash)"),
    status: str | None = Query(None, description="Filter by status (paid, pending, failed, refunded)"),
    date_from: date | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List payments with filters.

    - Filter by patient, visit, method, status, or date range
    - Supports pagination
    - Ordered by payment date (newest first)
    """
    return await service.list_payments(
        patient_id=patient_id,
        visit_id=visit_id,
        payment_method=payment_method,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=PaymentSummary)
async def get_payment_summary(
    service: Annotated[PaymentService, Depends(get_payment_service)],
    date_from: date | None = Query(None, description="Start date for summary"),
    date_to: date | None = Query(None, description="End date for summary"),
):
    """
    Get payment summary statistics.

    - Total payments count and amount
    - Breakdown by status (paid, pending)
    - Breakdown by method (cash, bKash)
    - Optional date range filter
    """
    return await service.get_payment_summary(date_from=date_from, date_to=date_to)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Get payment by ID.

    - Returns full payment details
    - Tenant filtering applied automatically
    """
    return await service.get_payment(payment_id)


# ===== bKash Payment Endpoints =====


@router.post("/bkash/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_bkash_payment(
    data: BkashPaymentCreate,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a bKash payment and get payment URL.

    - Creates payment record in 'pending' status
    - Returns bKash payment URL for user to complete payment
    - Maximum amount: 25,000 BDT
    - Returns: payment_id, bkash_payment_id, bkash_url, merchant_invoice_number
    """
    return await service.create_bkash_payment(data, created_by=current_user.user_id)


@router.post("/bkash/execute", response_model=PaymentResponse)
async def execute_bkash_payment(
    data: BkashPaymentExecute,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Execute bKash payment after user completes payment.

    - Call this after user returns from bKash payment page
    - Updates payment status to 'paid' or 'failed'
    - Stores transaction ID from bKash
    - Returns updated payment record
    """
    # Note: In production, you'd extract payment_id from callback params
    # For now, we'll need both payment_id and bkash_payment_id
    # This is a simplified implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Execute endpoint needs payment_id mapping - implement callback handler",
    )


@router.post("/bkash/query", response_model=BkashPaymentResponse)
async def query_bkash_payment(
    data: BkashPaymentQuery,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Query bKash payment status.

    - Check status of a bKash payment
    - Useful for verifying payment completion
    - Returns: payment status, transaction ID, amount, etc.
    """
    return await service.query_bkash_payment(data.payment_id)


# ===== Invoice Endpoints =====


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create an invoice for a payment.

    - Generates unique invoice number (INV-YYYYMM-NNNN)
    - Links invoice to payment
    - Initial status: 'draft'
    """
    return await service.create_invoice(data, created_by=current_user.user_id)


@router.get("/invoices", response_model=list[InvoiceListItem])
async def list_invoices(
    service: Annotated[PaymentService, Depends(get_payment_service)],
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List invoices with filters.

    - Filter by status (draft, sent, paid, overdue, cancelled)
    - Supports pagination
    - Ordered by creation date (newest first)
    """
    return await service.list_invoices(status=status, limit=limit, offset=offset)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Get invoice by ID.

    - Returns full invoice details
    - Tenant filtering applied automatically
    """
    return await service.get_invoice(invoice_id)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    data: InvoiceUpdate,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update invoice.

    - Can update status and due date
    - Maintains audit trail
    """
    return await service.update_invoice(invoice_id, data, updated_by=current_user.user_id)


@router.post("/invoices/{invoice_id}/generate-pdf", response_model=dict)
async def generate_invoice_pdf(
    invoice_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Generate PDF for invoice.

    - Creates PDF from invoice data
    - Stores PDF URL in invoice record
    - Returns: { pdf_url: string }

    TODO: Implement actual PDF generation
    """
    pdf_url = await service.generate_invoice_pdf(invoice_id)
    return {"pdf_url": pdf_url}
