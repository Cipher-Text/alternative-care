"""Unit tests for payment service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.modules.payment.service import PaymentService
from app.shared.models import Payment, Invoice
from app.shared.schemas import (
    PaymentCreate,
    PaymentUpdate,
    BkashPaymentCreate,
    InvoiceCreate,
    InvoiceUpdate,
)


@pytest.fixture
async def test_tenant_data(db_session):
    """Create test tenant."""
    from app.shared.models import Tenant

    tenant = Tenant(
        id=str(uuid4()),
        name="Test Clinic",
        email="test@clinic.com",
        clinic_name="Test Clinic",
        specializations=["homeopathy"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db_session, test_tenant_data):
    """Create test user."""
    from app.shared.models import User

    user = User(
        id=str(uuid4()),
        tenant_id=test_tenant_data.id,
        email="user@test.com",
        password_hash="$2b$12$test_hash",
        role="doctor",
        full_name="Dr. Test",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_patient(db_session, test_tenant_data, test_user):
    """Create test patient."""
    from app.shared.models import Patient

    patient = Patient(
        id=str(uuid4()),
        tenant_id=test_tenant_data.id,
        full_name="Test Patient",
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
def tenant_id(test_tenant_data):
    """Test tenant ID."""
    return test_tenant_data.id


@pytest.fixture
def user_id(test_user):
    """Test user ID."""
    return test_user.id


@pytest.fixture
def payment_service(db_session, tenant_id):
    """Create payment service instance."""
    return PaymentService(db=db_session, tenant_id=tenant_id)


# ===== Manual Payment Tests =====


@pytest.mark.asyncio
async def test_create_cash_payment(payment_service, test_patient, user_id):
    """Test creating a cash payment."""
    data = PaymentCreate(
        patient_id=test_patient.id,
        amount=500.00,
        payment_method="cash",
        description="Consultation fee",
        payment_date=date.today(),
    )

    payment = await payment_service.create_payment(data, received_by=user_id)

    assert payment.id is not None
    assert payment.patient_id == test_patient.id
    assert payment.amount == 500.00
    assert payment.payment_method == "cash"
    assert payment.status == "paid"
    assert payment.currency == "BDT"
    assert payment.received_by == user_id


@pytest.mark.asyncio
async def test_create_payment_with_visit(payment_service, test_patient, user_id):
    """Test creating payment linked to a visit."""
    visit_id = str(uuid4())

    data = PaymentCreate(
        patient_id=test_patient.id,
        visit_id=visit_id,
        amount=1000.00,
        payment_method="cash",
    )

    payment = await payment_service.create_payment(data, received_by=user_id)

    assert payment.visit_id == visit_id


@pytest.mark.asyncio
async def test_get_payment(payment_service, test_patient, user_id):
    """Test getting payment by ID."""
    data = PaymentCreate(
        patient_id=test_patient.id,
        amount=500.00,
        payment_method="cash",
    )
    created = await payment_service.create_payment(data, received_by=user_id)

    payment = await payment_service.get_payment(created.id)

    assert payment.id == created.id
    assert payment.amount == 500.00


@pytest.mark.asyncio
async def test_get_payment_not_found(payment_service):
    """Test getting non-existent payment raises 404."""
    with pytest.raises(HTTPException) as exc:
        await payment_service.get_payment(str(uuid4()))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_payments_empty(payment_service):
    """Test listing payments when none exist."""
    payments = await payment_service.list_payments()
    assert len(payments) == 0


@pytest.mark.asyncio
async def test_list_payments_by_patient(payment_service, test_patient, user_id, db_session):
    """Test listing payments filtered by patient."""
    from app.shared.models import Patient

    # Create another patient
    other_patient = Patient(
        id=str(uuid4()),
        tenant_id=payment_service.tenant_id,
        full_name="Other Patient",
        is_active=True,
        created_by=user_id,
    )
    db_session.add(other_patient)
    await db_session.commit()

    # Create payments for both patients
    for patient in [test_patient, other_patient]:
        data = PaymentCreate(
            patient_id=patient.id,
            amount=500.00,
            payment_method="cash",
        )
        await payment_service.create_payment(data, received_by=user_id)

    # List payments for test_patient only
    payments = await payment_service.list_payments(patient_id=test_patient.id)

    assert len(payments) == 1
    assert payments[0].patient_id == test_patient.id


@pytest.mark.asyncio
async def test_list_payments_by_method(payment_service, test_patient, user_id):
    """Test listing payments filtered by payment method."""
    # Create cash and bkash payments
    for method in ["cash", "cash", "bkash"]:
        data = PaymentCreate(
            patient_id=test_patient.id,
            amount=500.00,
            payment_method=method,
        )
        payment = await payment_service.create_payment(data, received_by=user_id)

        # Mark bkash as pending (override default 'paid')
        if method == "bkash":
            payment.status = "pending"
            await payment_service.db.commit()

    # List only cash payments
    payments = await payment_service.list_payments(payment_method="cash")

    assert len(payments) == 2
    assert all(p.payment_method == "cash" for p in payments)


@pytest.mark.asyncio
async def test_list_payments_by_date_range(payment_service, test_patient, user_id):
    """Test listing payments with date filter."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Create payment yesterday
    data1 = PaymentCreate(
        patient_id=test_patient.id,
        amount=500.00,
        payment_method="cash",
        payment_date=yesterday,
    )
    await payment_service.create_payment(data1, received_by=user_id)

    # Create payment today
    data2 = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
        payment_date=today,
    )
    await payment_service.create_payment(data2, received_by=user_id)

    # List only today's payments
    payments = await payment_service.list_payments(date_from=today, date_to=today)

    assert len(payments) == 1
    assert payments[0].payment_date == today


