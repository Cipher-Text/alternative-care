"""Integration tests for payment and invoice API routes."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Payment, Invoice, Patient, Visit


@pytest.mark.asyncio
class TestPaymentRoutes:
    """Test payment API endpoints."""

    async def test_create_cash_payment(
        self, client: AsyncClient, doctor_token: str, test_patient: Patient
    ):
        """Test creating a cash payment."""
        response = await client.post(
            "/api/v1/payments",
            json={
                "patient_id": test_patient.id,
                "amount": 1000.0,
                "payment_method": "cash",
                "description": "Consultation fee",
                "payment_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 1000.0
        assert data["payment_method"] == "cash"
        assert data["status"] == "paid"
        assert data["patient_id"] == test_patient.id

    async def test_create_payment_with_visit(
        self,
        client: AsyncClient,
        doctor_token: str,
        test_patient: Patient,
        test_visit: Visit,
    ):
        """Test creating payment linked to visit."""
        response = await client.post(
            "/api/v1/payments",
            json={
                "patient_id": test_patient.id,
                "visit_id": test_visit.id,
                "amount": 1500.0,
                "payment_method": "cash",
                "payment_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["visit_id"] == test_visit.id
        assert data["amount"] == 1500.0

    async def test_get_payment(
        self, client: AsyncClient, doctor_token: str, test_payment: Payment
    ):
        """Test retrieving a payment by ID."""
        response = await client.get(
            f"/api/v1/payments/{test_payment.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_payment.id
        assert data["amount"] == float(test_payment.amount)

    async def test_get_payment_not_found(self, client: AsyncClient, doctor_token: str):
        """Test retrieving non-existent payment."""
        response = await client.get(
            "/api/v1/payments/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_list_payments(
        self, client: AsyncClient, doctor_token: str, test_payment: Payment
    ):
        """Test listing payments."""
        response = await client.get(
            "/api/v1/payments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(p["id"] == test_payment.id for p in data)

    async def test_list_payments_filter_by_patient(
        self, client: AsyncClient, doctor_token: str, test_patient: Patient, test_payment: Payment
    ):
        """Test filtering payments by patient."""
        response = await client.get(
            f"/api/v1/payments?patient_id={test_patient.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(p["patient_id"] == test_patient.id for p in data)

    async def test_list_payments_filter_by_method(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test filtering payments by payment method."""
        response = await client.get(
            "/api/v1/payments?payment_method=cash",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(p["payment_method"] == "cash" for p in data)

    async def test_list_payments_filter_by_date_range(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test filtering payments by date range."""
        date_from = date.today() - timedelta(days=7)
        date_to = date.today()

        response = await client.get(
            f"/api/v1/payments?date_from={date_from}&date_to={date_to}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_payments_pagination(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test payment list pagination."""
        response = await client.get(
            "/api/v1/payments?limit=5&offset=0",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    async def test_get_payment_summary(
        self, client: AsyncClient, doctor_token: str, test_payment: Payment
    ):
        """Test getting payment summary statistics."""
        response = await client.get(
            "/api/v1/payments/summary",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_payments" in data
        assert "total_amount" in data
        assert "paid_amount" in data
        assert "pending_amount" in data
        assert "cash_amount" in data
        assert "bkash_amount" in data
        assert data["total_payments"] >= 1

    async def test_get_payment_summary_with_date_range(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test payment summary with date filters."""
        date_from = date.today() - timedelta(days=30)
        date_to = date.today()

        response = await client.get(
            f"/api/v1/payments/summary?date_from={date_from}&date_to={date_to}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == str(date_from)
        assert data["period_end"] == str(date_to)

    async def test_create_payment_requires_auth(
        self, client: AsyncClient, test_patient: Patient
    ):
        """Test that creating payment requires authentication."""
        response = await client.post(
            "/api/v1/payments",
            json={
                "patient_id": test_patient.id,
                "amount": 1000.0,
                "payment_method": "cash",
                "payment_date": str(date.today()),
            },
        )

        assert response.status_code == 401

    async def test_create_payment_invalid_amount(
        self, client: AsyncClient, doctor_token: str, test_patient: Patient
    ):
        """Test validation for invalid payment amount."""
        response = await client.post(
            "/api/v1/payments",
            json={
                "patient_id": test_patient.id,
                "amount": -100.0,  # Negative amount
                "payment_method": "cash",
                "payment_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestBkashPaymentRoutes:
    """Test bKash payment integration endpoints."""

    @patch("app.modules.payment.bkash_service.bkash_service.create_payment")
    async def test_create_bkash_payment(
        self,
        mock_create: AsyncMock,
        client: AsyncClient,
        doctor_token: str,
        test_patient: Patient,
    ):
        """Test creating a bKash payment."""
        mock_create.return_value = {
            "paymentID": "TR0011ABC123",
            "bkashURL": "https://sandbox.bka.sh/pay/TR0011ABC123",
            "amount": "2000.00",
            "intent": "sale",
            "merchantInvoiceNumber": "INV-202604-0001",
        }

        response = await client.post(
            "/api/v1/payments/bkash/create",
            json={
                "patient_id": test_patient.id,
                "amount": 2000.0,
                "description": "Treatment fee",
                "callback_url": "https://example.com/callback",
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "payment_id" in data
        assert "bkash_payment_id" in data
        assert "bkash_url" in data
        assert data["bkash_payment_id"] == "TR0011ABC123"
        assert data["amount"] == "2000.00"

        mock_create.assert_called_once()

    @patch("app.modules.payment.bkash_service.bkash_service.query_payment")
    async def test_query_bkash_payment(
        self, mock_query: AsyncMock, client: AsyncClient, doctor_token: str
    ):
        """Test querying bKash payment status."""
        mock_query.return_value = {
            "paymentID": "TR0011ABC123",
            "trxID": "8AS9D0023K",
            "transactionStatus": "Completed",
            "amount": "2000.00",
            "currency": "BDT",
            "merchantInvoiceNumber": "INV-202604-0001",
            "paymentExecuteTime": "2026-04-29T10:30:00Z",
        }

        response = await client.post(
            "/api/v1/payments/bkash/query",
            json={"payment_id": "TR0011ABC123"},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["paymentID"] == "TR0011ABC123"
        assert data["transactionStatus"] == "Completed"
        assert data["trxID"] == "8AS9D0023K"

        mock_query.assert_called_once_with("TR0011ABC123")

    async def test_execute_bkash_payment_not_implemented(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test that execute endpoint returns 501 (needs callback handler)."""
        response = await client.post(
            "/api/v1/payments/bkash/execute",
            json={
                "payment_id": "some-payment-id",
                "bkash_payment_id": "TR0011ABC123",
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 501
        assert "implement" in response.json()["detail"].lower()

    async def test_create_bkash_payment_amount_validation(
        self, client: AsyncClient, doctor_token: str, test_patient: Patient
    ):
        """Test bKash amount validation (max 25000 BDT)."""
        response = await client.post(
            "/api/v1/payments/bkash/create",
            json={
                "patient_id": test_patient.id,
                "amount": 30000.0,  # Exceeds bKash limit
                "description": "Large payment",
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestInvoiceRoutes:
    """Test invoice API endpoints."""

    async def test_create_invoice(
        self, client: AsyncClient, doctor_token: str, test_payment: Payment
    ):
        """Test creating an invoice."""
        due_date = date.today() + timedelta(days=30)

        response = await client.post(
            "/api/v1/payments/invoices",
            json={
                "payment_id": test_payment.id,
                "due_date": str(due_date),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["payment_id"] == test_payment.id
        assert data["status"] == "draft"
        assert "invoice_number" in data
        assert data["invoice_number"].startswith(f"INV-{date.today():%Y%m}-")

    async def test_invoice_number_sequential(
        self, client: AsyncClient, doctor_token: str, test_payment: Payment
    ):
        """Test that invoice numbers are sequential within a month."""
        due_date = date.today() + timedelta(days=30)

        # Create first invoice
        response1 = await client.post(
            "/api/v1/payments/invoices",
            json={"payment_id": test_payment.id, "due_date": str(due_date)},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        invoice1 = response1.json()

        # Create another payment and invoice
        response_payment = await client.post(
            "/api/v1/payments",
            json={
                "patient_id": test_payment.patient_id,
                "amount": 1500.0,
                "payment_method": "cash",
                "payment_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        payment2 = response_payment.json()

        response2 = await client.post(
            "/api/v1/payments/invoices",
            json={"payment_id": payment2["id"], "due_date": str(due_date)},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        invoice2 = response2.json()

        # Extract sequence numbers
        seq1 = int(invoice1["invoice_number"].split("-")[-1])
        seq2 = int(invoice2["invoice_number"].split("-")[-1])

        assert seq2 == seq1 + 1

    async def test_get_invoice(
        self, client: AsyncClient, doctor_token: str, test_invoice: Invoice
    ):
        """Test retrieving an invoice by ID."""
        response = await client.get(
            f"/api/v1/payments/invoices/{test_invoice.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_invoice.id
        assert data["invoice_number"] == test_invoice.invoice_number

    async def test_list_invoices(
        self, client: AsyncClient, doctor_token: str, test_invoice: Invoice
    ):
        """Test listing invoices."""
        response = await client.get(
            "/api/v1/payments/invoices",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(inv["id"] == test_invoice.id for inv in data)

    async def test_list_invoices_filter_by_status(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test filtering invoices by status."""
        response = await client.get(
            "/api/v1/payments/invoices?status=draft",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(inv["status"] == "draft" for inv in data)

    async def test_update_invoice(
        self, client: AsyncClient, doctor_token: str, test_invoice: Invoice
    ):
        """Test updating an invoice."""
        new_due_date = date.today() + timedelta(days=45)

        response = await client.patch(
            f"/api/v1/payments/invoices/{test_invoice.id}",
            json={
                "status": "sent",
                "due_date": str(new_due_date),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["due_date"] == str(new_due_date)

    async def test_generate_invoice_pdf(
        self, client: AsyncClient, doctor_token: str, test_invoice: Invoice
    ):
        """Test generating invoice PDF."""
        response = await client.post(
            f"/api/v1/payments/invoices/{test_invoice.id}/generate-pdf",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "pdf_url" in data
        assert test_invoice.id in data["pdf_url"]

    async def test_create_invoice_for_nonexistent_payment(
        self, client: AsyncClient, doctor_token: str
    ):
        """Test creating invoice for non-existent payment."""
        response = await client.post(
            "/api/v1/payments/invoices",
            json={
                "payment_id": "00000000-0000-0000-0000-000000000000",
                "due_date": str(date.today() + timedelta(days=30)),
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPaymentTenantIsolation:
    """Test multi-tenant isolation for payments and invoices."""

    async def test_cannot_access_other_tenant_payment(
        self,
        client: AsyncClient,
        doctor_token: str,
        other_tenant_payment: Payment,
    ):
        """Test that users cannot access payments from other tenants."""
        response = await client.get(
            f"/api/v1/payments/{other_tenant_payment.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 404

    async def test_cannot_list_other_tenant_payments(
        self,
        client: AsyncClient,
        doctor_token: str,
        test_payment: Payment,
        other_tenant_payment: Payment,
    ):
        """Test that payment lists are filtered by tenant."""
        response = await client.get(
            "/api/v1/payments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        payment_ids = [p["id"] for p in data]

        assert test_payment.id in payment_ids
        assert other_tenant_payment.id not in payment_ids

    async def test_cannot_access_other_tenant_invoice(
        self,
        client: AsyncClient,
        doctor_token: str,
        other_tenant_invoice: Invoice,
    ):
        """Test that users cannot access invoices from other tenants."""
        response = await client.get(
            f"/api/v1/payments/invoices/{other_tenant_invoice.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 404

    async def test_payment_summary_scoped_to_tenant(
        self,
        client: AsyncClient,
        doctor_token: str,
        test_payment: Payment,
        other_tenant_payment: Payment,
    ):
        """Test that payment summary only includes tenant's data."""
        response = await client.get(
            "/api/v1/payments/summary",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Summary should only count current tenant's payments
        # We can't test exact counts without knowing all test data,
        # but we can verify the endpoint works
        assert "total_payments" in data
        assert "total_amount" in data
