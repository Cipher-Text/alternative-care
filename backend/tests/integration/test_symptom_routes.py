"""Integration tests for symptom API routes — global/tenant catalog visibility."""

from uuid import uuid4

import pytest

from app.core.security import create_access_token
from app.shared.models import Symptom, SymptomAlias, Tenant, User


@pytest.fixture
async def tenant_a(db_session):
    tenant = Tenant(
        id=str(uuid4()),
        name="Clinic A",
        email="a@clinic.com",
        clinic_name="Clinic A",
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
async def tenant_b(db_session):
    tenant = Tenant(
        id=str(uuid4()),
        name="Clinic B",
        email="b@clinic.com",
        clinic_name="Clinic B",
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
async def doctor_a(db_session, tenant_a):
    doctor = User(
        id=str(uuid4()),
        tenant_id=tenant_a.id,
        email="doctor.a@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Dr. A",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def doctor_b(db_session, tenant_b):
    doctor = User(
        id=str(uuid4()),
        tenant_id=tenant_b.id,
        email="doctor.b@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Dr. B",
        role="doctor",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def admin(db_session):
    user = User(
        id=str(uuid4()),
        tenant_id=None,
        email="admin@test.com",
        password_hash="$2b$12$test_hash_for_testing_only",
        full_name="Platform Admin",
        role="admin",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers_a(doctor_a):
    return _headers(doctor_a)


@pytest.fixture
def headers_b(doctor_b):
    return _headers(doctor_b)


@pytest.fixture
def admin_headers(admin):
    return _headers(admin)


@pytest.fixture
async def global_symptom(db_session):
    symptom = Symptom(
        tenant_id=None,
        name_en="Headache",
        category="neurological",
        is_global=True,
        is_active=True,
    )
    db_session.add(symptom)
    await db_session.commit()
    await db_session.refresh(symptom)
    return symptom


@pytest.fixture
async def tenant_b_symptom(db_session, tenant_b):
    symptom = Symptom(
        tenant_id=tenant_b.id,
        name_en="Tenant B Private Symptom",
        is_global=False,
        is_active=True,
    )
    db_session.add(symptom)
    await db_session.commit()
    await db_session.refresh(symptom)
    return symptom


# ===== Create =====


@pytest.mark.asyncio
async def test_create_symptom_tenant_specific(client, headers_a):
    response = await client.post(
        "/api/v1/symptoms/", json={"name_en": "Nausea"}, headers=headers_a
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name_en"] == "Nausea"
    assert data["is_global"] is False


@pytest.mark.asyncio
async def test_create_global_symptom_requires_admin(client, headers_a):
    response = await client.post(
        "/api/v1/symptoms/",
        json={"name_en": "Fever", "is_global": True},
        headers=headers_a,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_global_symptom_as_admin(client, admin_headers):
    response = await client.post(
        "/api/v1/symptoms/",
        json={"name_en": "Chills", "is_global": True},
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_global"] is True
    assert data["tenant_id"] is None


# ===== Visibility (also regression-covers the tenant_id nullability schema fix) =====


@pytest.mark.asyncio
async def test_list_symptoms_sees_global_and_own_not_other_tenant(
    client, headers_a, global_symptom, tenant_b_symptom
):
    response = await client.get("/api/v1/symptoms/", headers=headers_a)

    assert response.status_code == 200
    ids = {s["id"] for s in response.json()}
    assert global_symptom.id in ids
    assert tenant_b_symptom.id not in ids


@pytest.mark.asyncio
async def test_get_other_tenants_symptom_is_404(client, headers_a, tenant_b_symptom):
    response = await client.get(f"/api/v1/symptoms/{tenant_b_symptom.id}", headers=headers_a)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_global_symptom_visible_to_any_tenant(client, headers_a, global_symptom):
    """Regression test: SymptomResponse.tenant_id used to be a required
    (non-null) str, which would 500 serializing this exact response for
    any global symptom, since the DB column is nullable."""
    response = await client.get(f"/api/v1/symptoms/{global_symptom.id}", headers=headers_a)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == global_symptom.id
    assert body["tenant_id"] is None


@pytest.mark.asyncio
async def test_admin_sees_only_global_symptoms(
    client, admin_headers, global_symptom, tenant_b_symptom
):
    response = await client.get("/api/v1/symptoms/", headers=admin_headers)

    assert response.status_code == 200
    ids = {s["id"] for s in response.json()}
    assert global_symptom.id in ids
    assert tenant_b_symptom.id not in ids


# ===== Update / Delete =====


@pytest.mark.asyncio
async def test_update_own_symptom(client, headers_a):
    create_response = await client.post(
        "/api/v1/symptoms/", json={"name_en": "Cough"}, headers=headers_a
    )
    symptom_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/symptoms/{symptom_id}",
        json={"category": "respiratory"},
        headers=headers_a,
    )

    assert response.status_code == 200
    assert response.json()["category"] == "respiratory"


@pytest.mark.asyncio
async def test_cannot_update_global_symptom_even_as_admin(
    client, admin_headers, global_symptom
):
    """Pre-existing behavior, preserved by this refactor: not even an admin
    can edit a global row through this endpoint."""
    response = await client.patch(
        f"/api/v1/symptoms/{global_symptom.id}",
        json={"category": "respiratory"},
        headers=admin_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_update_other_tenants_symptom(client, headers_a, tenant_b_symptom):
    response = await client.patch(
        f"/api/v1/symptoms/{tenant_b_symptom.id}",
        json={"category": "respiratory"},
        headers=headers_a,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_own_symptom_deactivates(client, headers_a):
    create_response = await client.post(
        "/api/v1/symptoms/", json={"name_en": "Dizziness"}, headers=headers_a
    )
    symptom_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/symptoms/{symptom_id}", headers=headers_a)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/symptoms/{symptom_id}", headers=headers_a)
    assert get_response.json()["is_active"] is False


# ===== Search =====


@pytest.mark.asyncio
async def test_search_symptoms_by_name(client, headers_a, global_symptom):
    response = await client.get(
        "/api/v1/symptoms/search", params={"q": "head"}, headers=headers_a
    )

    assert response.status_code == 200
    names = [r["symptom"]["name_en"] for r in response.json()]
    assert global_symptom.name_en in names


@pytest.mark.asyncio
async def test_search_symptoms_by_alias(client, headers_a, db_session, global_symptom):
    alias = SymptomAlias(
        symptom_id=global_symptom.id,
        tenant_id=None,
        alias_en="matha byatha",
        alias_type="transliteration",
        is_active=True,
    )
    db_session.add(alias)
    await db_session.commit()

    response = await client.get(
        "/api/v1/symptoms/search", params={"q": "matha"}, headers=headers_a
    )

    assert response.status_code == 200
    results = response.json()
    assert any(
        r["symptom"]["id"] == global_symptom.id and r["matched_term"] == "matha byatha"
        for r in results
    )


# ===== Aliases =====


@pytest.mark.asyncio
async def test_alias_crud(client, headers_a):
    create_response = await client.post(
        "/api/v1/symptoms/", json={"name_en": "Vomiting"}, headers=headers_a
    )
    symptom_id = create_response.json()["id"]

    create_alias_response = await client.post(
        f"/api/v1/symptoms/{symptom_id}/aliases",
        json={"symptom_id": symptom_id, "alias_en": "Throwing up"},
        headers=headers_a,
    )
    assert create_alias_response.status_code == 201
    alias_id = create_alias_response.json()["id"]

    list_response = await client.get(
        f"/api/v1/symptoms/{symptom_id}/aliases", headers=headers_a
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = await client.delete(f"/api/v1/symptoms/aliases/{alias_id}", headers=headers_a)
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_other_tenants_alias(client, headers_a, headers_b):
    create_response = await client.post(
        "/api/v1/symptoms/", json={"name_en": "Rash"}, headers=headers_a
    )
    symptom_id = create_response.json()["id"]

    alias_response = await client.post(
        f"/api/v1/symptoms/{symptom_id}/aliases",
        json={"symptom_id": symptom_id, "alias_en": "Skin rash"},
        headers=headers_a,
    )
    alias_id = alias_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/symptoms/aliases/{alias_id}", headers=headers_b
    )
    assert delete_response.status_code == 404
