"""Unit tests for patient service."""

import pytest
from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.patient.service import PatientService
from app.shared.models import Patient, PatientTag, PatientDiagnosis
from app.shared.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientTagCreate,
    PatientTagUpdate,
    PatientDiagnosisCreate,
    PatientDiagnosisUpdate,
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
        password_hash="$2b$12$test_hash_for_testing_only",
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
def tenant_id(test_tenant_data):
    """Test tenant ID."""
    return test_tenant_data.id


@pytest.fixture
def user_id(test_doctor):
    """Test user ID for created_by/updated_by."""
    return test_doctor.id


@pytest.fixture
def patient_service(db_session, tenant_id):
    """Create patient service instance."""
    return PatientService(db=db_session, tenant_id=tenant_id)


# ===== Patient CRUD Tests =====


@pytest.mark.asyncio
async def test_create_patient_minimal(patient_service, user_id):
    """Test creating patient with minimal required data."""
    data = PatientCreate(full_name="John Doe")

    patient = await patient_service.create_patient(data, created_by=user_id)

    assert patient.id is not None
    assert patient.full_name == "John Doe"
    assert patient.tenant_id == patient_service.tenant_id
    assert patient.is_active is True
    assert patient.created_by == user_id


@pytest.mark.asyncio
async def test_create_patient_full(patient_service, user_id):
    """Test creating patient with all fields."""
    data = PatientCreate(
        full_name="Jane Smith",
        date_of_birth=date(1990, 5, 15),
        gender="female",
        blood_group="O+",
        phone="+8801712345678",
        email="jane@example.com",
        whatsapp="+8801712345678",
        address="123 Main St, Dhaka",
        chief_complaint="Chronic headache",
        medical_history="No significant history",
        next_visit_date=date(2026, 5, 1),
    )

    patient = await patient_service.create_patient(data, created_by=user_id)

    assert patient.full_name == "Jane Smith"
    assert patient.date_of_birth == date(1990, 5, 15)
    assert patient.gender == "female"
    assert patient.blood_group == "O+"
    assert patient.phone == "+8801712345678"
    assert patient.email == "jane@example.com"


@pytest.mark.asyncio
async def test_get_patient(patient_service, user_id):
    """Test getting patient by ID."""
    # Create patient
    data = PatientCreate(full_name="Test Patient")
    created = await patient_service.create_patient(data, created_by=user_id)

    # Get patient
    patient = await patient_service.get_patient(created.id)

    assert patient.id == created.id
    assert patient.full_name == "Test Patient"


@pytest.mark.asyncio
async def test_get_patient_not_found(patient_service):
    """Test getting non-existent patient raises 404."""
    with pytest.raises(HTTPException) as exc:
        await patient_service.get_patient(str(uuid4()))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_patients_empty(patient_service):
    """Test listing patients when none exist."""
    patients = await patient_service.list_patients()
    assert patients == []


@pytest.mark.asyncio
async def test_list_patients_basic(patient_service, user_id):
    """Test listing patients."""
    # Create 3 patients
    for i in range(3):
        data = PatientCreate(full_name=f"Patient {i}")
        await patient_service.create_patient(data, created_by=user_id)

    patients = await patient_service.list_patients()

    assert len(patients) == 3
    # Ordered by created_at desc, so most recent first
    assert patients[0].full_name == "Patient 2"


@pytest.mark.asyncio
async def test_list_patients_search_by_name(patient_service, user_id):
    """Test searching patients by name."""
    # Create patients
    await patient_service.create_patient(
        PatientCreate(full_name="John Doe"), created_by=user_id
    )
    await patient_service.create_patient(
        PatientCreate(full_name="Jane Smith"), created_by=user_id
    )
    await patient_service.create_patient(
        PatientCreate(full_name="Bob Johnson"), created_by=user_id
    )

    # Search by "John" - should match "John Doe" and "Bob Johnson"
    patients = await patient_service.list_patients(search="John")
    assert len(patients) == 2
    names = {p.full_name for p in patients}
    assert "John Doe" in names
    assert "Bob Johnson" in names


@pytest.mark.asyncio
async def test_list_patients_search_by_phone(patient_service, user_id):
    """Test searching patients by phone."""
    await patient_service.create_patient(
        PatientCreate(full_name="Patient 1", phone="01712345678"),
        created_by=user_id,
    )
    await patient_service.create_patient(
        PatientCreate(full_name="Patient 2", phone="01798765432"),
        created_by=user_id,
    )

    patients = await patient_service.list_patients(search="01712")
    assert len(patients) == 1
    assert patients[0].phone == "01712345678"


