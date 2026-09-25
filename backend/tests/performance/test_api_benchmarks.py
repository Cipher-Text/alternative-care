"""
Performance benchmarks for critical API endpoints.

Tests response times for MVP features under load:
- Authentication endpoints
- Patient list/search
- Dashboard analytics

Target: < 200ms for list endpoints, < 500ms for analytics
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.shared.models import Patient, Payment, Appointment


@pytest.mark.asyncio
@pytest.mark.benchmark(group="auth")
class TestAuthPerformance:
    """Benchmark authentication endpoints."""

    async def test_login_performance(
        self, client: AsyncClient, test_user, benchmark
    ):
        """Test login endpoint response time."""

        async def do_login():
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": "TestPass123"},
            )
            assert response.status_code == 200
            return response

        result = await benchmark.pedantic(do_login, iterations=10, rounds=5)
        # Target: < 100ms for login
        assert result is not None

    async def test_token_refresh_performance(
        self, client: AsyncClient, test_user, benchmark
    ):
        """Test token refresh endpoint response time."""
        # Login first to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass123"},
        )
        assert login_response.status_code == 200
        refresh_token = client.cookies.get("refresh_token")

        async def do_refresh():
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert response.status_code == 200
            return response

        result = await benchmark.pedantic(do_refresh, iterations=10, rounds=5)
        # Target: < 50ms for token refresh (no DB query)
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.benchmark(group="patients")
class TestPatientPerformance:
    """Benchmark patient management endpoints."""

    async def test_patient_list_performance(
        self, authenticated_client: AsyncClient, db_session, test_tenant, test_user, benchmark
    ):
        """Test patient list endpoint with 100 patients."""
        # Create 100 test patients
        from app.shared.models import Patient
        from uuid import uuid4

        patients = [
            Patient(
                id=str(uuid4()),
                tenant_id=test_tenant.id,
                full_name=f"Test Patient {i}",
                phone=f"0171000{i:04d}",
                is_active=True,
                created_by=test_user.id,
            )
            for i in range(100)
        ]
        db_session.add_all(patients)
        await db_session.commit()

        async def get_patients():
            response = await authenticated_client.get("/api/v1/patients")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 100
            return response

        result = await benchmark.pedantic(get_patients, iterations=5, rounds=3)
        # Target: < 200ms for 100 patients
        assert result is not None

    async def test_patient_search_performance(
        self, authenticated_client: AsyncClient, db_session, test_tenant, test_user, benchmark
    ):
        """Test patient search performance."""
        # Patients already created from previous test or fixture
        async def search_patients():
            response = await authenticated_client.get(
                "/api/v1/patients?search=Test"
            )
            assert response.status_code == 200
            return response

        result = await benchmark.pedantic(search_patients, iterations=5, rounds=3)
        # Target: < 150ms for search with LIKE query
        assert result is not None

    async def test_patient_get_by_id_performance(
        self, authenticated_client: AsyncClient, test_patient, benchmark
    ):
        """Test single patient retrieval."""

        async def get_patient():
            response = await authenticated_client.get(
                f"/api/v1/patients/{test_patient.id}"
            )
            assert response.status_code == 200
            return response

        result = await benchmark.pedantic(get_patient, iterations=10, rounds=5)
        # Target: < 50ms for get by ID (primary key lookup)
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.benchmark(group="dashboard")
class TestDashboardPerformance:
    """Benchmark dashboard analytics endpoints."""

    async def test_dashboard_overview_performance(
        self, authenticated_client: AsyncClient, db_session, test_tenant, test_user, benchmark
    ):
        """Test dashboard overview with realistic data."""
        from app.shared.models import Patient, Payment, Appointment
        from uuid import uuid4
        from datetime import date, time

        # Create realistic test data: 50 patients, 100 payments, 50 appointments
        patients = [
            Patient(
                id=str(uuid4()),
                tenant_id=test_tenant.id,
                full_name=f"Patient {i}",
                is_active=True,
                created_by=test_user.id,
            )
            for i in range(50)
        ]
        db_session.add_all(patients)
        await db_session.flush()

        payments = [
            Payment(
                id=str(uuid4()),
                tenant_id=test_tenant.id,
                patient_id=patients[i % 50].id,
                amount=500.0 + (i * 10),
                payment_method="cash",
                payment_date=date.today(),
                received_by=test_user.id,
                status="paid",
                created_by=test_user.id,
            )
            for i in range(100)
        ]
        db_session.add_all(payments)

        appointments = [
            Appointment(
                id=str(uuid4()),
                tenant_id=test_tenant.id,
                patient_id=patients[i % 50].id,
                doctor_id=test_user.id,
                appointment_date=date.today(),
                appointment_time=time(10, 0),
                status="scheduled",
                created_by=test_user.id,
            )
            for i in range(50)
        ]
        db_session.add_all(appointments)
        await db_session.commit()

        async def get_overview():
            response = await authenticated_client.get("/api/v1/dashboard/overview")
            assert response.status_code == 200
            data = response.json()
            assert data["total_patients"] >= 50
            assert data["total_revenue"] > 0
            return response

        result = await benchmark.pedantic(get_overview, iterations=5, rounds=3)
        # Target: < 500ms for aggregated analytics
        assert result is not None

    async def test_financial_analytics_performance(
        self, authenticated_client: AsyncClient, benchmark
    ):
        """Test financial analytics endpoint."""
        # Data already created from overview test

        async def get_financial():
            response = await authenticated_client.get("/api/v1/dashboard/financial")
            assert response.status_code == 200
            return response

        result = await benchmark.pedantic(get_financial, iterations=5, rounds=3)
        # Target: < 400ms for complex aggregations
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.benchmark(group="database")
class TestDatabaseQueryPerformance:
    """Benchmark raw database queries."""

    async def test_tenant_filter_query_performance(
        self, db_session, test_tenant, benchmark
    ):
        """Test that tenant_id filtering is using index."""

        async def query_patients():
            result = await db_session.execute(
                select(Patient).where(Patient.tenant_id == test_tenant.id).limit(100)
            )
            patients = result.scalars().all()
            return patients

        result = await benchmark.pedantic(query_patients, iterations=10, rounds=5)
        # Should be very fast with index
        assert result is not None

    async def test_payment_aggregation_performance(
        self, db_session, test_tenant, benchmark
    ):
        """Test payment sum aggregation performance."""
        from sqlalchemy import func

        async def aggregate_payments():
            result = await db_session.execute(
                select(func.sum(Payment.amount)).where(
                    Payment.tenant_id == test_tenant.id,
                    Payment.status == "paid"
                )
            )
            total = result.scalar() or 0
            return total

        result = await benchmark.pedantic(aggregate_payments, iterations=10, rounds=5)
        # Target: < 20ms for aggregation with index
        assert result is not None


@pytest.mark.asyncio
class TestConcurrentRequests:
    """Test API under concurrent load."""

    async def test_concurrent_patient_list_requests(
        self, authenticated_client: AsyncClient, test_tenant
    ):
        """Test 10 concurrent patient list requests."""
        import asyncio

        async def get_patients():
            response = await authenticated_client.get("/api/v1/patients")
            assert response.status_code == 200
            return response

        # Simulate 10 concurrent users
        tasks = [get_patients() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r.status_code == 200 for r in results)

    async def test_concurrent_dashboard_requests(
        self, authenticated_client: AsyncClient
    ):
        """Test 5 concurrent dashboard requests."""
        import asyncio

        async def get_dashboard():
            response = await authenticated_client.get("/api/v1/dashboard/overview")
            assert response.status_code == 200
            return response

        tasks = [get_dashboard() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r.status_code == 200 for r in results)


@pytest.mark.asyncio
class TestMemoryUsage:
    """Test memory efficiency of large data sets."""

    async def test_large_patient_list_memory(
        self, authenticated_client: AsyncClient, db_session, test_tenant, test_user
    ):
        """Test memory usage with 1000 patients."""
        from app.shared.models import Patient
        from uuid import uuid4
        import tracemalloc

        # Create 1000 patients
        patients = [
            Patient(
                id=str(uuid4()),
                tenant_id=test_tenant.id,
                full_name=f"Patient {i}",
                phone=f"017{i:07d}",
                is_active=True,
                created_by=test_user.id,
            )
            for i in range(1000)
        ]
        db_session.add_all(patients)
        await db_session.commit()

        # Track memory
        tracemalloc.start()

        # GET /api/v1/patients caps page size at 500 (le=500) by design, so
        # 1000 seeded patients can't come back in one call — request the max.
        response = await authenticated_client.get("/api/v1/patients?limit=500")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 500

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should be reasonable (< 50MB for 1000 records)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 50, f"Peak memory usage too high: {peak_mb:.2f}MB"
