"""Integration tests for prescription API routes."""

import pytest
from datetime import date
from uuid import uuid4

from app.shared.models import User, Tenant, Patient, Prescription


@pytest.fixture
async def test_tenant(db_session):
    """Create test tenant."""
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
async def second_tenant(db_session):
    """Create second tenant for isolation tests."""
    tenant = Tenant(
        id=str(uuid4()),
        name="Second Clinic",
        email="second@clinic.com",
        clinic_name="Second Clinic",
        specializations=["ayurveda"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_doctor(db_session, test_tenant):
    """Create test doctor user."""
    doctor = User(
        id=str(uuid4()),
        tenant_id=test_tenant.id,
        email="doctor@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Dr. Test Doctor",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def second_doctor(db_session, second_tenant):
    """Create doctor in second tenant."""
    doctor = User(
        id=str(uuid4()),
        tenant_id=second_tenant.id,
        email="doctor2@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Dr. Second Doctor",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def test_receptionist(db_session, test_tenant):
    """Create test receptionist user (non-doctor)."""
    receptionist = User(
        id=str(uuid4()),
        tenant_id=test_tenant.id,
        email="receptionist@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Test Receptionist",
        role="receptionist",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(receptionist)
    await db_session.commit()
    await db_session.refresh(receptionist)
    return receptionist


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
async def second_auth_headers(second_doctor, second_tenant):
    """Create authentication headers for second tenant."""
    from app.core.security import create_access_token

    token_data = {
        "sub": second_doctor.id,
        "email": second_doctor.email,
        "role": second_doctor.role,
        "tenant_id": second_tenant.id,
    }
    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def receptionist_headers(test_receptionist, test_tenant):
    """Create authentication headers for receptionist."""
    from app.core.security import create_access_token

    token_data = {
        "sub": test_receptionist.id,
        "email": test_receptionist.email,
        "role": test_receptionist.role,
        "tenant_id": test_tenant.id,
    }
    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_patient(db_session, test_tenant):
    """Create test patient."""
    patient = Patient(
        id=str(uuid4()),
        tenant_id=test_tenant.id,
        full_name="Test Patient",
        phone="01712345678",
        email="patient@test.com",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def second_patient(db_session, second_tenant):
    """Create patient in second tenant."""
    patient = Patient(
        id=str(uuid4()),
        tenant_id=second_tenant.id,
        full_name="Second Patient",
        phone="01712345679",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


# ===== Prescription Creation Tests =====


@pytest.mark.asyncio
async def test_create_prescription_success(client, auth_headers, test_patient):
    """Test successful prescription creation via API."""
    response = await client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "Common cold with fever",
            "doctors_notes": "Patient presents with mild symptoms",
            "advice": "Rest and hydration",
            "status": "draft",
            "items": [
                {
                    "medicine_name": "Arnica 30C",
                    "dosage": "30C",
                    "frequency": "3 times daily",
                    "duration": "7 days",
                    "quantity": 1.0,
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient.id
    assert data["diagnosis"] == "Common cold with fever"
    assert data["status"] == "draft"
    assert len(data["items"]) == 1
    assert data["items"][0]["medicine_name"] == "Arnica 30C"


@pytest.mark.asyncio
async def test_create_prescription_minimal(client, auth_headers, test_patient):
    """Test creating prescription with minimal data."""
    response = await client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "Test diagnosis",
            "status": "draft",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient.id
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_create_prescription_without_auth(client, test_patient):
    """Test prescription creation without authentication fails."""
    response = await client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "Test",
            "status": "draft",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_prescription_non_doctor_fails(
    client, receptionist_headers, test_patient
):
    """Test that non-doctors cannot create prescriptions."""
    response = await client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "Test",
            "status": "draft",
        },
        headers=receptionist_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_prescription_issued_directly(client, auth_headers, test_patient):
    """Test creating prescription in issued status directly."""
    response = await client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": test_patient.id,
            "diagnosis": "Diagnosis",
            "status": "issued",
            "items": [
                {
                    "medicine_name": "Test Medicine",
                    "dosage": "30C",
                    "frequency": "Daily",
                }
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "issued"


# ===== Prescription Listing Tests =====


@pytest.mark.asyncio
async def test_list_prescriptions(client, auth_headers, test_patient, db_session):
    """Test listing prescriptions."""
    # Create prescriptions via DB
    from app.shared.models import Prescription

    for i in range(3):
        prescription = Prescription(
            id=str(uuid4()),
            tenant_id=test_patient.tenant_id,
            patient_id=test_patient.id,
            prescribed_by=str(uuid4()),
            diagnosis=f"Diagnosis {i}",
            status="issued",
        )
        db_session.add(prescription)
    await db_session.commit()

    response = await client.get("/api/v1/prescriptions", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_prescriptions_filter_by_patient(
    client, auth_headers, test_patient, db_session
):
    """Test listing prescriptions filtered by patient."""
    from app.shared.models import Prescription

    # Create another patient
    other_patient = Patient(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        full_name="Other Patient",
        is_active=True,
    )
    db_session.add(other_patient)

    # Create prescriptions for both patients
    for patient in [test_patient, other_patient]:
        prescription = Prescription(
            id=str(uuid4()),
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            prescribed_by=str(uuid4()),
            diagnosis="Test",
            status="issued",
        )
        db_session.add(prescription)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/prescriptions?patient_id={test_patient.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == test_patient.id


@pytest.mark.asyncio
async def test_list_prescriptions_filter_by_status(
    client, auth_headers, test_patient, db_session
):
    """Test listing prescriptions filtered by status."""
    from app.shared.models import Prescription

    # Create prescriptions with different statuses
    for status in ["draft", "issued", "issued", "voided"]:
        prescription = Prescription(
            id=str(uuid4()),
            tenant_id=test_patient.tenant_id,
            patient_id=test_patient.id,
            prescribed_by=str(uuid4()),
            diagnosis="Test",
            status=status,
        )
        db_session.add(prescription)
    await db_session.commit()

    response = await client.get(
        "/api/v1/prescriptions?status=issued", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["status"] == "issued" for p in data)


# ===== Get Prescription Tests =====


@pytest.mark.asyncio
async def test_get_prescription(client, auth_headers, test_patient, db_session):
    """Test getting prescription by ID."""
    from app.shared.models import Prescription, PrescriptionItem

    # Create prescription with items
    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Test Diagnosis",
        status="issued",
    )
    db_session.add(prescription)

    item = PrescriptionItem(
        prescription_id=prescription.id,
        tenant_id=test_patient.tenant_id,
        medicine_name="Test Medicine",
        dosage="30C",
        frequency="Daily",
    )
    db_session.add(item)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/prescriptions/{prescription.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prescription.id
    assert data["diagnosis"] == "Test Diagnosis"
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_prescription_not_found(client, auth_headers):
    """Test getting non-existent prescription returns 404."""
    response = await client.get(
        f"/api/v1/prescriptions/{str(uuid4())}", headers=auth_headers
    )

    assert response.status_code == 404


# ===== Update Prescription Tests =====


@pytest.mark.asyncio
async def test_update_draft_prescription(client, auth_headers, test_patient, db_session):
    """Test updating a draft prescription."""
    from app.shared.models import Prescription

    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Original diagnosis",
        status="draft",
    )
    db_session.add(prescription)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/prescriptions/{prescription.id}",
        json={"diagnosis": "Updated diagnosis", "advice": "New advice"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["diagnosis"] == "Updated diagnosis"
    assert data["advice"] == "New advice"


@pytest.mark.asyncio
async def test_update_issued_prescription_fails(
    client, auth_headers, test_patient, db_session
):
    """Test that updating issued prescription fails."""
    from app.shared.models import Prescription

    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Original",
        status="issued",
    )
    db_session.add(prescription)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/prescriptions/{prescription.id}",
        json={"diagnosis": "Should fail"},
        headers=auth_headers,
    )

    assert response.status_code == 400


# ===== Void Prescription Tests =====


@pytest.mark.asyncio
async def test_void_prescription(client, auth_headers, test_patient, db_session):
    """Test voiding a prescription."""
    from app.shared.models import Prescription

    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Test",
        status="issued",
    )
    db_session.add(prescription)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/prescriptions/{prescription.id}/void", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "voided"


# ===== PDF Generation Tests =====


@pytest.mark.asyncio
async def test_generate_pdf(client, auth_headers, test_patient, db_session):
    """Test generating PDF for prescription."""
    from app.shared.models import Prescription

    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Test",
        status="issued",
    )
    db_session.add(prescription)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/prescriptions/{prescription.id}/generate-pdf", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "pdf_url" in data
    assert data["pdf_url"] is not None


# ===== Multi-Tenant Isolation Tests =====


@pytest.mark.asyncio
async def test_tenant_isolation_list(
    client, auth_headers, second_auth_headers, test_patient, second_patient, db_session
):
    """Test that tenants cannot see each other's prescriptions."""
    from app.shared.models import Prescription

    # Create prescription for first tenant
    prescription1 = Prescription(
        id=str(uuid4()),
        tenant_id=test_patient.tenant_id,
        patient_id=test_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Tenant 1 prescription",
        status="issued",
    )
    db_session.add(prescription1)

    # Create prescription for second tenant
    prescription2 = Prescription(
        id=str(uuid4()),
        tenant_id=second_patient.tenant_id,
        patient_id=second_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Tenant 2 prescription",
        status="issued",
    )
    db_session.add(prescription2)
    await db_session.commit()

    # First tenant should only see their prescription
    response1 = await client.get("/api/v1/prescriptions", headers=auth_headers)
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]["id"] == prescription1.id

    # Second tenant should only see their prescription
    response2 = await client.get("/api/v1/prescriptions", headers=second_auth_headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["id"] == prescription2.id


@pytest.mark.asyncio
async def test_tenant_isolation_get(
    client, auth_headers, second_auth_headers, test_patient, second_patient, db_session
):
    """Test that tenants cannot access each other's prescriptions by ID."""
    from app.shared.models import Prescription

    # Create prescription for second tenant
    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=second_patient.tenant_id,
        patient_id=second_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Tenant 2 prescription",
        status="issued",
    )
    db_session.add(prescription)
    await db_session.commit()

    # First tenant tries to access second tenant's prescription
    response = await client.get(
        f"/api/v1/prescriptions/{prescription.id}", headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_update(
    client, auth_headers, second_patient, db_session
):
    """Test that tenants cannot update other tenant's prescriptions."""
    from app.shared.models import Prescription

    # Create prescription for second tenant
    prescription = Prescription(
        id=str(uuid4()),
        tenant_id=second_patient.tenant_id,
        patient_id=second_patient.id,
        prescribed_by=str(uuid4()),
        diagnosis="Original",
        status="draft",
    )
    db_session.add(prescription)
    await db_session.commit()

    # First tenant tries to update second tenant's prescription
    response = await client.patch(
        f"/api/v1/prescriptions/{prescription.id}",
        json={"diagnosis": "Hacked!"},
        headers=auth_headers,
    )

    assert response.status_code == 404