@pytest.mark.asyncio
async def test_list_patients_search_by_email(patient_service, user_id):
    """Test searching patients by email."""
    await patient_service.create_patient(
        PatientCreate(full_name="Patient 1", email="john@example.com"),
        created_by=user_id,
    )
    await patient_service.create_patient(
        PatientCreate(full_name="Patient 2", email="jane@example.com"),
        created_by=user_id,
    )

    patients = await patient_service.list_patients(search="john@")
    assert len(patients) == 1
    assert patients[0].email == "john@example.com"


@pytest.mark.asyncio
async def test_list_patients_filter_active(patient_service, user_id):
    """Test filtering patients by active status."""
    # Create active and inactive patients
    p1 = await patient_service.create_patient(
        PatientCreate(full_name="Active Patient"), created_by=user_id
    )
    p2 = await patient_service.create_patient(
        PatientCreate(full_name="Inactive Patient"), created_by=user_id
    )
    # Soft delete p2
    await patient_service.delete_patient(p2.id, updated_by=user_id)

    # Filter by active
    active = await patient_service.list_patients(is_active=True)
    assert len(active) == 1
    assert active[0].full_name == "Active Patient"

    # Filter by inactive
    inactive = await patient_service.list_patients(is_active=False)
    assert len(inactive) == 1
    assert inactive[0].full_name == "Inactive Patient"


@pytest.mark.asyncio
async def test_list_patients_filter_upcoming_visit(patient_service, user_id):
    """Test filtering patients by upcoming visit."""
    from datetime import timedelta

    today = date.today()
    future = today + timedelta(days=7)
    past = today - timedelta(days=7)

    # Patient with upcoming visit
    await patient_service.create_patient(
        PatientCreate(full_name="Has Upcoming", next_visit_date=future),
        created_by=user_id,
    )
    # Patient with past visit
    await patient_service.create_patient(
        PatientCreate(full_name="Has Past", next_visit_date=past),
        created_by=user_id,
    )
    # Patient with no visit
    await patient_service.create_patient(
        PatientCreate(full_name="No Visit"), created_by=user_id
    )

    # Filter with upcoming visits
    with_upcoming = await patient_service.list_patients(has_upcoming_visit=True)
    assert len(with_upcoming) == 1
    assert with_upcoming[0].full_name == "Has Upcoming"

    # Filter without upcoming visits
    without_upcoming = await patient_service.list_patients(has_upcoming_visit=False)
    assert len(without_upcoming) == 2


@pytest.mark.asyncio
async def test_list_patients_pagination(patient_service, user_id):
    """Test pagination."""
    # Create 10 patients
    for i in range(10):
        await patient_service.create_patient(
            PatientCreate(full_name=f"Patient {i:02d}"), created_by=user_id
        )

    # Get first page
    page1 = await patient_service.list_patients(limit=5, offset=0)
    assert len(page1) == 5

    # Get second page
    page2 = await patient_service.list_patients(limit=5, offset=5)
    assert len(page2) == 5

    # Pages should not overlap
    page1_ids = {p.id for p in page1}
    page2_ids = {p.id for p in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_update_patient(patient_service, user_id):
    """Test updating patient."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Old Name"), created_by=user_id
    )

    # Update
    update_data = PatientUpdate(
        full_name="New Name",
        phone="01712345678",
        email="newemail@example.com",
    )
    updated = await patient_service.update_patient(
        patient.id, update_data, updated_by=user_id
    )

    assert updated.full_name == "New Name"
    assert updated.phone == "01712345678"
    assert updated.email == "newemail@example.com"
    assert updated.updated_by == user_id


@pytest.mark.asyncio
async def test_update_patient_partial(patient_service, user_id):
    """Test partial update."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="John Doe", phone="01712345678"),
        created_by=user_id,
    )

    # Update only phone
    update_data = PatientUpdate(phone="01798765432")
    updated = await patient_service.update_patient(
        patient.id, update_data, updated_by=user_id
    )

    assert updated.full_name == "John Doe"  # Unchanged
    assert updated.phone == "01798765432"  # Changed


