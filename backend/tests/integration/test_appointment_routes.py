"""Integration tests for appointment and visit API routes."""

from datetime import date, timedelta
from uuid import uuid4

import pytest


def appointment_payload(test_user, test_patient, **overrides):
    payload = {
        "patient_id": test_patient.id,
        "doctor_id": test_user.id,
        "appointment_date": str(date.today() + timedelta(days=1)),
        "appointment_time": "10:00:00",
        "duration_minutes": 30,
        "reason": "Routine checkup",
        "notes": "First visit",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_appointment_success(authenticated_client, test_user, test_patient):
    response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient.id
    assert data["doctor_id"] == test_user.id
    assert data["status"] == "scheduled"
    assert data["reminder_sent"] is False


@pytest.mark.asyncio
async def test_create_appointment_without_auth(client, test_user, test_patient):
    response = await client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_appointment_time_conflict(
    authenticated_client, test_user, test_patient
):
    response1 = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )
    assert response1.status_code == 201

    response2 = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(
            test_user,
            test_patient,
            appointment_time="10:15:00",
            reason="Second appointment",
        ),
    )

    assert response2.status_code == 409
    assert "not available" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_appointments(authenticated_client, test_user, test_patient):
    for index in range(3):
        response = await authenticated_client.post(
            "/api/v1/appointments",
            json=appointment_payload(
                test_user,
                test_patient,
                appointment_time=f"{10 + index}:00:00",
                reason=f"Appointment {index}",
            ),
        )
        assert response.status_code == 201

    response = await authenticated_client.get("/api/v1/appointments")

    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_list_appointments_with_filters(
    authenticated_client, test_user, test_patient
):
    appointment_date = date.today() + timedelta(days=1)
    create_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(
            test_user,
            test_patient,
            appointment_date=str(appointment_date),
        ),
    )
    assert create_response.status_code == 201

    response = await authenticated_client.get(
        f"/api/v1/appointments?appointment_date={appointment_date}"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == test_patient.id


@pytest.mark.asyncio
async def test_get_appointment(authenticated_client, test_user, test_patient):
    create_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )
    appointment_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/appointments/{appointment_id}")

    assert response.status_code == 200
    assert response.json()["id"] == appointment_id


@pytest.mark.asyncio
async def test_get_appointment_not_found(authenticated_client):
    response = await authenticated_client.get(f"/api/v1/appointments/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_appointment(authenticated_client, test_user, test_patient):
    create_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient, reason="Original reason"),
    )
    appointment_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={
            "reason": "Updated reason",
            "notes": "Added notes",
            "status": "confirmed",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reason"] == "Updated reason"
    assert data["notes"] == "Added notes"
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_appointment(authenticated_client, test_user, test_patient):
    create_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )
    appointment_id = create_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancellation_reason": "Patient requested"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Patient requested"
    assert data["cancelled_at"] is not None


@pytest.mark.asyncio
async def test_delete_appointment(authenticated_client, test_user, test_patient):
    create_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
    )
    appointment_id = create_response.json()["id"]

    response = await authenticated_client.delete(
        f"/api/v1/appointments/{appointment_id}"
    )
    get_response = await authenticated_client.get(
        f"/api/v1/appointments/{appointment_id}"
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_visit(authenticated_client, test_user, test_patient):
    response = await authenticated_client.post(
        "/api/v1/appointments/visits",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "visit_date": str(date.today()),
            "visit_type": "consultation",
            "chief_complaint": "Headache",
            "temperature": "98.6F",
            "blood_pressure": "120/80",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient.id
    assert data["status"] == "in_progress"
    assert data["chief_complaint"] == "Headache"


@pytest.mark.asyncio
async def test_create_visit_with_appointment(
    authenticated_client, test_user, test_patient
):
    appointment_response = await authenticated_client.post(
        "/api/v1/appointments",
        json=appointment_payload(
            test_user,
            test_patient,
            appointment_date=str(date.today()),
        ),
    )
    appointment_id = appointment_response.json()["id"]

    visit_response = await authenticated_client.post(
        "/api/v1/appointments/visits",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "visit_date": str(date.today()),
            "visit_type": "consultation",
            "appointment_id": appointment_id,
            "chief_complaint": "Test complaint",
        },
    )
    appointment_get = await authenticated_client.get(
        f"/api/v1/appointments/{appointment_id}"
    )

    assert visit_response.status_code == 201
    assert visit_response.json()["appointment_id"] == appointment_id
    assert appointment_get.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_visit(authenticated_client, test_user, test_patient):
    create_response = await authenticated_client.post(
        "/api/v1/appointments/visits",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "visit_date": str(date.today()),
            "visit_type": "consultation",
        },
    )
    visit_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/api/v1/appointments/visits/{visit_id}",
        json={
            "status": "completed",
            "provisional_diagnosis": "Common cold",
            "treatment_plan": "Rest and fluids",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["provisional_diagnosis"] == "Common cold"


@pytest.mark.asyncio
async def test_tenant_isolation_appointments(
    client,
    test_access_token,
    test_access_token_2,
    test_user,
    test_patient,
):
    tenant_1_headers = {"Authorization": f"Bearer {test_access_token}"}
    tenant_2_headers = {"Authorization": f"Bearer {test_access_token_2}"}

    create_response = await client.post(
        "/api/v1/appointments",
        json=appointment_payload(test_user, test_patient),
        headers=tenant_1_headers,
    )
    appointment_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/appointments/{appointment_id}",
        headers=tenant_2_headers,
    )
    list_response = await client.get("/api/v1/appointments", headers=tenant_2_headers)

    assert get_response.status_code == 404
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0
