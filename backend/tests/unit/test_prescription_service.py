"""Unit tests for prescription service."""

import pytest
from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.prescription.service import PrescriptionService
from app.shared.models import Prescription, PrescriptionItem, Patient
from app.shared.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionItemCreate,
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
async def test_patient(db_session, test_tenant_data, test_doctor):
    """Create test patient."""
    patient = Patient(
        id=str(uuid4()),
        tenant_id=test_tenant_data.id,
        full_name="Test Patient",
        is_active=True,
        created_by=test_doctor.id,
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
def prescription_service(db_session, tenant_id):
    """Create prescription service instance."""
    return PrescriptionService(db=db_session, tenant_id=tenant_id)


# ===== Prescription Creation Tests =====


@pytest.mark.asyncio
async def test_create_prescription_minimal(prescription_service, test_patient, doctor_id):
    """Test creating prescription with minimal data (no items)."""
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Common cold",
        status="draft",
    )

    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    assert prescription.id is not None
    assert prescription.patient_id == test_patient.id
    assert prescription.diagnosis == "Common cold"
    assert prescription.status == "draft"
    assert prescription.prescribed_by == doctor_id
    assert prescription.tenant_id == prescription_service.tenant_id
    assert len(prescription.items) == 0


@pytest.mark.asyncio
async def test_create_prescription_with_items(prescription_service, test_patient, doctor_id):
    """Test creating prescription with multiple items."""
    items = [
        PrescriptionItemCreate(
            medicine_name="Arnica 30C",
            dosage="30C",
            frequency="3 times daily",
            duration="7 days",
            quantity=1.0,
            display_order=0,
        ),
        PrescriptionItemCreate(
            medicine_name="Belladonna 200C",
            dosage="200C",
            frequency="Twice daily",
            duration="5 days",
            quantity=1.0,
            instructions="Take before meals",
            display_order=1,
        ),
    ]

    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Fever with headache",
        doctors_notes="Patient presents with high fever",
        advice="Rest and hydration",
        items=items,
        status="issued",
    )

    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    assert prescription.id is not None
    assert len(prescription.items) == 2
    assert prescription.status == "issued"
    assert prescription.items[0].medicine_name == "Arnica 30C"
    assert prescription.items[1].medicine_name == "Belladonna 200C"
    assert prescription.items[0].display_order == 0
    assert prescription.items[1].display_order == 1


@pytest.mark.asyncio
async def test_create_prescription_with_visit(prescription_service, test_patient, doctor_id):
    """Test creating prescription linked to a visit."""
    visit_id = str(uuid4())  # Mock visit ID

    data = PrescriptionCreate(
        patient_id=test_patient.id,
        visit_id=visit_id,
        diagnosis="Chronic condition follow-up",
        status="draft",
    )

    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    assert prescription.visit_id == visit_id


# ===== Get Prescription Tests =====


@pytest.mark.asyncio
async def test_get_prescription(prescription_service, test_patient, doctor_id):
    """Test getting prescription by ID with items loaded."""
    # Create prescription with items
    items = [
        PrescriptionItemCreate(
            medicine_name="Test Medicine",
            dosage="30C",
            frequency="Daily",
        )
    ]
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        items=items,
        status="draft",
    )
    created = await prescription_service.create_prescription(data, prescribed_by=doctor_id)

    # Get prescription
    prescription = await prescription_service.get_prescription(created.id)

    assert prescription.id == created.id
    assert len(prescription.items) == 1
    assert prescription.items[0].medicine_name == "Test Medicine"


@pytest.mark.asyncio
async def test_get_prescription_not_found(prescription_service):
    """Test getting non-existent prescription raises 404."""
    with pytest.raises(HTTPException) as exc:
        await prescription_service.get_prescription(str(uuid4()))
    assert exc.value.status_code == 404


# ===== List Prescriptions Tests =====


@pytest.mark.asyncio
async def test_list_prescriptions_empty(prescription_service):
    """Test listing prescriptions when none exist."""
    prescriptions = await prescription_service.list_prescriptions()
    assert len(prescriptions) == 0


