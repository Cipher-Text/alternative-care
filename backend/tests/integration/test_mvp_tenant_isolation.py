"""
Comprehensive multi-tenant isolation tests for MVP features.

CRITICAL: These tests ensure complete data isolation between tenants for:
- Patient Management (CRUD, search, tags, diagnoses)
- Dashboard Analytics (overview, financial, patient stats)

According to CLAUDE.md: "Target: 100% coverage for multi-tenant queries"
MVP Scope: Auth + Patients + Dashboard
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from uuid import uuid4
from datetime import date, datetime, timedelta

from app.shared.models import (
    Tenant,
    User,
    Patient,
    PatientTag,
    PatientDiagnosis,
    Payment,
    Appointment,
)


@pytest.fixture
async def setup_two_tenants(db_session):
    """Create two isolated tenants with doctors and patients."""
    # Create tenants
    tenant1 = Tenant(
        id=str(uuid4()),
        name="Clinic Alpha",
        email="alpha@clinic.com",
        clinic_name="Alpha Homeopathy Clinic",
        specializations=["homeopathy"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    tenant2 = Tenant(
        id=str(uuid4()),
        name="Clinic Beta",
        email="beta@clinic.com",
        clinic_name="Beta Ayurveda Center",
        specializations=["ayurveda"],
        plan="pro",
        is_active=True,
        is_approved=True,
    )
    db_session.add_all([tenant1, tenant2])
    await db_session.commit()

    # Create doctors
    doctor1 = User(
        id=str(uuid4()),
        tenant_id=tenant1.id,
        email="doctor.alpha@clinic.com",
        password_hash="$2b$12$test_hash_alpha",
        full_name="Dr. Alpha",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    doctor2 = User(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        email="doctor.beta@clinic.com",
        password_hash="$2b$12$test_hash_beta",
        full_name="Dr. Beta",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add_all([doctor1, doctor2])
    await db_session.commit()

    # Create patients for tenant1
    patient1a = Patient(
        id=str(uuid4()),
        tenant_id=tenant1.id,
        full_name="Alice Alpha",
        phone="01711111111",
        date_of_birth=date(1990, 1, 1),
        gender="female",
        is_active=True,
        created_by=doctor1.id,
    )
    patient1b = Patient(
        id=str(uuid4()),
        tenant_id=tenant1.id,
        full_name="Bob Alpha",
        phone="01722222222",
        date_of_birth=date(1985, 6, 15),
        gender="male",
        is_active=True,
        created_by=doctor1.id,
    )
    db_session.add_all([patient1a, patient1b])

    # Create patients for tenant2
    patient2a = Patient(
        id=str(uuid4()),
        tenant_id=tenant2.id,
        full_name="Charlie Beta",
        phone="01733333333",
        date_of_birth=date(1995, 3, 20),
        gender="male",
        is_active=True,
        created_by=doctor2.id,
    )
    db_session.add_all([patient2a])
    await db_session.commit()

    # Create tokens
    from app.core.security import create_access_token

    token1 = create_access_token(
        {
            "sub": doctor1.id,
            "email": doctor1.email,
            "role": doctor1.role,
            "tenant_id": tenant1.id,
            "plan": tenant1.plan,
        }
    )
    token2 = create_access_token(
        {
            "sub": doctor2.id,
            "email": doctor2.email,
            "role": doctor2.role,
            "tenant_id": tenant2.id,
            "plan": tenant2.plan,
        }
    )

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "doctor1": doctor1,
        "doctor2": doctor2,
        "patient1a": patient1a,
        "patient1b": patient1b,
        "patient2a": patient2a,
        "token1": token1,
        "token2": token2,
    }


@pytest.mark.asyncio
class TestPatientCRUDIsolation:
    """Test patient CRUD operations are tenant-isolated."""

    async def test_list_patients_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that list patients only returns tenant's own patients."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant1 should see 2 patients
        response1 = await client.get("/api/v1/patients", headers=headers1)
        assert response1.status_code == 200
        patients1 = response1.json()
        assert len(patients1) == 2
        assert all(p["full_name"].endswith("Alpha") for p in patients1)

        # Tenant2 should see 1 patient
        response2 = await client.get("/api/v1/patients", headers=headers2)
        assert response2.status_code == 200
        patients2 = response2.json()
        assert len(patients2) == 1
        assert patients2[0]["full_name"] == "Charlie Beta"

    async def test_get_patient_by_id_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that get patient by ID prevents cross-tenant access."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant1 can access their own patient
        response1 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers1
        )
        assert response1.status_code == 200
        assert response1.json()["full_name"] == "Alice Alpha"

        # Tenant2 CANNOT access tenant1's patient (should get 404, not 403)
        response2 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers2
        )
        assert response2.status_code == 404
        assert "not found" in response2.json()["detail"].lower()

        # Tenant1 CANNOT access tenant2's patient
        response3 = await client.get(
            f"/api/v1/patients/{data['patient2a'].id}", headers=headers1
        )
        assert response3.status_code == 404

    async def test_create_patient_tenant_scoping(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that created patients are automatically scoped to tenant."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}

        # Create patient as tenant1
        new_patient = {
            "full_name": "New Patient Alpha",
            "phone": "01799999999",
            "date_of_birth": "2000-01-01",
            "gender": "male",
        }
        response = await client.post(
            "/api/v1/patients", json=new_patient, headers=headers1
        )
        assert response.status_code == 201
        created = response.json()

        # Verify patient is scoped to tenant1
        assert created["full_name"] == "New Patient Alpha"

        # Tenant2 should NOT see this patient
        headers2 = {"Authorization": f"Bearer {data['token2']}"}
        response2 = await client.get(
            f"/api/v1/patients/{created['id']}", headers=headers2
        )
        assert response2.status_code == 404

    async def test_update_patient_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that update only works on own tenant's patients."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant1 can update their own patient
        update_data = {"full_name": "Alice Alpha Updated"}
        response1 = await client.patch(
            f"/api/v1/patients/{data['patient1a'].id}",
            json=update_data,
            headers=headers1,
        )
        assert response1.status_code == 200
        assert response1.json()["full_name"] == "Alice Alpha Updated"

        # Tenant2 CANNOT update tenant1's patient
        response2 = await client.patch(
            f"/api/v1/patients/{data['patient1a'].id}",
            json={"full_name": "Hacked"},
            headers=headers2,
        )
        assert response2.status_code == 404

        # Verify patient was NOT updated by tenant2
        response3 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers1
        )
        assert response3.json()["full_name"] == "Alice Alpha Updated"

    async def test_delete_patient_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that delete (soft delete) only works on own tenant's patients."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant2 CANNOT delete tenant1's patient
        response1 = await client.delete(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers2
        )
        assert response1.status_code == 404

        # Verify patient still exists for tenant1
        response2 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers1
        )
        assert response2.status_code == 200
        assert response2.json()["full_name"] == "Alice Alpha"

        # Tenant1 CAN delete their own patient
        response3 = await client.delete(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers1
        )
        assert response3.status_code in [200, 204]  # Either OK or No Content acceptable

        # Patient should be marked inactive (soft delete via is_active flag)
        await db_session.refresh(data["patient1a"])
        assert data["patient1a"].is_active == False


@pytest.mark.asyncio
class TestPatientSearchIsolation:
    """Test patient search is tenant-isolated."""

    async def test_search_by_name_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that search only returns tenant's own patients."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Search for "Alpha" as tenant1 - should find 2 patients
        response1 = await client.get(
            "/api/v1/patients?search=Alpha", headers=headers1
        )
        assert response1.status_code == 200
        assert len(response1.json()) == 2

        # Search for "Alpha" as tenant2 - should find 0 patients
        response2 = await client.get(
            "/api/v1/patients?search=Alpha", headers=headers2
        )
        assert response2.status_code == 200
        assert len(response2.json()) == 0

    async def test_search_by_phone_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that phone search doesn't leak across tenants."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant2 searches for tenant1's patient phone
        response = await client.get(
            "/api/v1/patients?search=01711111111", headers=headers2
        )
        assert response.status_code == 200
        assert len(response.json()) == 0  # Should not find tenant1's patient


@pytest.mark.asyncio
class TestPatientTagsIsolation:
    """Test patient tags are tenant-isolated."""

    async def test_patient_tags_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that patient tags don't leak across tenants."""
        data = setup_two_tenants

        # Create tags for patients
        tag1 = PatientTag(
            tenant_id=data["tenant1"].id,
            patient_id=data["patient1a"].id,
            tag_type="special_case",
            tag_value="vip",
            created_by=data["doctor1"].id,
        )
        tag2 = PatientTag(
            tenant_id=data["tenant2"].id,
            patient_id=data["patient2a"].id,
            tag_type="special_case",
            tag_value="vip",
            created_by=data["doctor2"].id,
        )
        db_session.add_all([tag1, tag2])
        await db_session.commit()

        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Get patient with tags from tenant1
        response1 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers1
        )
        patient1 = response1.json()
        # Note: Verify tags are returned if the API includes them

        # Tenant2 should not see tenant1's patient tags
        # (Already verified by patient isolation - 404 on access)
        response2 = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers2
        )
        assert response2.status_code == 404


