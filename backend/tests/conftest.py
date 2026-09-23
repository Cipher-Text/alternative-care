"""Pytest configuration and fixtures."""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.shared.models import (
    Division,
    District,
    Tenant,
    User,
    Patient,
    Visit,
    Payment,
    Invoice,
)

# Test database URL - replace the database name with test database
# Handle both 'altcare_dev' and 'alternative_care' database names
TEST_DATABASE_URL = str(settings.DATABASE_URL)
if "alternative_care" in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("alternative_care", "alternative_care_test")
elif "altcare_dev" in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("altcare_dev", "altcare_test")
else:
    # Fallback: append _test to whatever database name is there
    import re
    TEST_DATABASE_URL = re.sub(r"/([\w-]+)(\?|$)", r"/\1_test\2", TEST_DATABASE_URL)


@pytest.fixture(autouse=True)
def _disable_rate_limiting_by_default(monkeypatch):
    """Rate limiting defaults to off in tests so unrelated suites don't get
    poisoned by shared Redis counters. Tests that specifically exercise rate
    limiting re-enable it (settings.RATE_LIMIT_ENABLED = True) for their own
    scope.
    """
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)


@pytest.fixture(autouse=True)
async def _flush_rate_limit_redis():
    """Clear any rate-limit counters left over from a previous test run."""
    from app.core.rate_limit import get_redis_client

    try:
        redis = await get_redis_client()
        await redis.flushdb()
    except Exception:
        pass
    yield


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine for each test."""
    # Create a fresh engine for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

    # Drop all tables first
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.drop_all)

    # Try to create all tables
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # If creation fails (likely due to pgvector or pg_trgm),
        # create tables individually, skipping problematic ones
        error_msg = str(e).lower()
        if 'vector' in error_msg or 'trgm' in error_msg or 'gin' in error_msg:
            # Create tables one by one in separate transactions
            for table in Base.metadata.sorted_tables:
                try:
                    async with engine.begin() as conn:
                        await conn.run_sync(table.create, checkfirst=True)
                except Exception as ex:
                    # Skip tables that fail (embeddings, medicines with gin indexes, etc.)
                    if 'vector' not in str(ex).lower() and 'gin' not in str(ex).lower() and 'trgm' not in str(ex).lower():
                        # If it's a different error, raise it
                        print(f"Error creating table {table.name}: {ex}")
        else:
            raise

    yield engine

    # Cleanup: drop all tables after test
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            # Ignore errors during cleanup
            pass

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session."""
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client_2(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Second, independent test client sharing the same test database session.

    Kept as a distinct AsyncClient (not just `client` reused) so that
    `authenticated_client` and `authenticated_client_2` can carry different
    Authorization headers without one overwriting the other's header on the
    same shared object.
    """
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Geographic Data Fixtures
# ============================================================================


@pytest.fixture
async def test_division(db_session: AsyncSession) -> Division:
    """Create test division."""
    division = Division(
        id=1,
        name_en="Dhaka",
        name_bn="ঢাকা",
    )
    db_session.add(division)
    await db_session.commit()
    await db_session.refresh(division)
    return division


@pytest.fixture
async def test_district(db_session: AsyncSession, test_division: Division) -> District:
    """Create test district."""
    district = District(
        id=1,
        division_id=test_division.id,
        name_en="Dhaka",
        name_bn="ঢাকা",
    )
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    return district


# ============================================================================
# Tenant Fixtures
# ============================================================================


@pytest.fixture
async def test_tenant(db_session: AsyncSession, test_division: Division, test_district: District) -> Tenant:
    """Create approved test tenant."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Dr. Test Doctor",
        email="doctor@test.com",
        phone="+8801712345678",
        clinic_name="Test Clinic",
        clinic_address="123 Test St, Dhaka",
        division_id=test_division.id,
        district_id=test_district.id,
        specializations=["homeopathy", "ayurveda"],
        license_number="BMDC-12345",
        is_verified=True,
        is_approved=True,
        is_active=True,
        plan="free",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_tenant_2(db_session: AsyncSession, test_division: Division, test_district: District) -> Tenant:
    """Create second approved test tenant for multi-tenant isolation tests."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Dr. Another Doctor",
        email="doctor2@test.com",
        phone="+8801798765432",
        clinic_name="Another Clinic",
        clinic_address="456 Other St, Dhaka",
        division_id=test_division.id,
        district_id=test_district.id,
        specializations=["unani"],
        license_number="BMDC-54321",
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
async def unapproved_tenant(db_session: AsyncSession, test_division: Division, test_district: District) -> Tenant:
    """Create unapproved test tenant."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Dr. Pending Doctor",
        email="pending@test.com",
        phone="+8801755555555",
        clinic_name="Pending Clinic",
        clinic_address="789 Pending St, Dhaka",
        division_id=test_division.id,
        district_id=test_district.id,
        specializations=["herbal"],
        license_number="BMDC-99999",
        is_verified=False,
        is_approved=False,  # Not approved
        is_active=True,
        plan="free",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


# ============================================================================
# User Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create test doctor user with approved tenant."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        email="doctor@test.com",
        password_hash=get_password_hash("TestPass123"),
        role="doctor",
        full_name="Dr. Test Doctor",
        phone="+8801712345678",
        language="en",
        is_active=True,
        is_email_verified=True,
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_2(db_session: AsyncSession, test_tenant_2: Tenant) -> User:
    """Create second test doctor user for multi-tenant isolation tests."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant_2.id,
        email="doctor2@test.com",
        password_hash=get_password_hash("TestPass456"),
        role="doctor",
        full_name="Dr. Another Doctor",
        phone="+8801798765432",
        language="en",
        is_active=True,
        is_email_verified=True,
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def unapproved_user(db_session: AsyncSession, unapproved_tenant: Tenant) -> User:
    """Create test user with unapproved tenant."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=unapproved_tenant.id,
        email="pending@test.com",
        password_hash=get_password_hash("PendingPass123"),
        role="doctor",
        full_name="Dr. Pending Doctor",
        phone="+8801755555555",
        language="en",
        is_active=True,
        is_email_verified=False,
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def platform_admin(db_session: AsyncSession) -> User:
    """Create platform admin user (no tenant)."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=None,  # Platform user
        email="admin@altcare.com",
        password_hash=get_password_hash("AdminPass123"),
        role="admin",
        full_name="Platform Admin",
        phone="+8801700000000",
        language="en",
        is_active=True,
        is_email_verified=True,
        is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_with_2fa(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create test user with 2FA enabled."""
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        email="2fa@test.com",
        password_hash=get_password_hash("2FAPass123"),
        role="doctor",
        full_name="Dr. 2FA User",
        phone="+8801766666666",
        language="en",
        is_active=True,
        is_email_verified=True,
        is_2fa_enabled=True,
        totp_secret="JBSWY3DPEHPK3PXP",  # Test TOTP secret
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ============================================================================
# JWT Token Fixtures
# ============================================================================


@pytest.fixture
def test_access_token(test_user: User, test_tenant: Tenant) -> str:
    """Generate JWT access token for test user."""
    token_data = {
        "sub": test_user.id,
        "tenant_id": test_tenant.id,
        "role": test_user.role,
        "email": test_user.email,
        "plan": test_tenant.plan,
    }
    return create_access_token(token_data)


@pytest.fixture
def test_access_token_2(test_user_2: User, test_tenant_2: Tenant) -> str:
    """Generate JWT access token for second test user."""
    token_data = {
        "sub": test_user_2.id,
        "tenant_id": test_tenant_2.id,
        "role": test_user_2.role,
        "email": test_user_2.email,
        "plan": test_tenant_2.plan,
    }
    return create_access_token(token_data)


@pytest.fixture
def admin_access_token(platform_admin: User) -> str:
    """Generate JWT access token for platform admin."""
    token_data = {
        "sub": platform_admin.id,
        "tenant_id": None,  # Platform user
        "role": platform_admin.role,
        "email": platform_admin.email,
        "plan": None,
    }
    return create_access_token(token_data)


# ============================================================================
# Authenticated Client Fixtures
# ============================================================================


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_access_token: str) -> AsyncClient:
    """Create authenticated test client with JWT token."""
    client.headers["Authorization"] = f"Bearer {test_access_token}"
    return client