@pytest.mark.asyncio
async def test_list_prescriptions_by_patient(
    prescription_service, test_patient, doctor_id, db_session
):
    """Test listing prescriptions filtered by patient."""
    # Create another patient
    other_patient = Patient(
        id=str(uuid4()),
        tenant_id=prescription_service.tenant_id,
        full_name="Other Patient",
        is_active=True,
        created_by=doctor_id,
    )
    db_session.add(other_patient)
    await db_session.commit()

    # Create prescriptions for both patients
    for patient in [test_patient, other_patient]:
        data = PrescriptionCreate(
            patient_id=patient.id,
            diagnosis=f"Diagnosis for {patient.full_name}",
            status="issued",
        )
        await prescription_service.create_prescription(data, prescribed_by=doctor_id)

    # List prescriptions for test_patient only
    prescriptions = await prescription_service.list_prescriptions(
        patient_id=test_patient.id
    )

    assert len(prescriptions) == 1
    assert prescriptions[0].patient_id == test_patient.id


@pytest.mark.asyncio
async def test_list_prescriptions_by_status(prescription_service, test_patient, doctor_id):
    """Test listing prescriptions filtered by status."""
    # Create draft and issued prescriptions
    for status in ["draft", "issued", "issued"]:
        data = PrescriptionCreate(
            patient_id=test_patient.id,
            diagnosis="Test",
            status=status,
        )
        await prescription_service.create_prescription(data, prescribed_by=doctor_id)

    # List only issued prescriptions
    prescriptions = await prescription_service.list_prescriptions(status="issued")

    assert len(prescriptions) == 2
    assert all(p.status == "issued" for p in prescriptions)


@pytest.mark.asyncio
async def test_list_prescriptions_pagination(prescription_service, test_patient, doctor_id):
    """Test prescription pagination."""
    # Create 5 prescriptions
    for i in range(5):
        data = PrescriptionCreate(
            patient_id=test_patient.id,
            diagnosis=f"Diagnosis {i}",
            status="issued",
        )
        await prescription_service.create_prescription(data, prescribed_by=doctor_id)

    # Get first page
    page1 = await prescription_service.list_prescriptions(limit=2, offset=0)
    assert len(page1) == 2

    # Get second page
    page2 = await prescription_service.list_prescriptions(limit=2, offset=2)
    assert len(page2) == 2

    # Ensure different results
    assert page1[0].id != page2[0].id


# ===== Update Prescription Tests =====


@pytest.mark.asyncio
async def test_update_draft_prescription(prescription_service, test_patient, doctor_id):
    """Test updating a draft prescription."""
    # Create draft
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Initial diagnosis",
        status="draft",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Update
    update_data = PrescriptionUpdate(
        diagnosis="Updated diagnosis",
        advice="Updated advice",
    )
    updated = await prescription_service.update_prescription(
        prescription.id, update_data, updated_by=doctor_id
    )

    assert updated.diagnosis == "Updated diagnosis"
    assert updated.advice == "Updated advice"
    assert updated.updated_by == doctor_id


@pytest.mark.asyncio
async def test_update_issued_prescription_fails(
    prescription_service, test_patient, doctor_id
):
    """Test that updating issued prescription raises error."""
    # Create issued prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Try to update
    update_data = PrescriptionUpdate(diagnosis="Should fail")

    with pytest.raises(HTTPException) as exc:
        await prescription_service.update_prescription(
            prescription.id, update_data, updated_by=doctor_id
        )
    assert exc.value.status_code == 400
    assert "draft" in str(exc.value.detail).lower()


# ===== Void Prescription Tests =====


@pytest.mark.asyncio
async def test_void_prescription(prescription_service, test_patient, doctor_id):
    """Test voiding a prescription."""
    # Create prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Void it
    voided = await prescription_service.void_prescription(
        prescription.id, updated_by=doctor_id
    )

    assert voided.status == "voided"
    assert voided.updated_by == doctor_id