@pytest.mark.asyncio
async def test_get_payment_summary(payment_service, test_patient, user_id):
    """Test payment summary statistics."""
    # Create various payments
    payments_data = [
        {"amount": 500.00, "method": "cash", "status": "paid"},
        {"amount": 1000.00, "method": "cash", "status": "paid"},
        {"amount": 2000.00, "method": "bkash", "status": "pending"},
        {"amount": 1500.00, "method": "bkash", "status": "paid"},
    ]

    for p_data in payments_data:
        data = PaymentCreate(
            patient_id=test_patient.id,
            amount=p_data["amount"],
            payment_method=p_data["method"],
        )
        payment = await payment_service.create_payment(data, received_by=user_id)

        # Update status if needed
        if p_data["status"] != "paid":
            payment.status = p_data["status"]
            await payment_service.db.commit()

    summary = await payment_service.get_payment_summary()

    assert summary["total_payments"] == 4
    assert summary["total_amount"] == 5000.00
    assert summary["paid_amount"] == 3000.00  # 500 + 1000 + 1500
    assert summary["pending_amount"] == 2000.00
    assert summary["cash_amount"] == 1500.00  # 500 + 1000
    assert summary["bkash_amount"] == 1500.00  # Only paid bkash


# ===== bKash Payment Tests (Mocked) =====


@pytest.mark.asyncio
async def test_create_bkash_payment(payment_service, test_patient, user_id):
    """Test creating bKash payment."""
    data = BkashPaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        description="Consultation",
    )

    # Mock bKash service
    with patch('app.modules.payment.service.bkash_service.create_payment') as mock_create:
        mock_create.return_value = {
            "paymentID": "TR123456",
            "bkashURL": "https://sandbox.bka.sh/payment/TR123456",
            "amount": "1000.00",
            "merchantInvoiceNumber": "INV-202604-0001",
        }

        result = await payment_service.create_bkash_payment(data, created_by=user_id)

        assert result["payment_id"] is not None
        assert result["bkash_payment_id"] == "TR123456"
        assert result["bkash_url"] is not None
        assert "sandbox.bka.sh" in result["bkash_url"]


@pytest.mark.asyncio
async def test_query_bkash_payment(payment_service):
    """Test querying bKash payment status."""
    with patch('app.modules.payment.service.bkash_service.query_payment') as mock_query:
        mock_query.return_value = {
            "paymentID": "TR123456",
            "trxID": "8AG1234567",
            "transactionStatus": "Completed",
            "amount": "1000.00",
        }

        result = await payment_service.query_bkash_payment("TR123456")

        assert result["paymentID"] == "TR123456"
        assert result["transactionStatus"] == "Completed"


# ===== Invoice Tests =====


@pytest.mark.asyncio
async def test_create_invoice(payment_service, test_patient, user_id):
    """Test creating an invoice."""
    # First create a payment
    payment_data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(payment_data, received_by=user_id)

    # Create invoice
    invoice_data = InvoiceCreate(payment_id=payment.id)
    invoice = await payment_service.create_invoice(invoice_data, created_by=user_id)

    assert invoice.id is not None
    assert invoice.payment_id == payment.id
    assert invoice.invoice_number.startswith("INV-")
    assert invoice.status == "draft"


