"""Integration tests for dashboard API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDashboardRoutes:
    """Test dashboard API endpoints."""

    async def test_get_overview(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/overview endpoint."""
        response = await client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_patients" in data
        assert "total_revenue" in data
        assert "total_appointments" in data

    async def test_get_financial_analytics(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/financial endpoint."""
        response = await client.get(
            "/api/v1/dashboard/financial",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "revenue_by_method" in data
        assert "daily_revenue" in data

    async def test_get_patient_analytics(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/patients endpoint."""
        response = await client.get(
            "/api/v1/dashboard/patients",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_patients" in data
        assert "demographics" in data
        assert "age_distribution" in data

    async def test_get_appointment_analytics(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/appointments endpoint."""
        response = await client.get(
            "/api/v1/dashboard/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_appointments" in data
        assert "by_status" in data
        assert "by_type" in data

    async def test_get_visit_analytics(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/visits endpoint."""
        response = await client.get(
            "/api/v1/dashboard/visits",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_visits" in data
        assert "by_type" in data

    async def test_get_prescription_analytics(self, client: AsyncClient, doctor_token: str):
        """Test GET /dashboard/prescriptions endpoint."""
        response = await client.get(
            "/api/v1/dashboard/prescriptions",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_prescriptions" in data
        assert "by_status" in data

    async def test_dashboard_requires_auth(self, client: AsyncClient):
        """Test that dashboard endpoints require authentication."""
        response = await client.get("/api/v1/dashboard/overview")
        assert response.status_code == 401

    async def test_date_range_filtering(self, client: AsyncClient, doctor_token: str):
        """Test date range filtering on financial endpoint."""
        response = await client.get(
            "/api/v1/dashboard/financial?date_from=2026-04-01&date_to=2026-04-30",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == "2026-04-01"
        assert data["period_end"] == "2026-04-30"


@pytest.mark.asyncio
class TestOverdueInvoiceStats:
    """Regression: due_date is optional, and an unpaid invoice without one used to crash
    /dashboard/financial with `TypeError: '<' not supported between NoneType and date`."""

    async def _invoice(self, db_session, tenant, payment, due, status="sent", number="INV-DUE"):
        import uuid

        from app.shared.models import Invoice

        db_session.add(
            Invoice(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                payment_id=payment.id,
                invoice_number=number,
                status=status,
                due_date=due,
            )
        )
        await db_session.commit()

    async def test_unpaid_invoice_without_a_due_date_does_not_break_the_dashboard(
        self, client: AsyncClient, doctor_token: str, db_session, test_tenant, test_payment
    ):
        await self._invoice(db_session, test_tenant, test_payment, None)
        response = await client.get(
            "/api/v1/dashboard/financial", headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200, response.text

    async def test_overdue_invoices_are_still_counted(
        self, client: AsyncClient, doctor_token: str, db_session, test_tenant, test_payment
    ):
        from datetime import date, timedelta

        await self._invoice(db_session, test_tenant, test_payment, date.today() - timedelta(days=3), number="INV-LATE")
        await self._invoice(db_session, test_tenant, test_payment, None, number="INV-NODUE")
        await self._invoice(db_session, test_tenant, test_payment, date.today() + timedelta(days=3), number="INV-FUTURE")
        response = await client.get(
            "/api/v1/dashboard/financial", headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200, response.text
        stats = response.json()
        # exactly one of the three is overdue: past due and unpaid. No due date, or a future one, is not.
        assert stats["overdue_invoices"] == 1
        assert stats["total_invoices"] == 3
        assert stats["overdue_amount"] > 0

