"""Unit tests for appointment service."""

import pytest
from datetime import date, time, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.appointments.service import AppointmentService
from app.shared.models import Appointment, Visit
from app.shared.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentCancel,
    VisitCreate,
    VisitUpdate,
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
async def test_doctor(db_session, test_tenant_data):
    """Create test doctor."""
    from app.shared.models import User

    doctor = User(
        id=str(uuid4()),
        tenant_id=test_tenant_data.id,
        email="doctor@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",  # Fake hash for testing
        role="doctor",
        full_name="Dr. Test",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def test_patient(db_session, test_tenant_data):
    """Create test patient."""
    from app.shared.models import Patient

    patient = Patient(
        id=str(uuid4()),
        tenant_id=test_tenant_data.id,
        full_name="Test Patient",
        is_active=True,
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
def doctor_id(test_doctor):
    """Test doctor ID."""
    return test_doctor.id


@pytest.fixture
def patient_id(test_patient):
    """Test patient ID."""
    return test_patient.id


@pytest.fixture
def user_id(test_doctor):
    """Test user ID for created_by/updated_by."""
    return test_doctor.id


@pytest.fixture
async def appointment_service(db_session, tenant_id):
    """Create appointment service instance."""
    return AppointmentService(db=db_session, tenant_id=tenant_id)


# ===== Appointment Creation Tests =====


@pytest.mark.asyncio
async def test_create_appointment_success(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test successful appointment creation."""
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Routine checkup",
        notes="First visit",
    )

    appointment = await appointment_service.create_appointment(data, created_by=user_id)

    assert appointment.id is not None
    assert appointment.patient_id == patient_id
    assert appointment.doctor_id == doctor_id
    assert appointment.status == "scheduled"
    assert appointment.reminder_sent is False
    assert appointment.created_by == user_id


@pytest.mark.asyncio
async def test_create_appointment_conflict(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test appointment creation with time slot conflict."""
    apt_date = date.today() + timedelta(days=1)
    apt_time = time(10, 0)

    # Create first appointment
    data1 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        duration_minutes=30,
        reason="First appointment",
    )
    await appointment_service.create_appointment(data1, created_by=user_id)

    # Try to create overlapping appointment
    data2 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=time(10, 15),  # Overlaps with first appointment
        duration_minutes=30,
        reason="Second appointment",
    )

    with pytest.raises(HTTPException) as exc_info:
        await appointment_service.create_appointment(data2, created_by=user_id)

    assert exc_info.value.status_code == 409
    assert "not available" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_appointment_no_conflict_different_time(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test appointment creation with non-overlapping time slots."""
    apt_date = date.today() + timedelta(days=1)

    # Create first appointment at 10:00-10:30
    data1 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="First appointment",
    )
    apt1 = await appointment_service.create_appointment(data1, created_by=user_id)

    # Create second appointment at 10:30-11:00 (no overlap)
    data2 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=time(10, 30),
        duration_minutes=30,
        reason="Second appointment",
    )
    apt2 = await appointment_service.create_appointment(data2, created_by=user_id)

    assert apt1.id != apt2.id
    assert apt1.appointment_time == time(10, 0)
    assert apt2.appointment_time == time(10, 30)


# ===== Time Slot Validation Tests =====


@pytest.mark.asyncio
async def test_check_time_slot_available_empty(
    appointment_service, doctor_id
):
    """Test time slot availability when no appointments exist."""
    is_available = await appointment_service.check_time_slot_available(
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
    )

    assert is_available is True


@pytest.mark.asyncio
async def test_check_time_slot_unavailable_exact_overlap(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test time slot when exact same time is taken."""
    apt_date = date.today() + timedelta(days=1)
    apt_time = time(10, 0)

    # Create appointment
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        duration_minutes=30,
        reason="Test",
    )
    await appointment_service.create_appointment(data, created_by=user_id)

    # Check same slot
    is_available = await appointment_service.check_time_slot_available(
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        duration_minutes=30,
    )

    assert is_available is False


@pytest.mark.asyncio
async def test_check_time_slot_exclude_appointment(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test time slot availability excluding specific appointment (for updates)."""
    apt_date = date.today() + timedelta(days=1)
    apt_time = time(10, 0)

    # Create appointment
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        duration_minutes=30,
        reason="Test",
    )
    appointment = await appointment_service.create_appointment(data, created_by=user_id)

    # Check same slot but exclude this appointment
    is_available = await appointment_service.check_time_slot_available(
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        duration_minutes=30,
        exclude_appointment_id=appointment.id,
    )

    assert is_available is True


# ===== Appointment Retrieval Tests =====


@pytest.mark.asyncio
async def test_get_appointment_success(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test getting appointment by ID."""
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Test",
    )
    created = await appointment_service.create_appointment(data, created_by=user_id)

    retrieved = await appointment_service.get_appointment(created.id)

    assert retrieved.id == created.id
    assert retrieved.patient_id == patient_id


@pytest.mark.asyncio
async def test_get_appointment_not_found(appointment_service):
    """Test getting non-existent appointment."""
    with pytest.raises(HTTPException) as exc_info:
        await appointment_service.get_appointment(str(uuid4()))

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_appointments_with_filters(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test listing appointments with filters."""
    apt_date = date.today() + timedelta(days=1)

    # Create multiple appointments
    for i in range(3):
        data = AppointmentCreate(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=apt_date,
            appointment_time=time(10 + i, 0),
            duration_minutes=30,
            reason=f"Appointment {i}",
        )
        await appointment_service.create_appointment(data, created_by=user_id)

    # List all appointments
    appointments = await appointment_service.list_appointments()
    assert len(appointments) == 3

    # Filter by date
    filtered = await appointment_service.list_appointments(appointment_date=apt_date)
    assert len(filtered) == 3

    # Filter by patient
    filtered = await appointment_service.list_appointments(patient_id=patient_id)
    assert len(filtered) == 3

    # Filter by doctor
    filtered = await appointment_service.list_appointments(doctor_id=doctor_id)
    assert len(filtered) == 3


# ===== Appointment Update Tests =====


@pytest.mark.asyncio
async def test_update_appointment_success(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test successful appointment update."""
    # Create appointment
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Original reason",
    )
    appointment = await appointment_service.create_appointment(data, created_by=user_id)

    # Update appointment
    update_data = AppointmentUpdate(
        reason="Updated reason",
        notes="Added notes",
        status="confirmed",
    )
    updated = await appointment_service.update_appointment(
        appointment.id, update_data, updated_by=user_id
    )

    assert updated.reason == "Updated reason"
    assert updated.notes == "Added notes"
    assert updated.status == "confirmed"
    assert updated.updated_by == user_id


@pytest.mark.asyncio
async def test_update_appointment_time_conflict(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test updating appointment to conflicting time slot."""
    apt_date = date.today() + timedelta(days=1)

    # Create two appointments
    data1 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="First",
    )
    apt1 = await appointment_service.create_appointment(data1, created_by=user_id)

    data2 = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        appointment_time=time(11, 0),
        duration_minutes=30,
        reason="Second",
    )
    apt2 = await appointment_service.create_appointment(data2, created_by=user_id)

    # Try to update apt2 to overlap with apt1
    update_data = AppointmentUpdate(appointment_time=time(10, 15))

    with pytest.raises(HTTPException) as exc_info:
        await appointment_service.update_appointment(
            apt2.id, update_data, updated_by=user_id
        )

    assert exc_info.value.status_code == 409


# ===== Appointment Cancellation Tests =====


@pytest.mark.asyncio
async def test_cancel_appointment(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test cancelling an appointment."""
    # Create appointment
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Test",
    )
    appointment = await appointment_service.create_appointment(data, created_by=user_id)

    # Cancel appointment
    cancel_data = AppointmentCancel(cancellation_reason="Patient requested")
    cancelled = await appointment_service.cancel_appointment(
        appointment.id, cancel_data, updated_by=user_id
    )

    assert cancelled.status == "cancelled"
    assert cancelled.cancellation_reason == "Patient requested"
    assert cancelled.cancelled_at is not None


# ===== Visit Tests =====


@pytest.mark.asyncio
async def test_create_visit_success(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test successful visit creation."""
    data = VisitCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        visit_date=date.today(),
        visit_type="consultation",
        chief_complaint="Headache",
        temperature="98.6°F",
        blood_pressure="120/80",
    )

    visit = await appointment_service.create_visit(data, created_by=user_id)

    assert visit.id is not None
    assert visit.patient_id == patient_id
    assert visit.status == "in_progress"
    assert visit.chief_complaint == "Headache"


@pytest.mark.asyncio
async def test_create_visit_with_appointment_link(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test creating visit linked to appointment."""
    # Create appointment
    apt_data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today(),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Consultation",
    )
    appointment = await appointment_service.create_appointment(apt_data, created_by=user_id)

    # Create visit linked to appointment
    visit_data = VisitCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        visit_date=date.today(),
        visit_type="consultation",
        appointment_id=appointment.id,
        chief_complaint="Test complaint",
    )
    visit = await appointment_service.create_visit(visit_data, created_by=user_id)

    # Verify appointment status updated
    updated_apt = await appointment_service.get_appointment(appointment.id)
    assert updated_apt.status == "in_progress"
    assert visit.appointment_id == appointment.id