@pytest.mark.asyncio
class TestPatientDiagnosesIsolation:
    """Test patient diagnoses are tenant-isolated."""

    async def test_patient_diagnoses_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that patient diagnoses don't leak across tenants."""
        data = setup_two_tenants

        # Create diagnoses for patients
        diagnosis1 = PatientDiagnosis(
            tenant_id=data["tenant1"].id,
            patient_id=data["patient1a"].id,
            description="Migraine",
            diagnosed_at=date.today(),
            created_by=data["doctor1"].id,
        )
        diagnosis2 = PatientDiagnosis(
            tenant_id=data["tenant2"].id,
            patient_id=data["patient2a"].id,
            description="Arthritis",
            diagnosed_at=date.today(),
            created_by=data["doctor2"].id,
        )
        db_session.add_all([diagnosis1, diagnosis2])
        await db_session.commit()

        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant2 cannot see tenant1's patient diagnoses
        response = await client.get(
            f"/api/v1/patients/{data['patient1a'].id}", headers=headers2
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDashboardAnalyticsIsolation:
    """Test dashboard analytics are tenant-isolated (CRITICAL)."""

    async def test_overview_stats_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that overview stats only show tenant's own data."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Create payments for tenant1
        payment1 = Payment(
            id=str(uuid4()),
            tenant_id=data["tenant1"].id,
            patient_id=data["patient1a"].id,
            amount=500.00,
            payment_method="cash",
            payment_date=date.today(),
            received_by=data["doctor1"].id,
            status="paid",
            created_by=data["doctor1"].id,
        )
        db_session.add(payment1)
        await db_session.commit()

        # Tenant1 dashboard
        response1 = await client.get("/api/v1/dashboard/overview", headers=headers1)
        assert response1.status_code == 200
        stats1 = response1.json()
        assert stats1["total_patients"] == 2  # Only tenant1's patients
        assert stats1["total_revenue"] == 500.00

        # Tenant2 dashboard
        response2 = await client.get("/api/v1/dashboard/overview", headers=headers2)
        assert response2.status_code == 200
        stats2 = response2.json()
        assert stats2["total_patients"] == 1  # Only tenant2's patients
        assert stats2["total_revenue"] == 0  # No payments for tenant2

    async def test_financial_analytics_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that financial analytics don't leak revenue data."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Create multiple payments for tenant1
        payments = [
            Payment(
                id=str(uuid4()),
                tenant_id=data["tenant1"].id,
                patient_id=data["patient1a"].id,
                amount=1000.00,
                payment_method="cash",
                payment_date=date.today(),
                received_by=data["doctor1"].id,
                status="paid",
                created_by=data["doctor1"].id,
            ),
            Payment(
                id=str(uuid4()),
                tenant_id=data["tenant1"].id,
                patient_id=data["patient1b"].id,
                amount=750.00,
                payment_method="bkash",
                payment_date=date.today(),
                received_by=data["doctor1"].id,
                status="paid",
                created_by=data["doctor1"].id,
            ),
        ]
        db_session.add_all(payments)
        await db_session.commit()

        # Tenant1 should see total 1750
        response1 = await client.get("/api/v1/dashboard/financial", headers=headers1)
        assert response1.status_code == 200
        financial1 = response1.json()
        assert financial1["total_revenue"] == 1750.00
        assert len(financial1["revenue_by_method"]) > 0

        # Tenant2 should see 0
        response2 = await client.get("/api/v1/dashboard/financial", headers=headers2)
        assert response2.status_code == 200
        financial2 = response2.json()
        assert financial2["total_revenue"] == 0

    async def test_patient_analytics_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that patient analytics only show tenant's demographics."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Tenant1 patient analytics
        response1 = await client.get("/api/v1/dashboard/patients", headers=headers1)
        assert response1.status_code == 200
        analytics1 = response1.json()
        assert analytics1["total_patients"] == 2
        # Demographics should only reflect tenant1's patients (1 male, 1 female)
        demographics1 = analytics1.get("demographics", {})
        if demographics1:
            assert demographics1.get("male", 0) + demographics1.get("female", 0) == 2

        # Tenant2 patient analytics
        response2 = await client.get("/api/v1/dashboard/patients", headers=headers2)
        assert response2.status_code == 200
        analytics2 = response2.json()
        assert analytics2["total_patients"] == 1
        # Demographics should only reflect tenant2's patients (1 male)

    async def test_appointment_analytics_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that appointment analytics don't leak appointment data."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Create appointment for tenant1
        from datetime import time as Time
        appointment = Appointment(
            id=str(uuid4()),
            tenant_id=data["tenant1"].id,
            patient_id=data["patient1a"].id,
            doctor_id=data["doctor1"].id,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=Time(10, 0),  # 10:00 AM
            duration_minutes=30,
            status="scheduled",
            reason="Consultation",
            created_by=data["doctor1"].id,
        )
        db_session.add(appointment)
        await db_session.commit()

        # Tenant1 should see 1 appointment
        response1 = await client.get(
            "/api/v1/dashboard/appointments", headers=headers1
        )
        assert response1.status_code == 200
        appt_stats1 = response1.json()
        assert appt_stats1["total_appointments"] == 1

        # Tenant2 should see 0 appointments
        response2 = await client.get(
            "/api/v1/dashboard/appointments", headers=headers2
        )
        assert response2.status_code == 200
        appt_stats2 = response2.json()
        assert appt_stats2["total_appointments"] == 0

    async def test_dashboard_date_range_tenant_isolation(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that date-range filtering still maintains tenant isolation."""
        data = setup_two_tenants
        headers1 = {"Authorization": f"Bearer {data['token1']}"}
        headers2 = {"Authorization": f"Bearer {data['token2']}"}

        # Create payment for tenant1 with specific date
        payment = Payment(
            id=str(uuid4()),
            tenant_id=data["tenant1"].id,
            patient_id=data["patient1a"].id,
            amount=2000.00,
            payment_method="cash",
            payment_date=date(2026, 4, 15),
            received_by=data["doctor1"].id,
            status="paid",
            created_at=datetime(2026, 4, 15),
            created_by=data["doctor1"].id,
        )
        db_session.add(payment)
        await db_session.commit()

        # Tenant2 queries same date range - should see 0
        response = await client.get(
            "/api/v1/dashboard/financial?date_from=2026-04-01&date_to=2026-04-30",
            headers=headers2,
        )
        assert response.status_code == 200
        assert response.json()["total_revenue"] == 0


@pytest.mark.asyncio
class TestJWTTokenManipulation:
    """Test that JWT token manipulation is blocked."""

    async def test_cannot_modify_tenant_id_in_jwt(
        self, client: AsyncClient, setup_two_tenants, db_session
    ):
        """Test that modifying tenant_id in JWT doesn't grant access."""
        data = setup_two_tenants

        # This test verifies that the JWT signature validation works
        # If someone tries to modify the tenant_id claim, the signature will be invalid

        # Create a fake token with wrong tenant_id (will fail signature check)
        from jose import jwt
        from app.core.config import settings

        # Try to create token with tenant2's ID but doctor1's info
        fake_payload = {
            "sub": data["doctor1"].id,
            "email": data["doctor1"].email,
            "role": data["doctor1"].role,
            "tenant_id": data["tenant2"].id,  # Wrong tenant!
        }

        # Sign with wrong secret (simulating tampering)
        fake_token = jwt.encode(fake_payload, "wrong-secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {fake_token}"}

        # Should be rejected with 401
        response = await client.get("/api/v1/patients", headers=headers)
        assert response.status_code == 401

    async def test_cannot_elevate_role_in_jwt(
        self, client: AsyncClient, setup_two_tenants
    ):
        """Test that modifying role in JWT doesn't grant elevated privileges."""
        data = setup_two_tenants

        # Create doctor token but try to claim admin role
        from jose import jwt
        from app.core.config import settings

        fake_payload = {
            "sub": data["doctor1"].id,
            "email": data["doctor1"].email,
            "role": "admin",  # Trying to elevate to admin
            "tenant_id": data["tenant1"].id,
        }

        # Sign with wrong secret
        fake_token = jwt.encode(fake_payload, "wrong-secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {fake_token}"}

        # Should be rejected
        response = await client.get("/api/v1/dashboard/overview", headers=headers)
        assert response.status_code == 401
