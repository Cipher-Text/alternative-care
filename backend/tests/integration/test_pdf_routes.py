"""GET /prescriptions/{id}/pdf and /payments/invoices/{id}/pdf — real documents, real access rules."""

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.shared.models import Invoice, Payment, Prescription, PrescriptionItem, UsageTracking

pytestmark = pytest.mark.requires_pdf


async def _prescription(db, tenant_id, patient_id, status="issued"):
    rx = Prescription(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        patient_id=patient_id,
        prescribed_by=str(uuid.uuid4()),
        diagnosis="Acute fever",
        advice="বিশ্রাম নিন এবং প্রচুর পানি পান করুন।",
        status=status,
    )
    db.add(rx)
    await db.flush()
    db.add(
        PrescriptionItem(
            prescription_id=rx.id,
            tenant_id=tenant_id,
            medicine_name="Belladonna 30C",
            dosage="5 drops",
            frequency="3 times daily",
        )
    )
    await db.commit()
    return rx


@pytest.mark.asyncio
class TestPrescriptionPdf:
    async def test_issued_prescription_downloads_as_a_real_pdf(
        self, authenticated_client, db_session, test_tenant, test_patient
    ):
        rx = await _prescription(db_session, test_tenant.id, test_patient.id)

        response = await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert f"prescription-{rx.id[:8]}.pdf" in response.headers["content-disposition"]
        assert response.headers["cache-control"] == "private, no-store"
        assert response.content.startswith(b"%PDF") and len(response.content) > 2000

    async def test_voided_prescription_can_still_be_printed(
        self, authenticated_client, db_session, test_tenant, test_patient
    ):
        rx = await _prescription(db_session, test_tenant.id, test_patient.id, status="voided")
        response = await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")
        assert response.status_code == 200

    async def test_draft_is_rejected(
        self, authenticated_client, db_session, test_tenant, test_patient
    ):
        rx = await _prescription(db_session, test_tenant.id, test_patient.id, status="draft")
        response = await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")
        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()

    async def test_another_tenants_prescription_is_404(
        self, authenticated_client, db_session, test_tenant_2, test_patient_2
    ):
        rx = await _prescription(db_session, test_tenant_2.id, test_patient_2.id)
        response = await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")
        assert response.status_code == 404

    async def test_unauthenticated_is_rejected(self, client, db_session, test_tenant, test_patient):
        rx = await _prescription(db_session, test_tenant.id, test_patient.id)
        client.headers.pop("Authorization", None)
        assert (await client.get(f"/api/v1/prescriptions/{rx.id}/pdf")).status_code in (401, 403)

    async def test_each_download_is_counted_in_usage(
        self, authenticated_client, db_session, test_tenant, test_patient
    ):
        rx = await _prescription(db_session, test_tenant.id, test_patient.id)
        await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")
        await authenticated_client.get(f"/api/v1/prescriptions/{rx.id}/pdf")

        rows = (
            await db_session.execute(
                select(UsageTracking).where(UsageTracking.tenant_id == test_tenant.id)
            )
        ).scalars().all()
        assert sum(r.pdfs_generated for r in rows) == 2


@pytest.mark.asyncio
class TestInvoicePdf:
    async def _invoice(self, db, tenant_id, patient_id):
        payment = Payment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            amount=1500,
            currency="BDT",
            payment_method="cash",
            status="paid",
            description="Consultation",
            payment_date=date.today(),
            received_by=str(uuid.uuid4()),
        )
        db.add(payment)
        await db.flush()
        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            payment_id=payment.id,
            invoice_number="INV-TEST-0001",
            status="sent",
        )
        db.add(invoice)
        await db.commit()
        return invoice

    async def test_invoice_downloads_as_a_real_pdf(
        self, authenticated_client, db_session, test_tenant, test_patient
    ):
        invoice = await self._invoice(db_session, test_tenant.id, test_patient.id)
        response = await authenticated_client.get(f"/api/v1/payments/invoices/{invoice.id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "invoice-INV-TEST-0001.pdf" in response.headers["content-disposition"]
        assert response.content.startswith(b"%PDF")

    async def test_another_tenants_invoice_is_404(
        self, authenticated_client, db_session, test_tenant_2, test_patient_2
    ):
        invoice = await self._invoice(db_session, test_tenant_2.id, test_patient_2.id)
        response = await authenticated_client.get(f"/api/v1/payments/invoices/{invoice.id}/pdf")
        assert response.status_code == 404
