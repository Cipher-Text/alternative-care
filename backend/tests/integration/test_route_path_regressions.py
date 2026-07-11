"""Integration regressions for API route path sync."""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.main import app


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeExecuteResult:
    def __init__(self, *, scalars=None, rows=None):
        self._scalars = scalars or []
        self._rows = rows or []

    def scalars(self):
        return _FakeScalarResult(self._scalars)

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)

    async def execute(self, _query):
        return self._results.pop(0)


async def _fake_current_user():
    return CurrentUser(
        user_id="test-user",
        tenant_id="test-tenant",
        role="doctor",
        email="doctor@test.local",
        plan="free",
    )


async def _request_with_fake_db(path: str, results, query: str = "bruise"):
    async def fake_get_db():
        yield _FakeSession(results)

    app.dependency_overrides[get_current_user] = _fake_current_user
    app.dependency_overrides[get_db] = fake_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            return await client.get(path, params={"q": query})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_appointments_endpoint_uses_canonical_path(
    authenticated_client,
    test_patient,
    test_user,
):
    response = await authenticated_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": test_patient.id,
            "doctor_id": test_user.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "11:00:00",
            "duration_minutes": 30,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == test_patient.id

    legacy_response = await authenticated_client.get("/api/v1/appointments/appointments")
    assert legacy_response.status_code == 404


@pytest.mark.asyncio
async def test_medicine_search_endpoint_is_not_captured_by_id_route(
):
    medicine = SimpleNamespace(
        id=42,
        name_en="Arnica Montana",
        name_bn="আর্নিকা",
        system="homeopathy",
        category="Plant",
        potency="30C",
    )
    response = await _request_with_fake_db(
        "/api/v1/medicines/search",
        [
            _FakeExecuteResult(scalars=[]),
            _FakeExecuteResult(rows=[(medicine, "Bruise remedy")]),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == medicine.id
    assert body[0]["matched_alias"] == "Bruise remedy"


@pytest.mark.asyncio
async def test_symptom_search_endpoint_is_not_captured_by_id_route(
):
    symptom = SimpleNamespace(
        id=24,
        tenant_id="test-tenant",
        name_en="Headache",
        name_bn="মাথাব্যথা",
        description_en=None,
        description_bn=None,
        category="neurological",
        is_global=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )
    response = await _request_with_fake_db(
        "/api/v1/symptoms/search",
        [
            _FakeExecuteResult(scalars=[]),
            _FakeExecuteResult(rows=[(symptom, "Migraine")]),
        ],
        query="migraine",
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["symptom"]["id"] == symptom.id
    assert body[0]["matched_term"] == "Migraine"
