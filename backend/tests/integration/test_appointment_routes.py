"""Integration tests for appointment API routes."""

import pytest
from datetime import date, time, timedelta
from uuid import uuid4

from httpx import AsyncClient

from app.main import app
from app.shared.models import User, Tenant


@pytest.fixture
async def test_tenant(db_session):
    """Create test tenant."""
    tenant = Tenant(
        id=str(uuid4()),
        name="Test Clinic",
        slug="test-clinic",
        specializations=["homeopathy"],
        plan="basic",
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_doctor(db_session, test_tenant):
    """Create test doctor user."""
    from app.core.security import get_password_hash

    doctor = User(
        id=str(uuid4()),
        tenant_id=test_tenant.id,
        email="doctor@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Dr. Test Doctor",
        role="doctor",
        is_active=True,
        email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def auth_headers(test_doctor, test_tenant):
    """Create authentication headers with JWT token."""
    from app.core.security import create_access_token

    token_data = {
        "sub": test_doctor.id,
        "email": test_doctor.email,
        "role": test_doctor.role,
        "tenant_id": test_tenant.id,
    }
    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def patient_id():
    """Test patient ID."""
    return str(uuid4())


# ===== Appointment Creation Tests =====


@pytest.mark.asyncio
async def test_create_appointment_success(auth_headers, test_doctor, patient_id):
    """Test successful appointment creation via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
                "reason": "Routine checkup",
                "notes": "First visit",
            },
            headers=auth_headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == patient_id
    assert data["doctor_id"] == test_doctor.id
    assert data["status"] == "scheduled"
    assert data["reminder_sent"] is False


@pytest.mark.asyncio
async def test_create_appointment_without_auth(test_doctor, patient_id):
    """Test appointment creation without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_appointment_time_conflict(
    auth_headers, test_doctor, patient_id
):
    """Test creating appointment with time conflict."""
    apt_date = str(date.today() + timedelta(days=1))
    apt_time = "10:00:00"

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create first appointment
        response1 = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": apt_date,
                "appointment_time": apt_time,
                "duration_minutes": 30,
                "reason": "First appointment",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Try to create overlapping appointment
        response2 = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": apt_date,
                "appointment_time": "10:15:00",  # Overlaps
                "duration_minutes": 30,
                "reason": "Second appointment",
            },
            headers=auth_headers,
        )

    assert response2.status_code == 409
    assert "not available" in response2.json()["detail"].lower()


# ===== Appointment Listing Tests =====


@pytest.mark.asyncio
async def test_list_appointments(auth_headers, test_doctor, patient_id):
    """Test listing appointments."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create multiple appointments
        for i in range(3):
            await client.post(
                "/api/v1/appointments",
                json={
                    "patient_id": patient_id,
                    "doctor_id": test_doctor.id,
                    "appointment_date": str(date.today() + timedelta(days=1)),
                    "appointment_time": f"{10 + i}:00:00",
                    "duration_minutes": 30,
                    "reason": f"Appointment {i}",
                },
                headers=auth_headers,
            )

        # List all appointments
        response = await client.get(
            "/api/v1/appointments",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_appointments_with_filters(
    auth_headers, test_doctor, patient_id
):
    """Test listing appointments with filters."""
    apt_date = date.today() + timedelta(days=1)

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(apt_date),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
                "reason": "Test",
            },
            headers=auth_headers,
        )

        # Filter by date
        response = await client.get(
            f"/api/v1/appointments?appointment_date={apt_date}",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == patient_id


# ===== Appointment Retrieval Tests =====


@pytest.mark.asyncio
async def test_get_appointment(auth_headers, test_doctor, patient_id):
    """Test getting appointment by ID."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        create_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        appointment_id = create_response.json()["id"]

        # Get appointment
        response = await client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == appointment_id


