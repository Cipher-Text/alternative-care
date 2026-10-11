"""Payment and invoice service layer."""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entitlements import EntitlementService
from app.core.pdf import render_pdf
from app.core.usage_tracking import UsageService
from app.modules.payment.pdf import build_invoice_html
from app.shared.models import Invoice, Patient, Payment, Tenant
from app.shared.schemas import (
    PaymentCreate,
    PaymentUpdate,
    BkashPaymentCreate,
    InvoiceCreate,
    InvoiceUpdate,
)
from app.modules.payment.bkash_service import bkash_service


class PaymentService:
    """Service for managing payments and invoices."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    # ===== Payment Methods =====

    async def create_payment(
        self, data: PaymentCreate, received_by: str
    ) -> Payment:
        """
        Create a manual payment (cash or other).

        Args:
            data: Payment creation data
            received_by: User ID receiving the payment

        Returns:
            Created payment record
        """
        payment = Payment(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            amount=data.amount,
            currency="BDT",
            payment_method=data.payment_method,
            status="paid",  # Manual payments are immediately paid
            description=data.description,
            payment_date=data.payment_date,
            received_by=received_by,
            created_by=received_by,
            updated_by=received_by,
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def create_bkash_payment(
        self, data: BkashPaymentCreate, created_by: str
    ) -> dict:
        """
        Create a bKash payment and get payment URL.

        Args:
            data: bKash payment creation data
            created_by: User ID creating the payment

        Returns:
            dict with payment_id, bkash_url, and merchant_invoice_number

        Raises:
            HTTPException: If bKash API fails
        """
        # Generate unique invoice number
        invoice_number = await self._generate_invoice_number()

        # Create payment in bKash
        bkash_response = await bkash_service.create_payment(
            amount=data.amount,
            invoice_number=invoice_number,
            callback_url=data.callback_url,
        )

        # Create pending payment record
        payment = Payment(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            amount=data.amount,
            currency="BDT",
            payment_method="bkash",
            status="pending",
            description=data.description,
            payment_date=date.today(),
            received_by=created_by,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        return {
            "payment_id": payment.id,
            "bkash_payment_id": bkash_response["paymentID"],
            "bkash_url": bkash_response["bkashURL"],
            "merchant_invoice_number": invoice_number,
            "amount": bkash_response["amount"],
        }

    async def execute_bkash_payment(
        self, payment_id: str, bkash_payment_id: str
    ) -> Payment:
        """
        Execute bKash payment after user completes payment.

        Args:
            payment_id: Internal payment ID
            bkash_payment_id: bKash payment ID

        Returns:
            Updated payment record

        Raises:
            HTTPException: If payment not found or execution fails
        """
        # Get payment
        payment = await self.get_payment(payment_id)

        if payment.payment_method != "bkash":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is not a bKash payment",
            )

        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment already {payment.status}",
            )

        # Execute payment in bKash
        bkash_response = await bkash_service.execute_payment(bkash_payment_id)

        # Update payment record
        payment.transaction_id = bkash_response["trxID"]
        payment.status = "paid" if bkash_response["transactionStatus"] == "Completed" else "failed"
        payment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def query_bkash_payment(self, bkash_payment_id: str) -> dict:
        """
        Query bKash payment status.

        Args:
            bkash_payment_id: bKash payment ID

        Returns:
            Payment status from bKash
        """
        return await bkash_service.query_payment(bkash_payment_id)

    async def refund_payment(
        self, payment_id: str, amount: float, reason: str, refunded_by: str
    ) -> Payment:
        """
        Refund a payment.

        Args:
            payment_id: Payment ID to refund
            amount: Refund amount
            reason: Refund reason
            refunded_by: User ID processing refund

        Returns:
            Updated payment record

        Raises:
            HTTPException: If payment not found or not refundable
        """
        payment = await self.get_payment(payment_id)

        if payment.status != "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only paid payments can be refunded",
            )

        if amount > payment.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed payment amount",
            )

        # Process bKash refund if applicable
        if payment.payment_method == "bkash" and payment.transaction_id:
            # Get bKash payment ID (stored in description or separate field)
            # For now, we'll need the bkash_payment_id passed separately
            # In production, store this in a separate field or integration_log
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="bKash refund requires bkash_payment_id - implement storage first",
            )

        # For cash payments, just mark as refunded
        payment.status = "refunded"
        payment.updated_by = refunded_by
        payment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def get_payment(self, payment_id: str) -> Payment:
        """Get payment by ID with tenant filtering."""
        result = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.id == payment_id,
                    Payment.tenant_id == self.tenant_id,
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    async def list_payments(
        self,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """
        List payments with filtering.

        Args:
            patient_id: Filter by patient
            visit_id: Filter by visit
            payment_method: Filter by method (cash, bkash)
            status: Filter by status
            date_from: Start date filter
            date_to: End date filter
            limit: Results limit
            offset: Results offset

        Returns:
            List of payments
        """
        query = select(Payment).where(Payment.tenant_id == self.tenant_id)

        # Apply filters
        if patient_id:
            query = query.where(Payment.patient_id == patient_id)
        if visit_id:
            query = query.where(Payment.visit_id == visit_id)
        if payment_method:
            query = query.where(Payment.payment_method == payment_method)
        if status:
            query = query.where(Payment.status == status)
        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        if date_to:
            query = query.where(Payment.payment_date <= date_to)

        # Order by payment date descending
        query = query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_payment_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """
        Get payment summary statistics.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Payment summary with totals
        """
        query = select(Payment).where(Payment.tenant_id == self.tenant_id)

        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        if date_to:
            query = query.where(Payment.payment_date <= date_to)

        result = await self.db.execute(query)
        payments = result.scalars().all()

        total_amount = sum(p.amount for p in payments)
        paid_amount = sum(p.amount for p in payments if p.status == "paid")
        pending_amount = sum(p.amount for p in payments if p.status == "pending")
        cash_amount = sum(p.amount for p in payments if p.payment_method == "cash" and p.status == "paid")
        bkash_amount = sum(p.amount for p in payments if p.payment_method == "bkash" and p.status == "paid")

        return {
            "total_payments": len(payments),
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "cash_amount": cash_amount,
            "bkash_amount": bkash_amount,
            "period_start": date_from,
            "period_end": date_to,
        }

    # ===== Invoice Methods =====

    async def create_invoice(
        self, data: InvoiceCreate, created_by: str
    ) -> Invoice:
        """
        Create an invoice for a payment.

        Args:
            data: Invoice creation data
            created_by: User ID creating invoice

        Returns:
            Created invoice

        Raises:
            HTTPException: If payment not found
        """
        await EntitlementService(self.db).check_feature(self.tenant_id, "feature_invoicing")

        # Verify payment exists and belongs to tenant
        payment = await self.get_payment(data.payment_id)

        # Generate invoice number
        invoice_number = await self._generate_invoice_number()

        invoice = Invoice(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            payment_id=data.payment_id,
            invoice_number=invoice_number,
            status="draft",
            due_date=data.due_date,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice

    async def _generate_invoice_number(self) -> str:
        """
        Generate unique invoice number for tenant.

        Format: INV-YYYYMM-NNNN
        Example: INV-202604-0001

        Returns:
            Invoice number string
        """
        today = date.today()
        prefix = f"INV-{today.year}{today.month:02d}"

        # Get count of invoices this month
        result = await self.db.execute(
            select(func.count(Invoice.id))
            .where(
                and_(
                    Invoice.tenant_id == self.tenant_id,
                    extract("year", Invoice.created_at) == today.year,
                    extract("month", Invoice.created_at) == today.month,
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    async def get_invoice(self, invoice_id: str) -> Invoice:
        """Get invoice by ID with tenant filtering."""
        result = await self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.id == invoice_id,
                    Invoice.tenant_id == self.tenant_id,
                )
            )
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        return invoice

    async def list_invoices(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Invoice]:
        """List invoices with filtering."""
        query = select(Invoice).where(Invoice.tenant_id == self.tenant_id)

        if status:
            query = query.where(Invoice.status == status)

        query = query.order_by(Invoice.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_invoice(
        self, invoice_id: str, data: InvoiceUpdate, updated_by: str
    ) -> Invoice:
        """Update invoice."""
        invoice = await self.get_invoice(invoice_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        invoice.updated_by = updated_by
        invoice.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice

    async def payment_list_views(self, payments: list[Payment]) -> list[dict]:
        """Payments plus the patient's name and phone, for list screens."""
        if not payments:
            return []
        patients = {
            p.id: p
            for p in (
                await self.db.execute(
                    select(Patient).where(
                        Patient.tenant_id == self.tenant_id,
                        Patient.id.in_({p.patient_id for p in payments}),
                    )
                )
            ).scalars()
        }
        return [
            {
                **{
                    c: getattr(p, c)
                    for c in (
                        "id", "patient_id", "amount", "currency", "payment_method", "status",
                        "payment_date", "description", "created_at",
                    )
                },
                "patient_name": patients[p.patient_id].full_name if p.patient_id in patients else None,
                "patient_phone": patients[p.patient_id].phone if p.patient_id in patients else None,
            }
            for p in payments
        ]

    async def invoice_views(self, invoices: list[Invoice]) -> list[dict]:
        """Invoices plus the fields a client shows, derived from each invoiced payment."""
        if not invoices:
            return []
        payments = {
            p.id: p
            for p in (
                await self.db.execute(
                    select(Payment).where(
                        Payment.tenant_id == self.tenant_id,
                        Payment.id.in_({i.payment_id for i in invoices}),
                    )
                )
            ).scalars()
        }
        patients = {
            p.id: p
            for p in (
                await self.db.execute(
                    select(Patient).where(
                        Patient.tenant_id == self.tenant_id,
                        Patient.id.in_({p.patient_id for p in payments.values()}),
                    )
                )
            ).scalars()
        }
        views = []
        for inv in invoices:
            payment = payments.get(inv.payment_id)
            patient = patients.get(payment.patient_id) if payment else None
            amount = float(payment.amount) if payment else 0.0
            views.append(
                {
                    **{
                        c: getattr(inv, c)
                        for c in (
                            "id", "tenant_id", "payment_id", "invoice_number", "pdf_url", "status",
                            "due_date", "created_at", "updated_at", "created_by", "updated_by",
                        )
                    },
                    "patient_id": payment.patient_id if payment else None,
                    "patient_name": patient.full_name if patient else None,
                    "patient_phone": getattr(patient, "phone", None) if patient else None,
                    "amount": amount,
                    "currency": payment.currency if payment else "BDT",
                    "issue_date": payment.payment_date if payment else None,
                    "items": (
                        [
                            {
                                "description": payment.description or "Consultation",
                                "quantity": 1,
                                "unit_price": amount,
                                "total": amount,
                            }
                        ]
                        if payment
                        else []
                    ),
                    "notes": None,
                }
            )
        return views

    async def invoice_view(self, invoice: Invoice) -> dict:
        return (await self.invoice_views([invoice]))[0]

    async def build_invoice_pdf(self, invoice_id: str) -> tuple[bytes, str]:
        """
        Render an invoice as a PDF document (on demand, not stored).

        Returns (pdf bytes, suggested filename).
        """
        invoice = await self.get_invoice(invoice_id)
        payment = await self.get_payment(invoice.payment_id)
        patient = (
            await self.db.execute(
                select(Patient).where(
                    Patient.id == payment.patient_id, Patient.tenant_id == self.tenant_id
                )
            )
        ).scalar_one()
        tenant = (
            await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))
        ).scalar_one()

        html = build_invoice_html(invoice=invoice, payment=payment, patient=patient, tenant=tenant)
        pdf = await render_pdf(html)

        await UsageService(self.db, self.tenant_id).increment("pdfs_generated")
        return pdf, f"invoice-{invoice.invoice_number}.pdf"
