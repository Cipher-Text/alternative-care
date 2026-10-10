"""Receptionist RBAC: read-only on clinical areas, full on appointments/payments, no access to
doctor-profile / integrations / AI. Matrix: docs/architecture/roles-access.md."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.shared.models import User


@pytest.fixture
async def receptionist(db_session, test_tenant) -> User:
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        email="front.desk@test.com",
        password_hash=get_password_hash("FrontDesk123"),
        role="receptionist",
        full_name="Front Desk",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def desk(client: AsyncClient, receptionist, test_tenant) -> AsyncClient:
    token = create_access_token(
        {
            "sub": receptionist.id,
            "tenant_id": test_tenant.id,
            "role": "receptionist",
            "email": receptionist.email,
            "plan": test_tenant.plan,
        }
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def _denied(response):
    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert isinstance(detail, dict) and detail["code"] == "role_not_permitted"


@pytest.mark.asyncio
class TestReceptionistReadAccess:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/patients",
            "/api/v1/prescriptions",
            "/api/v1/medicines/",
            "/api/v1/symptoms/",
            "/api/v1/appointments",
            "/api/v1/appointments/visits",
            "/api/v1/payments",
            "/api/v1/entitlements/me",
        ],
    )
    async def test_can_read(self, desk: AsyncClient, path: str):
        response = await desk.get(path)
        assert response.status_code == 200, f"{path}: {response.text}"


@pytest.mark.asyncio
class TestReceptionistWriteRestrictions:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("POST", "/api/v1/patients"),
            ("PATCH", "/api/v1/patients/some-id"),
            ("DELETE", "/api/v1/patients/some-id"),
            ("POST", "/api/v1/prescriptions"),
            ("POST", "/api/v1/prescriptions/some-id/void"),
            ("POST", "/api/v1/medicines/"),
            ("POST", "/api/v1/symptoms/"),
            ("POST", "/api/v1/medicines/mappings"),
            ("POST", "/api/v1/appointments/visits"),
            ("PATCH", "/api/v1/appointments/visits/some-id"),
        ],
    )
    async def test_cannot_write(self, desk: AsyncClient, method: str, path: str):
        _denied(await desk.request(method, path, json={}))

    async def test_can_print_prescription_pdf(self, desk: AsyncClient):
        # printing is a GET (read-only), so the role guard lets it through; 404 = got past the
        # role check and found no such prescription.
        response = await desk.get("/api/v1/prescriptions/no-such-id/pdf")
        assert response.status_code == 404, response.text

    @pytest.mark.parametrize(
        "path", ["/api/v1/doctor/profile", "/api/v1/doctor/degrees", "/api/v1/integrations/"]
    )
    async def test_no_access_to_doctor_only_areas(self, desk: AsyncClient, path: str):
        _denied(await desk.get(path))

    async def test_no_ai_assistant(self, desk: AsyncClient):
        _denied(await desk.post("/api/v1/ai/query", json={"query": "q"}))


@pytest.mark.asyncio
class TestReceptionistKeepsFrontDeskWrites:
    async def test_appointments_and_payments_are_not_blocked_by_role(self, desk: AsyncClient):
        # An empty body fails validation (422), which proves the role guard let the request
        # through; a role block would be a 403.
        for path in ("/api/v1/appointments", "/api/v1/payments"):
            response = await desk.post(path, json={})
            assert response.status_code == 422, f"{path}: {response.status_code} {response.text}"


@pytest.mark.asyncio
class TestDoctorIsUnaffected:
    async def test_doctor_still_has_full_access(self, authenticated_client: AsyncClient):
        for path in (
            "/api/v1/patients",
            "/api/v1/doctor/profile",
            "/api/v1/integrations/",
            "/api/v1/appointments/visits",  # regression: was shadowed by /appointments/{id}
        ):
            response = await authenticated_client.get(path)
            assert response.status_code == 200, f"{path}: {response.text}"


@pytest.mark.asyncio
class TestSeatsCountPractitionersOnly:
    async def test_receptionist_does_not_use_a_seat(
        self, db_session, test_tenant, test_user, receptionist
    ):
        from app.core.entitlements import EntitlementService

        # test_user (doctor) + receptionist are both active users; only the doctor is a seat.
        assert await EntitlementService(db_session).used(test_tenant.id, "max_seats") == 1
