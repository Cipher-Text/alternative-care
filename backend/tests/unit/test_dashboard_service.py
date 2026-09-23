"""Unit tests for dashboard service layer."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.service import DashboardService
from app.shared.models import (
    Tenant,
    Patient,
    Appointment,
    Visit,
    Payment,
    Invoice,
    Prescription,
    PrescriptionItem,
    PatientDiagnosis,
)


@pytest.fixture
async def test_tenant_dashboard(db_session: AsyncSession, test_division, test_district):
    """Create test tenant for dashboard tests."""
    from app.shared.models import Tenant

    tenant = Tenant(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Dr. Test Doctor",
        email="doctor@test.com",
        phone="+8801712345678",
        clinic_name="Test Clinic",
        clinic_address="123 Test St",
        division_id=test_division.id,
        district_id=test_district.id,
        specializations=["homeopathy"],
        license_number="TEST123",
        is_verified=True,
        is_approved=True,
        is_active=True,
        plan="pro",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
def tenant_data(test_tenant_dashboard):
    """Test tenant data."""
    return {
        "id": test_tenant_dashboard.id,
        "name": test_tenant_dashboard.name,
        "email": test_tenant_dashboard.email,
        "plan": test_tenant_dashboard.plan,
    }


@pytest.fixture
async def user_id(db_session: AsyncSession, test_tenant_dashboard) -> str:
    """Create a real doctor User row and return its id.

    Visit.doctor_id, Appointment.doctor_id, and Prescription.doctor_id are
    real FKs to users.id — a bare UUID string satisfies created_by/updated_by
    (plain audit columns, not FK'd) but not those.
    """
    from app.core.security import get_password_hash
    from app.shared.models import User

    user = User(
        id="660e8400-e29b-41d4-a716-446655440000",
        tenant_id=test_tenant_dashboard.id,
        email="dashboard-doctor@test.com",
        password_hash=get_password_hash("TestPass123"),
        role="doctor",
        full_name="Dr. Dashboard Test",
        phone="+8801700000001",
        language="en",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id


@pytest.fixture
async def dashboard_service(
    db_session: AsyncSession, test_tenant_dashboard
) -> DashboardService:
    """Create dashboard service instance."""
    return DashboardService(db=db_session, tenant_id=test_tenant_dashboard.id)


# ===== Overview Dashboard Tests =====


@pytest.mark.asyncio
async def test_get_overview(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting overview statistics."""
    # Create test data
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)

    payment = Payment(
        id="payment1",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=1000.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        payment_date=date.today(),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(payment)

    await db_session.commit()

    # Get overview
    overview = await dashboard_service.get_overview()

    assert overview.total_patients == 1
    assert overview.total_revenue == 1000.0
    assert overview.period_start is not None
    assert overview.period_end is not None


@pytest.mark.asyncio
async def test_get_overview_empty(dashboard_service: DashboardService):
    """Test getting overview with no data."""
    overview = await dashboard_service.get_overview()

    assert overview.total_patients == 0
    assert overview.total_revenue == 0.0
    assert overview.total_appointments == 0
    assert overview.total_visits == 0
    assert overview.total_prescriptions == 0


# ===== Financial Analytics Tests =====


@pytest.mark.asyncio
async def test_get_financial_analytics(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting financial analytics."""
    # Create test payments
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)

    # Cash payment
    payment1 = Payment(
        id="payment1",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=1000.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        payment_date=date.today(),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(payment1)

    # bKash payment
    payment2 = Payment(
        id="payment2",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=2000.0,
        currency="BDT",
        payment_method="bkash",
        status="paid",
        payment_date=date.today(),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(payment2)

    # Pending payment
    payment3 = Payment(
        id="payment3",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=500.0,
        currency="BDT",
        payment_method="cash",
        status="pending",
        payment_date=date.today(),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(payment3)

    await db_session.commit()

    # Get financial analytics
    analytics = await dashboard_service.get_financial_analytics()

    assert analytics.total_payments == 3
    assert analytics.total_revenue == 3500.0
    assert analytics.paid_amount == 3000.0
    assert analytics.pending_amount == 500.0
    assert analytics.revenue_by_method.cash == 1000.0
    assert analytics.revenue_by_method.bkash == 2000.0
    assert analytics.average_payment == 3500.0 / 3


@pytest.mark.asyncio
async def test_get_financial_analytics_with_date_range(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test filtering financial analytics by date range."""
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)

    # Old payment (outside range)
    old_payment = Payment(
        id="old_payment",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=1000.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        payment_date=date.today() - timedelta(days=60),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(old_payment)

    # Recent payment (within range)
    recent_payment = Payment(
        id="recent_payment",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=2000.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        payment_date=date.today() - timedelta(days=5),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(recent_payment)

    await db_session.commit()

    # Filter last 30 days
    date_from = date.today() - timedelta(days=30)
    analytics = await dashboard_service.get_financial_analytics(
        date_from=date_from, date_to=date.today()
    )

    assert analytics.total_payments == 1
    assert analytics.total_revenue == 2000.0


# ===== Patient Analytics Tests =====


@pytest.mark.asyncio
async def test_get_patient_analytics(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting patient analytics."""
    # Create test patients with different demographics
    patient1 = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 5, 15),  # Age ~46
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient1)

    patient2 = Patient(
        id="patient2",
        tenant_id=tenant_data["id"],
        full_name="Jane Smith",
        date_of_birth=date(1995, 8, 20),  # Age ~30
        gender="female",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient2)
    # Flush so patient1/patient2 exist before rows that FK-reference them —
    # Visit/PatientDiagnosis have no ORM relationship() to Patient, so the
    # flush's automatic dependency ordering doesn't cover them.
    await db_session.flush()

    # Add diagnosis
    diagnosis = PatientDiagnosis(
        tenant_id=tenant_data["id"],
        patient_id=patient1.id,
        description="Headache",
        diagnosed_at=date.today(),
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(diagnosis)

    # Add visit for active patient count
    visit = Visit(
        id="visit1",
        tenant_id=tenant_data["id"],
        patient_id=patient1.id,
        doctor_id=user_id,
        visit_date=(datetime.utcnow() - timedelta(days=5)).date(),
        visit_type="consultation",
        chief_complaint="Headache",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(visit)

    await db_session.commit()

    # Get patient analytics
    analytics = await dashboard_service.get_patient_analytics()

    assert analytics.total_patients == 2
    assert analytics.active_patients == 1  # patient1 had visit in last 30 days
    assert analytics.demographics.male == 1
    assert analytics.demographics.female == 1
    assert len(analytics.top_diagnoses) == 1
    assert analytics.top_diagnoses[0].diagnosis == "Headache"
    assert analytics.top_diagnoses[0].count == 1


@pytest.mark.asyncio
async def test_patient_age_distribution(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test patient age distribution calculation."""
    # Create patients in different age groups
    patients = [
        Patient(
            id=f"patient{i}",
            tenant_id=tenant_data["id"],
            full_name=f"Patient {i}",
            date_of_birth=birthdate,
            gender="male" if i % 2 == 0 else "female",
            created_by=user_id,
            updated_by=user_id,
        )
        for i, birthdate in enumerate([
            date.today() - timedelta(days=365 * 10),  # Age 10 (0-18)
            date.today() - timedelta(days=365 * 25),  # Age 25 (19-35)
            date.today() - timedelta(days=365 * 40),  # Age 40 (36-50)
            date.today() - timedelta(days=365 * 60),  # Age 60 (51-65)
            date.today() - timedelta(days=365 * 70),  # Age 70 (66+)
        ])
    ]

    for patient in patients:
        db_session.add(patient)
    await db_session.commit()

    analytics = await dashboard_service.get_patient_analytics()

    assert analytics.age_distribution.age_0_18 == 1
    assert analytics.age_distribution.age_19_35 == 1
    assert analytics.age_distribution.age_36_50 == 1
    assert analytics.age_distribution.age_51_65 == 1
    assert analytics.age_distribution.age_66_plus == 1


# ===== Appointment Analytics Tests =====


@pytest.mark.asyncio
async def test_get_appointment_analytics(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting appointment analytics."""
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)
    # Flush so patient exists before Appointment rows that FK-reference it —
    # Appointment has no ORM relationship() to Patient, so the flush's
    # automatic dependency ordering doesn't cover it.
    await db_session.flush()

    # Create appointments with different statuses
    appt1 = Appointment(
        id="appt1",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        doctor_id=user_id,
        appointment_date=(datetime.utcnow() + timedelta(days=1)).date(),
        appointment_time=time(10, 0),
        status="scheduled",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(appt1)

    appt2 = Appointment(
        id="appt2",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        doctor_id=user_id,
        appointment_date=(datetime.utcnow() - timedelta(days=1)).date(),
        appointment_time=time(10, 0),
        status="completed",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(appt2)

    appt3 = Appointment(
        id="appt3",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        doctor_id=user_id,
        appointment_date=(datetime.utcnow() + timedelta(days=2)).date(),
        appointment_time=time(10, 0),
        status="cancelled",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(appt3)

    await db_session.commit()

    # Get appointment analytics
    analytics = await dashboard_service.get_appointment_analytics()

    assert analytics.total_appointments == 3
    assert analytics.upcoming_appointments == 1  # Only scheduled/confirmed
    assert analytics.completed_appointments == 1
    assert analytics.cancellation_rate == pytest.approx(33.33, rel=0.1)  # 1/3
    assert analytics.by_status.scheduled == 1
    assert analytics.by_status.completed == 1
    assert analytics.by_status.cancelled == 1
    # Appointment has no appointment_type column (only free-text 'reason') —
    # by_type is a documented placeholder in DashboardService.get_appointment_analytics
    # until that field is added.
    assert analytics.by_type.consultation == 0
    assert analytics.by_type.follow_up == 0


# ===== Visit Analytics Tests =====


@pytest.mark.asyncio
async def test_get_visit_analytics(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting visit analytics."""
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)
    # Flush so patient exists before Visit rows that FK-reference it — Visit
    # has no ORM relationship() to Patient, so the flush's automatic
    # dependency ordering doesn't cover it.
    await db_session.flush()

    # Create visits with different types
    visit1 = Visit(
        id="visit1",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        doctor_id=user_id,
        visit_date=datetime.utcnow().date(),
        visit_type="consultation",
        chief_complaint="Headache",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(visit1)

    visit2 = Visit(
        id="visit2",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        doctor_id=user_id,
        visit_date=datetime.utcnow().date(),
        visit_type="follow_up",
        chief_complaint="Fever",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(visit2)

    await db_session.commit()

    # Get visit analytics
    analytics = await dashboard_service.get_visit_analytics()

    assert analytics.total_visits == 2
    assert analytics.average_visits_per_patient == 2.0  # 2 visits / 1 patient
    assert analytics.by_type.consultation == 1
    assert analytics.by_type.follow_up == 1
    assert len(analytics.top_complaints) == 2


# ===== Prescription Analytics Tests =====


@pytest.mark.asyncio
async def test_get_prescription_analytics(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test getting prescription analytics."""
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)
    # Flush so patient/presc1 exist before rows that FK-reference them —
    # Prescription/PrescriptionItem have no ORM relationship() to their
    # parents, so the flush's automatic dependency ordering doesn't cover them.
    await db_session.flush()

    # Create prescriptions
    presc1 = Prescription(
        id="presc1",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        prescribed_by=user_id,
        status="issued",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(presc1)
    await db_session.flush()

    # Add prescription items
    item1 = PrescriptionItem(
        tenant_id=tenant_data["id"],
        prescription_id=presc1.id,
        medicine_name="Arnica Montana 30C",
        dosage="5 drops",
        frequency="3 times daily",
        duration="7 days",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(item1)

    item2 = PrescriptionItem(
        tenant_id=tenant_data["id"],
        prescription_id=presc1.id,
        medicine_name="Belladonna 200C",
        dosage="3 drops",
        frequency="2 times daily",
        duration="3 days",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(item2)

    presc2 = Prescription(
        id="presc2",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        prescribed_by=user_id,
        status="draft",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(presc2)

    await db_session.commit()

    # Get prescription analytics
    analytics = await dashboard_service.get_prescription_analytics()

    assert analytics.total_prescriptions == 2
    assert analytics.total_items == 2
    assert analytics.average_items_per_prescription == 1.0  # 2 items / 2 prescriptions
    assert analytics.by_status.issued == 1
    assert analytics.by_status.draft == 1
    assert len(analytics.top_medicines) == 2


# ===== Helper Method Tests =====


@pytest.mark.asyncio
async def test_count_total_patients(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test counting total patients."""
    # Create patients
    for i in range(3):
        patient = Patient(
            id=f"patient{i}",
            tenant_id=tenant_data["id"],
            full_name=f"Patient {i}",
            date_of_birth=date(1980, 1, 1),
            gender="male",
            created_by=user_id,
            updated_by=user_id,
        )
        db_session.add(patient)

    await db_session.commit()

    count = await dashboard_service._count_total_patients()
    assert count == 3


@pytest.mark.asyncio
async def test_count_new_patients_in_month(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test counting new patients this month."""
    today = date.today()
    first_day_this_month = date(today.year, today.month, 1)

    # Patient created this month
    patient1 = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="Recent Patient",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient1)

    await db_session.commit()

    # Update created_at to ensure it's this month
    await db_session.execute(
        Patient.__table__.update()
        .where(Patient.id == "patient1")
        .values(created_at=datetime.now())
    )
    await db_session.commit()

    count = await dashboard_service._count_new_patients_in_month()
    assert count >= 1  # At least the one we just created


@pytest.mark.asyncio
async def test_calculate_total_revenue(
    dashboard_service: DashboardService,
    db_session: AsyncSession,
    tenant_data: dict,
    user_id: str,
):
    """Test calculating total revenue."""
    patient = Patient(
        id="patient1",
        tenant_id=tenant_data["id"],
        full_name="John Doe",
        date_of_birth=date(1980, 1, 1),
        gender="male",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(patient)

    # Paid payments
    for i in range(3):
        payment = Payment(
            id=f"payment{i}",
            tenant_id=tenant_data["id"],
            patient_id=patient.id,
            amount=1000.0,
            currency="BDT",
            payment_method="cash",
            status="paid",
            payment_date=date.today(),
            received_by=user_id,
            created_by=user_id,
            updated_by=user_id,
        )
        db_session.add(payment)

    # Pending payment (should not count)
    pending_payment = Payment(
        id="pending",
        tenant_id=tenant_data["id"],
        patient_id=patient.id,
        amount=500.0,
        currency="BDT",
        payment_method="cash",
        status="pending",
        payment_date=date.today(),
        received_by=user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add(pending_payment)

    await db_session.commit()

    revenue = await dashboard_service._calculate_total_revenue()
    assert revenue == 3000.0
