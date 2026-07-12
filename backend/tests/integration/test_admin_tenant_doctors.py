"""Integration tests for tenant doctor management."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.shared.models import User


@pytest.mark.asyncio
async def test_admin_can_add_multiple_doctors_to_existing_tenant(
    admin_client: AsyncClient,
    db_session,
    test_tenant,
    test_user,
):
    response = await admin_client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/doctors",
        json={
            "email": "second.doctor@test.com",
            "password": "SecondPass123",
            "full_name": "Dr. Second Doctor",
            "phone": "+8801711111111",
            "language": "en",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == test_tenant.id
    assert body["doctor"]["email"] == "second.doctor@test.com"
    assert body["doctor"]["role"] == "doctor"

    users_result = await db_session.execute(
        select(User).where(
            User.tenant_id == test_tenant.id,
            User.role == "doctor",
        )
    )
    doctors = users_result.scalars().all()
    assert {doctor.email for doctor in doctors} == {
        test_user.email,
        "second.doctor@test.com",
    }

    detail_response = await admin_client.get(f"/api/v1/admin/tenants/{test_tenant.id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["doctors"]) == 2


@pytest.mark.asyncio
async def test_admin_cannot_add_doctor_with_duplicate_email(
    admin_client: AsyncClient,
    test_tenant,
    test_user,
):
    response = await admin_client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/doctors",
        json={
            "email": test_user.email,
            "password": "SecondPass123",
            "full_name": "Dr. Duplicate",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_cannot_add_doctor_to_missing_tenant(admin_client: AsyncClient):
    response = await admin_client.post(
        "/api/v1/admin/tenants/missing-tenant/doctors",
        json={
            "email": "missing.tenant.doctor@test.com",
            "password": "SecondPass123",
            "full_name": "Dr. Missing Tenant",
        },
    )

    assert response.status_code == 404
    assert "tenant not found" in response.json()["detail"].lower()
