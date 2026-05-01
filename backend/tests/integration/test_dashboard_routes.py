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