@pytest.mark.asyncio
async def test_get_appointment_not_found(auth_headers):
    """Test getting non-existent appointment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/appointments/{uuid4()}",
            headers=auth_headers,
        )

    assert response.status_code == 404


# ===== Appointment Update Tests =====


@pytest.mark.asyncio
async def test_update_appointment(auth_headers, test_doctor, patient_id):
    """Test updating appointment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        create_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
                "reason": "Original reason",
            },
            headers=auth_headers,
        )
        appointment_id = create_response.json()["id"]

        # Update appointment
        response = await client.patch(
            f"/api/v1/appointments/{appointment_id}",
            json={
                "reason": "Updated reason",
                "notes": "Added notes",
                "status": "confirmed",
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["reason"] == "Updated reason"
    assert data["notes"] == "Added notes"
    assert data["status"] == "confirmed"


# ===== Appointment Cancellation Tests =====


@pytest.mark.asyncio
async def test_cancel_appointment(auth_headers, test_doctor, patient_id):
    """Test cancelling appointment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        create_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        appointment_id = create_response.json()["id"]

        # Cancel appointment
        response = await client.post(
            f"/api/v1/appointments/{appointment_id}/cancel",
            json={"cancellation_reason": "Patient requested"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Patient requested"
    assert data["cancelled_at"] is not None


# ===== Appointment Deletion Tests =====


@pytest.mark.asyncio
async def test_delete_appointment(auth_headers, test_doctor, patient_id):
    """Test deleting appointment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        create_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        appointment_id = create_response.json()["id"]

        # Delete appointment
        response = await client.delete(
            f"/api/v1/appointments/{appointment_id}",
            headers=auth_headers,
        )

    assert response.status_code == 204

    # Verify deleted
    async with AsyncClient(app=app, base_url="http://test") as client:
        get_response = await client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=auth_headers,
        )
    assert get_response.status_code == 404


# ===== Visit Tests =====


@pytest.mark.asyncio
async def test_create_visit(auth_headers, test_doctor, patient_id):
    """Test creating visit."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/appointments/visits",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "visit_date": str(date.today()),
                "visit_type": "consultation",
                "chief_complaint": "Headache",
                "temperature": "98.6°F",
                "blood_pressure": "120/80",
            },
            headers=auth_headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == patient_id
    assert data["status"] == "in_progress"
    assert data["chief_complaint"] == "Headache"


@pytest.mark.asyncio
async def test_create_visit_with_appointment(
    auth_headers, test_doctor, patient_id
):
    """Test creating visit linked to appointment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment
        apt_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today()),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        appointment_id = apt_response.json()["id"]

        # Create visit linked to appointment
        visit_response = await client.post(
            "/api/v1/appointments/visits",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "visit_date": str(date.today()),
                "visit_type": "consultation",
                "appointment_id": appointment_id,
                "chief_complaint": "Test complaint",
            },
            headers=auth_headers,
        )

        # Get appointment to verify status changed
        apt_get = await client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=auth_headers,
        )

    assert visit_response.status_code == 201
    assert visit_response.json()["appointment_id"] == appointment_id
    assert apt_get.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_visit(auth_headers, test_doctor, patient_id):
    """Test updating visit."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create visit
        create_response = await client.post(
            "/api/v1/appointments/visits",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "visit_date": str(date.today()),
                "visit_type": "consultation",
            },
            headers=auth_headers,
        )
        visit_id = create_response.json()["id"]

        # Update visit
        response = await client.patch(
            f"/api/v1/appointments/visits/{visit_id}",
            json={
                "status": "completed",
                "provisional_diagnosis": "Common cold",
                "treatment_plan": "Rest and fluids",
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["provisional_diagnosis"] == "Common cold"


# ===== Multi-tenant Isolation Tests =====


@pytest.mark.asyncio
async def test_tenant_isolation_appointments(db_session, test_doctor, patient_id):
    """Test that appointments are isolated between tenants."""
    from app.core.security import create_access_token, get_password_hash

    # Create second tenant and doctor
    tenant2 = Tenant(
        id=str(uuid4()),
        name="Other Clinic",
        slug="other-clinic",
        specializations=["ayurveda"],
        plan="basic",
        is_active=True,
    )
    db_session.add(tenant2)

    doctor2 = User(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        email="doctor2@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Dr. Other Doctor",
        role="doctor",
        is_active=True,
        email_verified=True,
    )
    db_session.add(doctor2)
    await db_session.commit()

    # Create tokens for both doctors
    token1 = create_access_token(
        {
            "sub": test_doctor.id,
            "email": test_doctor.email,
            "role": test_doctor.role,
            "tenant_id": test_doctor.tenant_id,
        }
    )
    token2 = create_access_token(
        {
            "sub": doctor2.id,
            "email": doctor2.email,
            "role": doctor2.role,
            "tenant_id": tenant2.id,
        }
    )

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create appointment for tenant1
        apt_response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient_id,
                "doctor_id": test_doctor.id,
                "appointment_date": str(date.today() + timedelta(days=1)),
                "appointment_time": "10:00:00",
                "duration_minutes": 30,
            },
            headers=headers1,
        )
        appointment_id = apt_response.json()["id"]

        # Try to access from tenant2 - should fail
        response = await client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=headers2,
        )

    assert response.status_code == 404

    # List appointments for tenant2 - should be empty
    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get(
            "/api/v1/appointments",
            headers=headers2,
        )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 0
