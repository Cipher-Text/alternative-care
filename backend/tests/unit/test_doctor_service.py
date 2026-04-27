"""Unit tests for doctor service."""

import pytest
from datetime import date
from uuid import uuid4

from fastapi import HTTPException

from app.modules.doctor.service import DoctorService
from app.shared.models import User, Tenant, DoctorDegree, DoctorTraining
from app.shared.schemas import (
    DoctorProfileUpdate,
    DoctorDegreeCreate,
    DoctorDegreeUpdate,
    DoctorTrainingCreate,
    DoctorTrainingUpdate,
)


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
def doctor_service(db_session, test_doctor, test_tenant):
    """Create doctor service instance."""
    return DoctorService(
        db=db_session, user_id=test_doctor.id, tenant_id=test_tenant.id
    )


# ===== Profile Tests =====


@pytest.mark.asyncio
async def test_get_profile(doctor_service, test_doctor, test_tenant):
    """Test getting doctor profile."""
    profile = await doctor_service.get_profile()

    assert profile["id"] == test_doctor.id
    assert profile["email"] == test_doctor.email
    assert profile["full_name"] == test_doctor.full_name
    assert profile["tenant_id"] == test_tenant.id
    assert profile["clinic_name"] == test_tenant.clinic_name
    assert profile["specializations"] == test_tenant.specializations


@pytest.mark.asyncio
async def test_update_profile(doctor_service, test_doctor):
    """Test updating doctor profile."""
    update_data = DoctorProfileUpdate(
        full_name="Dr. Updated Name",
        phone="+8801798765432",
        clinic_name="Updated Clinic",
        clinic_address="456 New St",
    )

    profile = await doctor_service.update_profile(update_data, updated_by=test_doctor.id)

    assert profile["full_name"] == "Dr. Updated Name"
    assert profile["phone"] == "+8801798765432"
    assert profile["clinic_name"] == "Updated Clinic"
    assert profile["clinic_address"] == "456 New St"


@pytest.mark.asyncio
async def test_update_profile_partial(doctor_service, test_doctor):
    """Test partial profile update."""
    update_data = DoctorProfileUpdate(clinic_name="Only Clinic Updated")

    profile = await doctor_service.update_profile(update_data, updated_by=test_doctor.id)

    assert profile["clinic_name"] == "Only Clinic Updated"
    assert profile["full_name"] == test_doctor.full_name  # Unchanged


# ===== Degree Tests =====


@pytest.mark.asyncio
async def test_create_degree(doctor_service, test_doctor):
    """Test creating doctor degree."""
    degree_data = DoctorDegreeCreate(
        degree_type="Bachelor",
        degree_name="BHMS",
        specialization="General Practice",
        institution_name="National Medical College",
        institution_location="Dhaka",
        start_year=2015,
        completion_year=2020,
        display_order=1,
    )

    degree = await doctor_service.create_degree(degree_data, created_by=test_doctor.id)

    assert degree.degree_name == "BHMS"
    assert degree.degree_type == "Bachelor"
    assert degree.user_id == test_doctor.id
    assert degree.is_verified is False


@pytest.mark.asyncio
async def test_list_degrees_empty(doctor_service):
    """Test listing degrees when none exist."""
    degrees = await doctor_service.list_degrees()
    assert degrees == []


@pytest.mark.asyncio
async def test_list_degrees(doctor_service, test_doctor):
    """Test listing degrees."""
    # Create 2 degrees
    await doctor_service.create_degree(
        DoctorDegreeCreate(
            degree_type="Bachelor",
            degree_name="BHMS",
            institution_name="College A",
            completion_year=2020,
            display_order=1,
        ),
        created_by=test_doctor.id,
    )
    await doctor_service.create_degree(
        DoctorDegreeCreate(
            degree_type="Master",
            degree_name="MD (Homeopathy)",
            institution_name="College B",
            completion_year=2022,
            display_order=0,
        ),
        created_by=test_doctor.id,
    )

    degrees = await doctor_service.list_degrees()

    assert len(degrees) == 2
    # Ordered by display_order first
    assert degrees[0].degree_name == "MD (Homeopathy)"


@pytest.mark.asyncio
async def test_get_degree(doctor_service, test_doctor):
    """Test getting degree by ID."""
    created = await doctor_service.create_degree(
        DoctorDegreeCreate(
            degree_type="Bachelor",
            degree_name="BHMS",
            institution_name="Test College",
            completion_year=2020,
        ),
        created_by=test_doctor.id,
    )

    degree = await doctor_service.get_degree(created.id)

    assert degree.id == created.id
    assert degree.degree_name == "BHMS"


