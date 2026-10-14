"""Payment and invoice API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, module_guard, require_permission
from app.modules.payment.service import PaymentService
from app.shared.schemas import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentListItem,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListItem,
    PaymentSummary,
)

router = APIRouter(
    dependencies=[
        Depends(
            module_guard(read=("payments.read", "invoices.read"), write=("payments.write", "invoices.write"))
        )
    ]
)


def get_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PaymentService:
    """Dependency for payment service with tenant context."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform users cannot manage payment records. Use a tenant account.",
        )
    return PaymentService(db=db, tenant_id=current_user.tenant_id)


# ===== Payment Endpoints =====


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("payments.write"))])
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


@router.get("", response_model=list[PaymentListItem], dependencies=[Depends(require_permission("payments.read"))])
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
    return await service.payment_list_views(
        await service.list_payments(
            patient_id=patient_id,
            visit_id=visit_id,
            payment_method=payment_method,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/summary", response_model=PaymentSummary, dependencies=[Depends(require_permission("payments.read"))])
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


# ===== Invoice Endpoints =====
# NOTE: registered before GET /{payment_id} — both /invoices and
# /{payment_id} are single-segment path templates, and Starlette matches
# routes in registration order, so /invoices would otherwise be shadowed
# (every GET /invoices request would try to look up a payment literally
# named "invoices" and 404).


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("invoices.write"))])
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
    return await service.invoice_view(
        await service.create_invoice(data, created_by=current_user.user_id)
    )


@router.get("/invoices", response_model=list[InvoiceListItem], dependencies=[Depends(require_permission("invoices.read"))])
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
    return await service.invoice_views(
        await service.list_invoices(status=status, limit=limit, offset=offset)
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, dependencies=[Depends(require_permission("invoices.read"))])
async def get_invoice(
    invoice_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Get invoice by ID.

    - Returns full invoice details
    - Tenant filtering applied automatically
    """
    return await service.invoice_view(await service.get_invoice(invoice_id))


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse, dependencies=[Depends(require_permission("invoices.write"))])
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
    return await service.invoice_view(
        await service.update_invoice(invoice_id, data, updated_by=current_user.user_id)
    )


@router.get(
    "/invoices/{invoice_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
    dependencies=[Depends(require_permission("invoices.read"))],
)
async def get_invoice_pdf(
    invoice_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    Download the printable invoice as a PDF.

    - Rendered on demand with bilingual labels
    - Read-only: needs the invoices.read permission
    """
    pdf, filename = await service.build_invoice_pdf(invoice_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/{payment_id}", response_model=PaymentResponse, dependencies=[Depends(require_permission("payments.read"))])
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