@pytest.fixture
async def authenticated_client_2(client_2: AsyncClient, test_access_token_2: str) -> AsyncClient:
    """Create authenticated test client for second user.

    Uses `client_2`, a separate AsyncClient from `authenticated_client`'s
    `client` — see `client_2`'s docstring for why.
    """
    client_2.headers["Authorization"] = f"Bearer {test_access_token_2}"
    return client_2


@pytest.fixture
async def admin_client(client: AsyncClient, admin_access_token: str) -> AsyncClient:
    """Create authenticated admin client."""
    client.headers["Authorization"] = f"Bearer {admin_access_token}"
    return client


# ============================================================================
# Convenient Token Alias Fixtures
# ============================================================================


@pytest.fixture
def doctor_token(test_access_token: str) -> str:
    """Alias for test_access_token (for clearer test naming)."""
    return test_access_token


# ============================================================================
# Patient Fixtures
# ============================================================================


@pytest.fixture
async def test_patient(db_session: AsyncSession, test_tenant: Tenant) -> Patient:
    """Create test patient."""
    from datetime import date

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        full_name="John Doe",
        date_of_birth=date(1980, 5, 15),
        gender="male",
        phone="+8801811111111",
        email="john.doe@example.com",
        address="123 Patient Street, Dhaka",
        blood_group="O+",
        created_by=str(uuid.uuid4()),
        updated_by=str(uuid.uuid4()),
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def test_patient_2(db_session: AsyncSession, test_tenant_2: Tenant) -> Patient:
    """Create test patient for second tenant (isolation tests)."""
    from datetime import date

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant_2.id,
        full_name="Jane Smith",
        date_of_birth=date(1985, 8, 20),
        gender="female",
        phone="+8801822222222",
        email="jane.smith@example.com",
        address="456 Patient Avenue, Dhaka",
        blood_group="A+",
        created_by=str(uuid.uuid4()),
        updated_by=str(uuid.uuid4()),
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


