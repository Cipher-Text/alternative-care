"""MVP contract/response-shape tests for critical APIs."""

from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_auth_login_response_contract(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "TestPass123"},
    )
    assert response.status_code == 200

    body = response.json()
    assert {"user", "tokens"}.issubset(body.keys())
    assert {"id", "email", "role"}.issubset(body["user"].keys())
    assert {"access_token", "token_type"}.issubset(body["tokens"].keys())
    # refresh_token is never in the body (D8) — delivered only via an
    # httpOnly cookie, invisible to JS.
    assert "refresh_token" not in body["tokens"]
    assert response.cookies.get("refresh_token") is not None


@pytest.mark.asyncio
async def test_auth_me_response_contract(authenticated_client):
    response = await authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200

    body = response.json()
    assert {"id", "email", "role", "is_active", "is_2fa_enabled"}.issubset(
        body["user"].keys()
    )
    assert {"id", "clinic_name", "is_active"}.issubset(body["tenant"].keys())


@pytest.mark.asyncio
async def test_patient_create_response_contract(authenticated_client):
    response = await authenticated_client.post(
        "/api/v1/patients",
        json={
            "full_name": "Contract Patient",
            "date_of_birth": "1990-01-15",
            "gender": "female",
            "phone": "+8801711111111",
            "email": "contract.patient@example.com",
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert {"id", "tenant_id", "full_name", "is_active"}.issubset(body.keys())
    assert body["full_name"] == "Contract Patient"


@pytest.mark.asyncio
async def test_appointment_create_response_contract(authenticated_client, test_user, test_patient):
    response = await authenticated_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "09:30:00",
            "duration_minutes": 30,
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert {
        "id",
        "tenant_id",
        "patient_id",
        "doctor_id",
        "appointment_date",
        "appointment_time",
        "status",
    }.issubset(body.keys())


@pytest.mark.asyncio
async def test_payment_create_response_contract(authenticated_client, test_patient):
    response = await authenticated_client.post(
        "/api/v1/payments",
        json={
            "patient_id": test_patient.id,
            "amount": 900.0,
            "payment_method": "cash",
            "description": "Contract payment",
            "payment_date": str(date.today()),
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert {
        "id",
        "tenant_id",
        "patient_id",
        "amount",
        "payment_method",
        "status",
    }.issubset(body.keys())


@pytest.mark.asyncio
async def test_prescription_create_response_contract(authenticated_client, test_patient):
    response = await authenticated_client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "contract diagnosis",
            "status": "draft",
            "doctors_notes": "notes",
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert {"id", "tenant_id", "patient_id", "status", "diagnosis"}.issubset(
        body.keys()
    )