@pytest.mark.asyncio
async def test_get_degree_not_found(doctor_service):
    """Test getting non-existent degree raises 404."""
    with pytest.raises(HTTPException) as exc:
        await doctor_service.get_degree(99999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_degree(doctor_service, test_doctor):
    """Test updating degree."""
    degree = await doctor_service.create_degree(
        DoctorDegreeCreate(
            degree_type="Bachelor",
            degree_name="BHMS",
            institution_name="Old College",
            completion_year=2020,
        ),
        created_by=test_doctor.id,
    )

    update_data = DoctorDegreeUpdate(
        institution_name="New College",
        specialization="Pediatrics",
    )
    updated = await doctor_service.update_degree(
        degree.id, update_data, updated_by=test_doctor.id
    )

    assert updated.institution_name == "New College"
    assert updated.specialization == "Pediatrics"
    assert updated.degree_name == "BHMS"  # Unchanged


@pytest.mark.asyncio
async def test_delete_degree(doctor_service, test_doctor, db_session):
    """Test deleting degree."""
    from sqlalchemy import select

    degree = await doctor_service.create_degree(
        DoctorDegreeCreate(
            degree_type="Bachelor",
            degree_name="BHMS",
            institution_name="Test College",
            completion_year=2020,
        ),
        created_by=test_doctor.id,
    )

    await doctor_service.delete_degree(degree.id)

    # Verify deleted
    result = await db_session.execute(
        select(DoctorDegree).where(DoctorDegree.id == degree.id)
    )
    assert result.scalar_one_or_none() is None


# ===== Training Tests =====


@pytest.mark.asyncio
async def test_create_training(doctor_service, test_doctor):
    """Test creating doctor training."""
    training_data = DoctorTrainingCreate(
        training_type="Certification",
        title="Advanced Homeopathy",
        provider="National Institute",
        description="Advanced prescribing techniques",
        skills="Acute prescribing, Chronic management",
        completion_date=date(2023, 6, 15),
        display_order=1,
    )

    training = await doctor_service.create_training(
        training_data, created_by=test_doctor.id
    )

    assert training.title == "Advanced Homeopathy"
    assert training.training_type == "Certification"
    assert training.user_id == test_doctor.id
    assert training.is_verified is False


@pytest.mark.asyncio
async def test_list_trainings_empty(doctor_service):
    """Test listing trainings when none exist."""
    trainings = await doctor_service.list_trainings()
    assert trainings == []


@pytest.mark.asyncio
async def test_list_trainings(doctor_service, test_doctor):
    """Test listing trainings."""
    # Create 2 trainings
    await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Workshop",
            title="Workshop A",
            provider="Provider A",
            completion_date=date(2023, 1, 1),
            display_order=1,
        ),
        created_by=test_doctor.id,
    )
    await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Certification",
            title="Certification B",
            provider="Provider B",
            completion_date=date(2023, 6, 1),
            display_order=0,
        ),
        created_by=test_doctor.id,
    )

    trainings = await doctor_service.list_trainings()

    assert len(trainings) == 2
    # Ordered by display_order first
    assert trainings[0].title == "Certification B"


@pytest.mark.asyncio
async def test_list_trainings_filter_active(doctor_service, test_doctor):
    """Test filtering expired trainings."""
    from datetime import timedelta

    today = date.today()

    # Create active training (no expiry)
    await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Workshop",
            title="Active Training",
            provider="Provider A",
            completion_date=today - timedelta(days=30),
        ),
        created_by=test_doctor.id,
    )

    # Create expired training
    await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Certification",
            title="Expired Training",
            provider="Provider B",
            completion_date=today - timedelta(days=400),
            expiry_date=today - timedelta(days=1),
        ),
        created_by=test_doctor.id,
    )

    # Create future expiry training
    await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Certification",
            title="Valid Training",
            provider="Provider C",
            completion_date=today - timedelta(days=200),
            expiry_date=today + timedelta(days=100),
        ),
        created_by=test_doctor.id,
    )

    # Get all trainings
    all_trainings = await doctor_service.list_trainings(active_only=False)
    assert len(all_trainings) == 3

    # Get only active trainings
    active_trainings = await doctor_service.list_trainings(active_only=True)
    assert len(active_trainings) == 2
    titles = {t.title for t in active_trainings}
    assert "Expired Training" not in titles


@pytest.mark.asyncio
async def test_get_training(doctor_service, test_doctor):
    """Test getting training by ID."""
    created = await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Workshop",
            title="Test Workshop",
            provider="Test Provider",
            completion_date=date(2023, 6, 1),
        ),
        created_by=test_doctor.id,
    )

    training = await doctor_service.get_training(created.id)

    assert training.id == created.id
    assert training.title == "Test Workshop"


@pytest.mark.asyncio
async def test_get_training_not_found(doctor_service):
    """Test getting non-existent training raises 404."""
    with pytest.raises(HTTPException) as exc:
        await doctor_service.get_training(99999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_training(doctor_service, test_doctor):
    """Test updating training."""
    training = await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Workshop",
            title="Old Title",
            provider="Old Provider",
            completion_date=date(2023, 6, 1),
        ),
        created_by=test_doctor.id,
    )

    update_data = DoctorTrainingUpdate(
        title="New Title",
        skills="New skills learned",
    )
    updated = await doctor_service.update_training(
        training.id, update_data, updated_by=test_doctor.id
    )

    assert updated.title == "New Title"
    assert updated.skills == "New skills learned"
    assert updated.provider == "Old Provider"  # Unchanged


@pytest.mark.asyncio
async def test_delete_training(doctor_service, test_doctor, db_session):
    """Test deleting training."""
    from sqlalchemy import select

    training = await doctor_service.create_training(
        DoctorTrainingCreate(
            training_type="Workshop",
            title="Test Workshop",
            provider="Test Provider",
            completion_date=date(2023, 6, 1),
        ),
        created_by=test_doctor.id,
    )

    await doctor_service.delete_training(training.id)

    # Verify deleted
    result = await db_session.execute(
        select(DoctorTraining).where(DoctorTraining.id == training.id)
    )
    assert result.scalar_one_or_none() is None