@pytest.mark.asyncio
async def test_delete_patient(patient_service, user_id):
    """Test soft deleting patient."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="To Delete"), created_by=user_id
    )

    # Delete
    deleted = await patient_service.delete_patient(patient.id, updated_by=user_id)

    assert deleted.is_active is False
    assert deleted.updated_by == user_id


@pytest.mark.asyncio
async def test_get_patient_count(patient_service, user_id):
    """Test getting patient count."""
    # Initially 0
    count = await patient_service.get_patient_count()
    assert count == 0

    # Create 3 active patients
    for i in range(3):
        await patient_service.create_patient(
            PatientCreate(full_name=f"Patient {i}"), created_by=user_id
        )

    count = await patient_service.get_patient_count()
    assert count == 3

    # Create and delete one
    p = await patient_service.create_patient(
        PatientCreate(full_name="Temp"), created_by=user_id
    )
    await patient_service.delete_patient(p.id, updated_by=user_id)

    # Count should still be 3 (only active)
    count = await patient_service.get_patient_count()
    assert count == 3


# ===== Patient Tag Tests =====


@pytest.mark.asyncio
async def test_create_patient_tag(patient_service, user_id):
    """Test creating patient tag."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )

    # Create tag
    tag_data = PatientTagCreate(
        patient_id=patient.id,
        tag_type="chronic",
        tag_value="Diabetes",
        notes="Type 2, managed with diet",
    )
    tag = await patient_service.create_patient_tag(tag_data, created_by=user_id)

    assert tag.patient_id == patient.id
    assert tag.tag_type == "chronic"
    assert tag.tag_value == "Diabetes"
    assert tag.notes == "Type 2, managed with diet"