# ============================================================================
# Visit Fixtures
# ============================================================================


@pytest.fixture
async def test_visit(
    db_session: AsyncSession, test_tenant: Tenant, test_patient: Patient, test_user: User
) -> Visit:
    """Create test visit."""
    from datetime import datetime

    visit = Visit(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        doctor_id=test_user.id,
        visit_date=datetime.utcnow().date(),
        visit_type="consultation",
        chief_complaint="Headache and fever",
        provisional_diagnosis="Common cold",
        treatment_plan="Rest and hydration recommended",
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(visit)
    await db_session.commit()
    await db_session.refresh(visit)
    return visit


# ============================================================================
# Payment Fixtures
# ============================================================================


@pytest.fixture
async def test_payment(
    db_session: AsyncSession, test_tenant: Tenant, test_patient: Patient, test_user: User
) -> Payment:
    """Create test payment."""
    from datetime import date

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        amount=1000.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        description="Consultation fee",
        payment_date=date.today(),
        received_by=test_user.id,
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


@pytest.fixture
async def other_tenant_payment(
    db_session: AsyncSession, test_tenant_2: Tenant, test_patient_2: Patient, test_user_2: User
) -> Payment:
    """Create payment for second tenant (isolation tests)."""
    from datetime import date

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant_2.id,
        patient_id=test_patient_2.id,
        amount=1500.0,
        currency="BDT",
        payment_method="cash",
        status="paid",
        description="Treatment fee",
        payment_date=date.today(),
        received_by=test_user_2.id,
        created_by=test_user_2.id,
        updated_by=test_user_2.id,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


# ============================================================================
# Invoice Fixtures
# ============================================================================


@pytest.fixture
async def test_invoice(
    db_session: AsyncSession, test_tenant: Tenant, test_payment: Payment, test_user: User
) -> Invoice:
    """Create test invoice."""
    from datetime import date, timedelta

    invoice = Invoice(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        payment_id=test_payment.id,
        invoice_number="INV-202604-0001",
        status="draft",
        due_date=date.today() + timedelta(days=30),
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def other_tenant_invoice(
    db_session: AsyncSession,
    test_tenant_2: Tenant,
    other_tenant_payment: Payment,
    test_user_2: User,
) -> Invoice:
    """Create invoice for second tenant (isolation tests)."""
    from datetime import date, timedelta

    invoice = Invoice(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant_2.id,
        payment_id=other_tenant_payment.id,
        invoice_number="INV-202604-0002",
        status="draft",
        due_date=date.today() + timedelta(days=30),
        created_by=test_user_2.id,
        updated_by=test_user_2.id,
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice
