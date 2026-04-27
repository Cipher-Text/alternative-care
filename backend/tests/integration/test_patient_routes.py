"""Integration tests for patient API routes."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.shared.models import User, Tenant, Patient


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


# ===== Patient Creation Tests =====


@pytest.mark.asyncio
async def test_create_patient_success(client, auth_headers):
    """Test successful patient creation via API."""
    response = await client.post(
        "/api/v1/patients",
        json={
            "full_name": "John Doe",
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "blood_group": "O+",
            "phone": "+8801712345678",
            "email": "john@example.com",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert data["gender"] == "male"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_patient_minimal(client, auth_headers):
    """Test creating patient with only required field."""
    response = await client.post(
        "/api/v1/patients",
        json={"full_name": "Jane Doe"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_create_patient_without_auth(client):
    """Test patient creation without authentication."""
    response = await client.post(
        "/api/v1/patients",
        json={"full_name": "Test Patient"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_patient_invalid_data(client, auth_headers):
    """Test patient creation with invalid data."""
    response = await client.post(
        "/api/v1/patients",
        json={
            "full_name": "",  # Empty name
        },
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error


# ===== Patient Listing Tests =====


@pytest.mark.asyncio
async def test_list_patients(client, auth_headers, test_patient):
    """Test listing patients."""
    response = await client.get(
        "/api/v1/patients",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_patients_with_search(client, auth_headers, test_patient):
    """Test searching patients."""
    response = await client.get(
        "/api/v1/patients?search=Test",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Test" in data[0]["full_name"]


@pytest.mark.asyncio
async def test_list_patients_filter_active(client, auth_headers, test_patient):
    """Test filtering patients by active status."""
    response = await client.get(
        "/api/v1/patients?is_active=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    for patient in data:
        assert patient["is_active"] is True


@pytest.mark.asyncio
async def test_list_patients_pagination(client, auth_headers, test_patient):
    """Test pagination."""
    response = await client.get(
        "/api/v1/patients?limit=5&offset=0",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


# ===== Patient Count Tests =====


@pytest.mark.asyncio
async def test_get_patient_count(client, auth_headers, test_patient):
    """Test getting patient count."""
    response = await client.get(
        "/api/v1/patients/count",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 1


# ===== Patient Retrieval Tests =====


@pytest.mark.asyncio
async def test_get_patient(client, auth_headers, test_patient):
    """Test getting patient by ID."""
    response = await client.get(
        f"/api/v1/patients/{test_patient.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_patient.id
    assert data["full_name"] == test_patient.full_name


@pytest.mark.asyncio
async def test_get_patient_not_found(client, auth_headers):
    """Test getting non-existent patient."""
    response = await client.get(
        f"/api/v1/patients/{str(uuid4())}",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ===== Patient Update Tests =====


@pytest.mark.asyncio
async def test_update_patient(client, auth_headers, test_patient):
    """Test updating patient."""
    response = await client.patch(
        f"/api/v1/patients/{test_patient.id}",
        json={
            "full_name": "Updated Name",
            "phone": "+8801798765432",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "+8801798765432"


@pytest.mark.asyncio
async def test_update_patient_partial(client, auth_headers, test_patient):
    """Test partial update."""
    response = await client.patch(
        f"/api/v1/patients/{test_patient.id}",
        json={"phone": "+8801611111111"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+8801611111111"
    # Name should remain unchanged
    assert data["full_name"] == test_patient.full_name


# ===== Patient Deletion Tests =====


@pytest.mark.asyncio
async def test_delete_patient(client, auth_headers, test_patient):
    """Test soft deleting patient."""
    response = await client.delete(
        f"/api/v1/patients/{test_patient.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


# ===== Patient Tag Tests =====


@pytest.mark.asyncio
async def test_create_patient_tag(client, auth_headers, test_patient):
    """Test creating patient tag."""
    response = await client.post(
        f"/api/v1/patients/{test_patient.id}/tags",
        json={
            "tag_type": "chronic",
            "tag_value": "Diabetes",
            "notes": "Type 2, managed with diet",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tag_type"] == "chronic"
    assert data["tag_value"] == "Diabetes"
    assert data["patient_id"] == test_patient.id


@pytest.mark.asyncio
async def test_list_patient_tags(client, auth_headers, test_patient, db_session):
    """Test listing patient tags."""
    # Create a tag first
    from app.shared.models import PatientTag

    tag = PatientTag(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        tag_type="allergy",
        tag_value="Penicillin",
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(tag)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/patients/{test_patient.id}/tags",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_update_patient_tag(client, auth_headers, test_patient, db_session):
    """Test updating patient tag."""
    # Create a tag first
    from app.shared.models import PatientTag

    tag = PatientTag(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        tag_type="chronic",
        tag_value="Old Value",
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    response = await client.patch(
        f"/api/v1/patients/tags/{tag.id}",
        json={
            "tag_value": "New Value",
            "notes": "Updated",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tag_value"] == "New Value"
    assert data["notes"] == "Updated"


@pytest.mark.asyncio
async def test_delete_patient_tag(client, auth_headers, test_patient, db_session):
    """Test deleting patient tag."""
    # Create a tag first
    from app.shared.models import PatientTag

    tag = PatientTag(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        tag_type="treatment",
        tag_value="To Delete",
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    response = await client.delete(
        f"/api/v1/patients/tags/{tag.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


# ===== Patient Diagnosis Tests =====


@pytest.mark.asyncio
async def test_create_patient_diagnosis(client, auth_headers, test_patient):
    """Test creating patient diagnosis."""
    response = await client.post(
        f"/api/v1/patients/{test_patient.id}/diagnoses",
        json={
            "description": "Chronic bronchitis",
            "icd_code": "J42",
            "diagnosed_at": "2026-04-15",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Chronic bronchitis"
    assert data["icd_code"] == "J42"
    assert data["patient_id"] == test_patient.id
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_patient_diagnoses(client, auth_headers, test_patient, db_session):
    """Test listing patient diagnoses."""
    # Create a diagnosis first
    from app.shared.models import PatientDiagnosis

    diagnosis = PatientDiagnosis(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        description="Test diagnosis",
        diagnosed_at=date.today(),
        is_active=True,
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(diagnosis)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/patients/{test_patient.id}/diagnoses",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_patient_diagnoses_filter_active(client, auth_headers, test_patient, db_session):
    """Test filtering diagnoses by active status."""
    # Create active and inactive diagnoses
    from app.shared.models import PatientDiagnosis

    active_diag = PatientDiagnosis(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        description="Active diagnosis",
        diagnosed_at=date.today(),
        is_active=True,
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    inactive_diag = PatientDiagnosis(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        description="Inactive diagnosis",
        diagnosed_at=date.today() - timedelta(days=30),
        is_active=False,
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add_all([active_diag, inactive_diag])
    await db_session.commit()

    # Filter active only
    response = await client.get(
        f"/api/v1/patients/{test_patient.id}/diagnoses?active_only=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    for diag in data:
        assert diag["is_active"] is True


@pytest.mark.asyncio
async def test_update_patient_diagnosis(client, auth_headers, test_patient, db_session):
    """Test updating patient diagnosis."""
    # Create a diagnosis first
    from app.shared.models import PatientDiagnosis

    diagnosis = PatientDiagnosis(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        description="Old description",
        diagnosed_at=date.today(),
        is_active=True,
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(diagnosis)
    await db_session.commit()
    await db_session.refresh(diagnosis)

    response = await client.patch(
        f"/api/v1/patients/diagnoses/{diagnosis.id}",
        json={
            "description": "New description",
            "icd_code": "A00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New description"
    assert data["icd_code"] == "A00"


@pytest.mark.asyncio
async def test_delete_patient_diagnosis(client, auth_headers, test_patient, db_session):
    """Test soft deleting patient diagnosis."""
    # Create a diagnosis first
    from app.shared.models import PatientDiagnosis

    diagnosis = PatientDiagnosis(
        patient_id=test_patient.id,
        tenant_id=test_patient.tenant_id,
        description="To delete",
        diagnosed_at=date.today(),
        is_active=True,
        created_by=str(uuid4()),
        updated_by=str(uuid4()),
    )
    db_session.add(diagnosis)
    await db_session.commit()
    await db_session.refresh(diagnosis)

    response = await client.delete(
        f"/api/v1/patients/diagnoses/{diagnosis.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


# ===== Multi-Tenant Isolation Tests =====


@pytest.mark.asyncio
async def test_patient_tenant_isolation(client, db_session):
    """Test patients are isolated by tenant."""
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

    # Create doctors for each tenant
    doctor1 = User(
        id=str(uuid4()),
        tenant_id=tenant1.id,
        email="doctor1@test.com",
        password_hash="$2b$12$test_hash",
        full_name="Dr. One",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    doctor2 = User(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        email="doctor2@test.com",
        password_hash="$2b$12$test_hash",
        full_name="Dr. Two",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add_all([doctor1, doctor2])
    await db_session.commit()

    # Create patient in tenant1
    patient = Patient(
        id=str(uuid4()),
        tenant_id=tenant1.id,
        full_name="Tenant 1 Patient",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.commit()

    # Create token for tenant1
    from app.core.security import create_access_token

    token1 = create_access_token({
        "sub": doctor1.id,
        "email": doctor1.email,
        "role": doctor1.role,
        "tenant_id": tenant1.id,
    })
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Create token for tenant2
    token2 = create_access_token({
        "sub": doctor2.id,
        "email": doctor2.email,
        "role": doctor2.role,
        "tenant_id": tenant2.id,
    })
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Tenant1 should see the patient
    response1 = await client.get("/api/v1/patients", headers=headers1)
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1

    # Tenant2 should NOT see the patient
    response2 = await client.get("/api/v1/patients", headers=headers2)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 0

    # Tenant2 should NOT be able to access tenant1's patient by ID
    response3 = await client.get(f"/api/v1/patients/{patient.id}", headers=headers2)
    assert response3.status_code == 404