@pytest.mark.asyncio
async def test_update_visit_completes_appointment(
    appointment_service, doctor_id, patient_id, user_id
):
    """Test that completing visit also completes linked appointment."""
    # Create appointment
    apt_data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today(),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Consultation",
    )
    appointment = await appointment_service.create_appointment(apt_data, created_by=user_id)

    # Create visit
    visit_data = VisitCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        visit_date=date.today(),
        visit_type="consultation",
        appointment_id=appointment.id,
    )
    visit = await appointment_service.create_visit(visit_data, created_by=user_id)

    # Complete visit
    update_data = VisitUpdate(
        status="completed",
        provisional_diagnosis="Common cold",
        treatment_plan="Rest and fluids",
    )
    updated_visit = await appointment_service.update_visit(
        visit.id, update_data, updated_by=user_id
    )

    # Verify both visit and appointment are completed
    assert updated_visit.status == "completed"

    updated_apt = await appointment_service.get_appointment(appointment.id)
    assert updated_apt.status == "completed"


# ===== Multi-tenant Isolation Tests =====


@pytest.mark.asyncio
async def test_tenant_isolation(db_session, test_tenant_data, test_doctor, test_patient, patient_id, doctor_id, user_id):
    """Test that appointments are isolated by tenant."""
    from app.shared.models import Tenant, User, Patient

    # Create second tenant with data
    tenant2 = Tenant(
        id=str(uuid4()),
        name="Tenant 2 Clinic",
        email="tenant2@test.com",
        clinic_name="Tenant 2",
        specializations=["ayurveda"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add(tenant2)

    doctor2 = User(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        email="doctor2@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        role="doctor",
        full_name="Dr. Test 2",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor2)

    patient2 = Patient(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        full_name="Patient 2",
        is_active=True,
    )
    db_session.add(patient2)
    await db_session.commit()

    service1 = AppointmentService(db=db_session, tenant_id=test_tenant_data.id)
    service2 = AppointmentService(db=db_session, tenant_id=tenant2.id)

    # Create appointment for tenant1
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.today() + timedelta(days=1),
        appointment_time=time(10, 0),
        duration_minutes=30,
        reason="Tenant 1 appointment",
    )
    apt1 = await service1.create_appointment(data, created_by=user_id)

    # Try to get appointment from tenant2 - should fail
    with pytest.raises(HTTPException) as exc_info:
        await service2.get_appointment(apt1.id)

    assert exc_info.value.status_code == 404

    # List appointments for tenant2 - should be empty
    appointments = await service2.list_appointments()
    assert len(appointments) == 0