@pytest.mark.asyncio
async def test_create_tag_for_nonexistent_patient(patient_service, user_id):
    """Test creating tag for non-existent patient raises 404."""
    tag_data = PatientTagCreate(
        patient_id=str(uuid4()),
        tag_type="allergy",
        tag_value="Penicillin",
    )

    with pytest.raises(HTTPException) as exc:
        await patient_service.create_patient_tag(tag_data, created_by=user_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_patient_tags(patient_service, user_id):
    """Test listing patient tags."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )

    # Create tags
    await patient_service.create_patient_tag(
        PatientTagCreate(patient_id=patient.id, tag_type="chronic", tag_value="Diabetes"),
        created_by=user_id,
    )
    await patient_service.create_patient_tag(
        PatientTagCreate(patient_id=patient.id, tag_type="allergy", tag_value="Penicillin"),
        created_by=user_id,
    )

    # List tags
    tags = await patient_service.list_patient_tags(patient.id)

    assert len(tags) == 2
    tag_types = {t.tag_type for t in tags}
    assert "chronic" in tag_types
    assert "allergy" in tag_types


@pytest.mark.asyncio
async def test_update_patient_tag(patient_service, user_id):
    """Test updating patient tag."""
    # Create patient and tag
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )
    tag = await patient_service.create_patient_tag(
        PatientTagCreate(patient_id=patient.id, tag_type="chronic", tag_value="Old Value"),
        created_by=user_id,
    )

    # Update tag
    update_data = PatientTagUpdate(tag_value="New Value", notes="Updated notes")
    updated = await patient_service.update_patient_tag(tag.id, update_data, updated_by=user_id)

    assert updated.tag_value == "New Value"
    assert updated.notes == "Updated notes"


@pytest.mark.asyncio
async def test_delete_patient_tag(patient_service, user_id, db_session):
    """Test deleting patient tag."""
    # Create patient and tag
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )
    tag = await patient_service.create_patient_tag(
        PatientTagCreate(patient_id=patient.id, tag_type="chronic", tag_value="Diabetes"),
        created_by=user_id,
    )

    # Delete tag
    await patient_service.delete_patient_tag(tag.id)

    # Verify deleted (hard delete)
    result = await db_session.execute(
        select(PatientTag).where(PatientTag.id == tag.id)
    )
    assert result.scalar_one_or_none() is None


# ===== Patient Diagnosis Tests =====


@pytest.mark.asyncio
async def test_create_patient_diagnosis(patient_service, user_id):
    """Test creating patient diagnosis."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )

    # Create diagnosis
    diag_data = PatientDiagnosisCreate(
        patient_id=patient.id,
        description="Chronic bronchitis",
        icd_code="J42",
        diagnosed_at=date(2026, 4, 15),
    )
    diagnosis = await patient_service.create_patient_diagnosis(diag_data, created_by=user_id)

    assert diagnosis.patient_id == patient.id
    assert diagnosis.description == "Chronic bronchitis"
    assert diagnosis.icd_code == "J42"
    assert diagnosis.is_active is True


@pytest.mark.asyncio
async def test_list_patient_diagnoses(patient_service, user_id):
    """Test listing patient diagnoses."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )

    # Create diagnoses
    await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="Diagnosis 1",
            diagnosed_at=date(2026, 4, 1),
        ),
        created_by=user_id,
    )
    await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="Diagnosis 2",
            diagnosed_at=date(2026, 4, 15),
        ),
        created_by=user_id,
    )

    # List diagnoses
    diagnoses = await patient_service.list_patient_diagnoses(patient.id)

    assert len(diagnoses) == 2
    # Ordered by diagnosed_at desc
    assert diagnoses[0].description == "Diagnosis 2"


@pytest.mark.asyncio
async def test_list_patient_diagnoses_filter_active(patient_service, user_id):
    """Test filtering diagnoses by active status."""
    # Create patient
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )

    # Create active and inactive diagnoses
    d1 = await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="Active",
            diagnosed_at=date(2026, 4, 1),
        ),
        created_by=user_id,
    )
    d2 = await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="Inactive",
            diagnosed_at=date(2026, 4, 2),
        ),
        created_by=user_id,
    )
    # Soft delete d2
    await patient_service.delete_patient_diagnosis(d2.id, updated_by=user_id)

    # List active only
    active = await patient_service.list_patient_diagnoses(patient.id, active_only=True)
    assert len(active) == 1
    assert active[0].description == "Active"

    # List all
    all_diag = await patient_service.list_patient_diagnoses(patient.id, active_only=False)
    assert len(all_diag) == 2


@pytest.mark.asyncio
async def test_update_patient_diagnosis(patient_service, user_id):
    """Test updating patient diagnosis."""
    # Create patient and diagnosis
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )
    diagnosis = await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="Old Description",
            diagnosed_at=date(2026, 4, 1),
        ),
        created_by=user_id,
    )

    # Update diagnosis
    update_data = PatientDiagnosisUpdate(
        description="New Description",
        icd_code="A00",
    )
    updated = await patient_service.update_patient_diagnosis(
        diagnosis.id, update_data, updated_by=user_id
    )

    assert updated.description == "New Description"
    assert updated.icd_code == "A00"


@pytest.mark.asyncio
async def test_delete_patient_diagnosis(patient_service, user_id):
    """Test soft deleting patient diagnosis."""
    # Create patient and diagnosis
    patient = await patient_service.create_patient(
        PatientCreate(full_name="Patient"), created_by=user_id
    )
    diagnosis = await patient_service.create_patient_diagnosis(
        PatientDiagnosisCreate(
            patient_id=patient.id,
            description="To Delete",
            diagnosed_at=date(2026, 4, 1),
        ),
        created_by=user_id,
    )

    # Delete
    deleted = await patient_service.delete_patient_diagnosis(diagnosis.id, updated_by=user_id)

    assert deleted.is_active is False
    assert deleted.updated_by == user_id


# ===== Multi-Tenant Isolation Tests =====


@pytest.mark.asyncio
async def test_patient_tenant_isolation(db_session, user_id):
    """Test patients are isolated by tenant."""
    from app.shared.models import Tenant

    # Create two tenants
    tenant1 = Tenant(
        id=str(uuid4()),
        name="Clinic 1",
        email="clinic1@test.com",
        clinic_name="Clinic 1",
        specializations=["homeopathy"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    tenant2 = Tenant(
        id=str(uuid4()),
        name="Clinic 2",
        email="clinic2@test.com",
        clinic_name="Clinic 2",
        specializations=["ayurveda"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add_all([tenant1, tenant2])
    await db_session.commit()

    # Create services for each tenant
    service1 = PatientService(db=db_session, tenant_id=tenant1.id)
    service2 = PatientService(db=db_session, tenant_id=tenant2.id)

    # Create patient in tenant1
    await service1.create_patient(PatientCreate(full_name="Patient 1"), created_by=user_id)

    # List from tenant2 - should be empty
    patients = await service2.list_patients()
    assert len(patients) == 0

    # List from tenant1 - should have 1
    patients = await service1.list_patients()
    assert len(patients) == 1
