"""Integration tests for doctor API routes."""

import pytest
from datetime import date
from uuid import uuid4

from app.shared.models import User, Tenant, DoctorDegree, DoctorTraining


@pytest.fixture
async def test_tenant(db_session):
    """Create test tenant."""
    tenant = Tenant(
        id=str(uuid4()),
        name="Dr. Test",
        email="test@clinic.com",
        clinic_name="Test Clinic",
        clinic_address="123 Main St",
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
        password_hash="$2b$12$test_hash",
        role="doctor",
        full_name="Dr. John Doe",
        phone="+8801712345678",
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


# ===== Profile Tests =====


@pytest.mark.asyncio
async def test_get_doctor_profile(client, auth_headers, test_doctor, test_tenant):
    """Test getting doctor profile."""
    response = await client.get(
        "/api/v1/doctor/profile",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_doctor.id
    assert data["email"] == test_doctor.email
    assert data["full_name"] == test_doctor.full_name
    assert data["tenant_id"] == test_tenant.id
    assert data["clinic_name"] == test_tenant.clinic_name


@pytest.mark.asyncio
async def test_get_profile_without_auth(client):
    """Test getting profile without authentication."""
    response = await client.get("/api/v1/doctor/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    ["/api/v1/doctor/profile", "/api/v1/patients", "/api/v1/integrations/"],
)
async def test_platform_admin_cannot_access_tenant_clinical_endpoints(
    client, admin_access_token, path
):
    """Platform identity does not grant access to tenant clinical endpoints."""
    response = await client.get(
        path, headers={"Authorization": f"Bearer {admin_access_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_doctor_profile(client, auth_headers):
    """Test updating doctor profile."""
    response = await client.patch(
        "/api/v1/doctor/profile",
        json={
            "full_name": "Dr. Updated Name",
            "phone": "+8801798765432",
            "clinic_name": "Updated Clinic",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Dr. Updated Name"
    assert data["phone"] == "+8801798765432"
    assert data["clinic_name"] == "Updated Clinic"


@pytest.mark.asyncio
async def test_update_profile_partial(client, auth_headers, test_doctor):
    """Test partial profile update."""
    response = await client.patch(
        "/api/v1/doctor/profile",
        json={"clinic_name": "Only Clinic Updated"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["clinic_name"] == "Only Clinic Updated"
    assert data["full_name"] == test_doctor.full_name  # Unchanged


# ===== Degree Tests =====


@pytest.mark.asyncio
async def test_create_degree(client, auth_headers):
    """Test creating doctor degree."""
    response = await client.post(
        "/api/v1/doctor/degrees",
        json={
            "degree_type": "Bachelor",
            "degree_name": "BHMS",
            "specialization": "General Practice",
            "institution_name": "National Medical College",
            "institution_location": "Dhaka",
            "start_year": 2015,
            "completion_year": 2020,
            "display_order": 1,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["degree_name"] == "BHMS"
    assert data["degree_type"] == "Bachelor"
    assert data["is_verified"] is False


@pytest.mark.asyncio
async def test_create_degree_minimal(client, auth_headers):
    """Test creating degree with minimal fields."""
    response = await client.post(
        "/api/v1/doctor/degrees",
        json={
            "degree_type": "Bachelor",
            "degree_name": "BHMS",
            "institution_name": "Test College",
            "completion_year": 2020,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["degree_name"] == "BHMS"


@pytest.mark.asyncio
async def test_list_degrees(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test listing degrees."""
    # Create a degree first
    degree = DoctorDegree(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        degree_type="Bachelor",
        degree_name="BHMS",
        institution_name="Test College",
        completion_year=2020,
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(degree)
    await db_session.commit()

    response = await client.get(
        "/api/v1/doctor/degrees",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_degree(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test getting degree by ID."""
    degree = DoctorDegree(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        degree_type="Bachelor",
        degree_name="BHMS",
        institution_name="Test College",
        completion_year=2020,
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(degree)
    await db_session.commit()
    await db_session.refresh(degree)

    response = await client.get(
        f"/api/v1/doctor/degrees/{degree.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == degree.id
    assert data["degree_name"] == "BHMS"


@pytest.mark.asyncio
async def test_get_degree_not_found(client, auth_headers):
    """Test getting non-existent degree."""
    response = await client.get(
        "/api/v1/doctor/degrees/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_degree(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test updating degree."""
    degree = DoctorDegree(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        degree_type="Bachelor",
        degree_name="BHMS",
        institution_name="Old College",
        completion_year=2020,
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(degree)
    await db_session.commit()
    await db_session.refresh(degree)

    response = await client.patch(
        f"/api/v1/doctor/degrees/{degree.id}",
        json={
            "institution_name": "New College",
            "specialization": "Pediatrics",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["institution_name"] == "New College"
    assert data["specialization"] == "Pediatrics"


@pytest.mark.asyncio
async def test_delete_degree(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test deleting degree."""
    degree = DoctorDegree(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        degree_type="Bachelor",
        degree_name="BHMS",
        institution_name="Test College",
        completion_year=2020,
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(degree)
    await db_session.commit()
    await db_session.refresh(degree)

    response = await client.delete(
        f"/api/v1/doctor/degrees/{degree.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


# ===== Training Tests =====


@pytest.mark.asyncio
async def test_create_training(client, auth_headers):
    """Test creating doctor training."""
    response = await client.post(
        "/api/v1/doctor/trainings",
        json={
            "training_type": "Certification",
            "title": "Advanced Homeopathy",
            "provider": "National Institute",
            "description": "Advanced prescribing techniques",
            "skills": "Acute prescribing, Chronic management",
            "completion_date": "2023-06-15",
            "display_order": 1,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Advanced Homeopathy"
    assert data["training_type"] == "Certification"
    assert data["is_verified"] is False


@pytest.mark.asyncio
async def test_create_training_minimal(client, auth_headers):
    """Test creating training with minimal fields."""
    response = await client.post(
        "/api/v1/doctor/trainings",
        json={
            "training_type": "Workshop",
            "title": "Test Workshop",
            "provider": "Test Provider",
            "completion_date": "2023-06-01",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Workshop"


@pytest.mark.asyncio
async def test_list_trainings(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test listing trainings."""
    # Create a training first
    training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Workshop",
        title="Test Workshop",
        provider="Test Provider",
        completion_date=date(2023, 6, 1),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(training)
    await db_session.commit()

    response = await client.get(
        "/api/v1/doctor/trainings",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_trainings_filter_active(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test filtering expired trainings."""
    from datetime import timedelta

    today = date.today()

    # Create expired training
    expired_training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Certification",
        title="Expired Training",
        provider="Provider",
        completion_date=today - timedelta(days=400),
        expiry_date=today - timedelta(days=1),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    # Create active training
    active_training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Workshop",
        title="Active Training",
        provider="Provider",
        completion_date=today - timedelta(days=30),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add_all([expired_training, active_training])
    await db_session.commit()

    # Get only active
    response = await client.get(
        "/api/v1/doctor/trainings?active_only=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    titles = {t["title"] for t in data}
    assert "Expired Training" not in titles


@pytest.mark.asyncio
async def test_get_training(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test getting training by ID."""
    training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Workshop",
        title="Test Workshop",
        provider="Test Provider",
        completion_date=date(2023, 6, 1),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(training)
    await db_session.commit()
    await db_session.refresh(training)

    response = await client.get(
        f"/api/v1/doctor/trainings/{training.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == training.id
    assert data["title"] == "Test Workshop"


@pytest.mark.asyncio
async def test_update_training(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test updating training."""
    training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Workshop",
        title="Old Title",
        provider="Old Provider",
        completion_date=date(2023, 6, 1),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(training)
    await db_session.commit()
    await db_session.refresh(training)

    response = await client.patch(
        f"/api/v1/doctor/trainings/{training.id}",
        json={
            "title": "New Title",
            "skills": "New skills",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["skills"] == "New skills"


@pytest.mark.asyncio
async def test_delete_training(client, auth_headers, db_session, test_doctor, test_tenant):
    """Test deleting training."""
    training = DoctorTraining(
        user_id=test_doctor.id,
        tenant_id=test_tenant.id,
        training_type="Workshop",
        title="Test Workshop",
        provider="Test Provider",
        completion_date=date(2023, 6, 1),
        is_verified=False,
        created_by=test_doctor.id,
        updated_by=test_doctor.id,
    )
    db_session.add(training)
    await db_session.commit()
    await db_session.refresh(training)

    response = await client.delete(
        f"/api/v1/doctor/trainings/{training.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