@pytest.mark.asyncio
async def test_generate_invoice_number(payment_service, test_patient, user_id):
    """Test invoice number generation."""
    # Create payment
    payment_data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(payment_data, received_by=user_id)

    # Create first invoice
    invoice1_data = InvoiceCreate(payment_id=payment.id)
    invoice1 = await payment_service.create_invoice(invoice1_data, created_by=user_id)

    # Create another payment
    payment2 = await payment_service.create_payment(payment_data, received_by=user_id)

    # Create second invoice
    invoice2_data = InvoiceCreate(payment_id=payment2.id)
    invoice2 = await payment_service.create_invoice(invoice2_data, created_by=user_id)

    # Check invoice numbers are sequential
    assert invoice1.invoice_number.startswith("INV-")
    assert invoice2.invoice_number.startswith("INV-")

    # Extract numbers and verify sequence
    num1 = int(invoice1.invoice_number.split("-")[-1])
    num2 = int(invoice2.invoice_number.split("-")[-1])
    assert num2 == num1 + 1


@pytest.mark.asyncio
async def test_get_invoice(payment_service, test_patient, user_id):
    """Test getting invoice by ID."""
    # Create payment and invoice
    payment_data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(payment_data, received_by=user_id)

    invoice_data = InvoiceCreate(payment_id=payment.id)
    created = await payment_service.create_invoice(invoice_data, created_by=user_id)

    # Get invoice
    invoice = await payment_service.get_invoice(created.id)

    assert invoice.id == created.id
    assert invoice.payment_id == payment.id


@pytest.mark.asyncio
async def test_get_invoice_not_found(payment_service):
    """Test getting non-existent invoice raises 404."""
    with pytest.raises(HTTPException) as exc:
        await payment_service.get_invoice(str(uuid4()))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_invoices(payment_service, test_patient, user_id):
    """Test listing invoices."""
    # Create payments and invoices
    for i in range(3):
        payment_data = PaymentCreate(
            patient_id=test_patient.id,
            amount=1000.00,
            payment_method="cash",
        )
        payment = await payment_service.create_payment(payment_data, received_by=user_id)

        invoice_data = InvoiceCreate(payment_id=payment.id)
        await payment_service.create_invoice(invoice_data, created_by=user_id)

    invoices = await payment_service.list_invoices()

    assert len(invoices) == 3


@pytest.mark.asyncio
async def test_update_invoice(payment_service, test_patient, user_id):
    """Test updating invoice."""
    # Create payment and invoice
    payment_data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(payment_data, received_by=user_id)

    invoice_data = InvoiceCreate(payment_id=payment.id)
    invoice = await payment_service.create_invoice(invoice_data, created_by=user_id)

    # Update invoice
    update_data = InvoiceUpdate(status="sent")
    updated = await payment_service.update_invoice(invoice.id, update_data, updated_by=user_id)

    assert updated.status == "sent"
    assert updated.updated_by == user_id


@pytest.mark.asyncio
async def test_generate_invoice_pdf(payment_service, test_patient, user_id):
    """Test invoice PDF generation (placeholder)."""
    # Create payment and invoice
    payment_data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(payment_data, received_by=user_id)

    invoice_data = InvoiceCreate(payment_id=payment.id)
    invoice = await payment_service.create_invoice(invoice_data, created_by=user_id)

    # Generate PDF
    pdf_url = await payment_service.generate_invoice_pdf(invoice.id)

    assert pdf_url is not None
    assert "invoice" in pdf_url.lower()


# ===== Refund Tests =====


@pytest.mark.asyncio
async def test_refund_cash_payment(payment_service, test_patient, user_id):
    """Test refunding a cash payment."""
    # Create paid payment
    data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(data, received_by=user_id)

    # Refund payment
    refunded = await payment_service.refund_payment(
        payment.id,
        amount=1000.00,
        reason="Patient requested refund",
        refunded_by=user_id,
    )

    assert refunded.status == "refunded"


@pytest.mark.asyncio
async def test_refund_unpaid_payment_fails(payment_service, test_patient, user_id):
    """Test that refunding unpaid payment fails."""
    # Create pending payment
    data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(data, received_by=user_id)
    payment.status = "pending"
    await payment_service.db.commit()

    # Try to refund
    with pytest.raises(HTTPException) as exc:
        await payment_service.refund_payment(
            payment.id,
            amount=1000.00,
            reason="Test",
            refunded_by=user_id,
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_refund_amount_exceeds_payment_fails(payment_service, test_patient, user_id):
    """Test that refund amount cannot exceed payment amount."""
    # Create payment
    data = PaymentCreate(
        patient_id=test_patient.id,
        amount=1000.00,
        payment_method="cash",
    )
    payment = await payment_service.create_payment(data, received_by=user_id)

    # Try to refund more than paid
    with pytest.raises(HTTPException) as exc:
        await payment_service.refund_payment(
            payment.id,
            amount=1500.00,
            reason="Test",
            refunded_by=user_id,
        )
    assert exc.value.status_code == 400