@pytest.mark.asyncio
async def test_void_already_voided_prescription_fails(
    prescription_service, test_patient, doctor_id
):
    """Test that voiding already voided prescription raises error."""
    # Create and void prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )
    await prescription_service.void_prescription(prescription.id, updated_by=doctor_id)

    # Try to void again
    with pytest.raises(HTTPException) as exc:
        await prescription_service.void_prescription(
            prescription.id, updated_by=doctor_id
        )
    assert exc.value.status_code == 400
    assert "already voided" in str(exc.value.detail).lower()


# ===== Prescription Item Tests =====


@pytest.mark.asyncio
async def test_add_item_to_draft_prescription(
    prescription_service, test_patient, doctor_id
):
    """Test adding item to draft prescription."""
    # Create draft prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="draft",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Add item
    item_data = PrescriptionItemCreate(
        medicine_name="New Medicine",
        dosage="30C",
        frequency="Daily",
    )
    item = await prescription_service.add_prescription_item(
        prescription.id, item_data, created_by=doctor_id
    )

    assert item.medicine_name == "New Medicine"
    assert item.prescription_id == prescription.id


@pytest.mark.asyncio
async def test_add_item_to_issued_prescription_fails(
    prescription_service, test_patient, doctor_id
):
    """Test that adding item to issued prescription fails."""
    # Create issued prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Try to add item
    item_data = PrescriptionItemCreate(
        medicine_name="Should Fail",
        dosage="30C",
        frequency="Daily",
    )

    with pytest.raises(HTTPException) as exc:
        await prescription_service.add_prescription_item(
            prescription.id, item_data, created_by=doctor_id
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_item_from_draft_prescription(
    prescription_service, test_patient, doctor_id
):
    """Test deleting item from draft prescription."""
    # Create draft prescription with item
    items = [
        PrescriptionItemCreate(
            medicine_name="Medicine to Delete",
            dosage="30C",
            frequency="Daily",
        )
    ]
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        items=items,
        status="draft",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    item_id = prescription.items[0].id

    # Delete item
    await prescription_service.delete_prescription_item(
        prescription.id, item_id, deleted_by=doctor_id
    )

    # Verify item deleted (need to get from DB, not cached prescription)
    from sqlalchemy import select
    result = await prescription_service.db.execute(
        select(PrescriptionItem).where(PrescriptionItem.prescription_id == prescription.id)
    )
    items = result.scalars().all()
    assert len(items) == 0


@pytest.mark.asyncio
async def test_delete_item_from_issued_prescription_fails(
    prescription_service, test_patient, doctor_id
):
    """Test that deleting item from issued prescription fails."""
    # Create issued prescription with item
    items = [
        PrescriptionItemCreate(
            medicine_name="Medicine",
            dosage="30C",
            frequency="Daily",
        )
    ]
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        items=items,
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    item_id = prescription.items[0].id

    # Try to delete item
    with pytest.raises(HTTPException) as exc:
        await prescription_service.delete_prescription_item(
            prescription.id, item_id, deleted_by=doctor_id
        )
    assert exc.value.status_code == 400


# ===== PDF Generation Test =====


@pytest.mark.asyncio
async def test_generate_pdf_for_issued_prescription(
    prescription_service, test_patient, doctor_id
):
    """Test generating PDF for issued prescription."""
    # Create issued prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="issued",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Generate PDF
    pdf_url = await prescription_service.generate_pdf(prescription.id)

    assert pdf_url is not None
    assert "prescription" in pdf_url.lower()

    # Verify prescription updated
    updated = await prescription_service.get_prescription(prescription.id)
    assert updated.pdf_url == pdf_url
    assert updated.pdf_generated_at is not None


@pytest.mark.asyncio
async def test_generate_pdf_for_draft_prescription_fails(
    prescription_service, test_patient, doctor_id
):
    """Test that generating PDF for draft prescription fails."""
    # Create draft prescription
    data = PrescriptionCreate(
        patient_id=test_patient.id,
        diagnosis="Test",
        status="draft",
    )
    prescription = await prescription_service.create_prescription(
        data, prescribed_by=doctor_id
    )

    # Try to generate PDF
    with pytest.raises(HTTPException) as exc:
        await prescription_service.generate_pdf(prescription.id)
    assert exc.value.status_code == 400
    assert "draft" in str(exc.value.detail).lower()
