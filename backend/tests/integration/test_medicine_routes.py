"""Integration tests for medicine API routes — global/tenant catalog visibility."""

from uuid import uuid4

import pytest

from app.core.security import create_access_token
from app.shared.models import Medicine, MedicineAlias, Symptom, Tenant, User


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
async def global_medicine(db_session):
    medicine = Medicine(
        tenant_id=None,
        name_en="Arnica Montana",
        system="homeopathy",
        is_global=True,
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)
    return medicine


@pytest.fixture
async def tenant_b_medicine(db_session, tenant_b):
    medicine = Medicine(
        tenant_id=tenant_b.id,
        name_en="Tenant B Private Medicine",
        system="homeopathy",
        is_global=False,
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)
    return medicine


# ===== Create =====


@pytest.mark.asyncio
async def test_create_medicine_tenant_specific(client, headers_a):
    response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Belladonna", "system": "homeopathy"},
        headers=headers_a,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name_en"] == "Belladonna"
    assert data["is_global"] is False


@pytest.mark.asyncio
async def test_create_global_medicine_requires_admin(client, headers_a):
    response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Nux Vomica", "system": "homeopathy", "is_global": True},
        headers=headers_a,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_global_medicine_as_admin(client, admin_headers):
    response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Pulsatilla", "system": "homeopathy", "is_global": True},
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_global"] is True
    assert data["tenant_id"] is None


# ===== Visibility =====


@pytest.mark.asyncio
async def test_list_medicines_sees_global_and_own_not_other_tenant(
    client, headers_a, global_medicine, tenant_b_medicine
):
    response = await client.get("/api/v1/medicines/", headers=headers_a)

    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}
    assert global_medicine.id in ids
    assert tenant_b_medicine.id not in ids


@pytest.mark.asyncio
async def test_get_other_tenants_medicine_is_404(client, headers_a, tenant_b_medicine):
    response = await client.get(f"/api/v1/medicines/{tenant_b_medicine.id}", headers=headers_a)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_global_medicine_visible_to_any_tenant(client, headers_a, global_medicine):
    response = await client.get(f"/api/v1/medicines/{global_medicine.id}", headers=headers_a)

    assert response.status_code == 200
    assert response.json()["id"] == global_medicine.id


@pytest.mark.asyncio
async def test_admin_sees_only_global_medicines(
    client, admin_headers, global_medicine, tenant_b_medicine
):
    response = await client.get("/api/v1/medicines/", headers=admin_headers)

    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}
    assert global_medicine.id in ids
    assert tenant_b_medicine.id not in ids


# ===== Update / Delete =====


@pytest.mark.asyncio
async def test_update_own_medicine(client, headers_a):
    create_response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Rhus Tox", "system": "homeopathy"},
        headers=headers_a,
    )
    medicine_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/medicines/{medicine_id}",
        json={"category": "Plant"},
        headers=headers_a,
    )

    assert response.status_code == 200
    assert response.json()["category"] == "Plant"


@pytest.mark.asyncio
async def test_cannot_update_global_medicine_even_as_admin(
    client, admin_headers, global_medicine
):
    """Pre-existing behavior, preserved by this refactor: not even an admin
    can edit a global row through this endpoint."""
    response = await client.patch(
        f"/api/v1/medicines/{global_medicine.id}",
        json={"category": "Plant"},
        headers=admin_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_update_other_tenants_medicine(client, headers_a, tenant_b_medicine):
    response = await client.patch(
        f"/api/v1/medicines/{tenant_b_medicine.id}",
        json={"category": "Plant"},
        headers=headers_a,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_own_medicine_deactivates(client, headers_a):
    create_response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Sepia", "system": "homeopathy"},
        headers=headers_a,
    )
    medicine_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/medicines/{medicine_id}", headers=headers_a)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/medicines/{medicine_id}", headers=headers_a)
    assert get_response.json()["is_active"] is False


# ===== Search =====


@pytest.mark.asyncio
async def test_search_medicines_by_name(client, headers_a, global_medicine):
    response = await client.get(
        "/api/v1/medicines/search", params={"q": "arnica"}, headers=headers_a
    )

    assert response.status_code == 200
    names = [r["name_en"] for r in response.json()]
    assert global_medicine.name_en in names


@pytest.mark.asyncio
async def test_search_medicines_by_alias(client, headers_a, db_session, global_medicine):
    alias = MedicineAlias(
        medicine_id=global_medicine.id,
        tenant_id=None,
        alias_en="arnika",
        alias_type="transliteration",
        is_active=True,
    )
    db_session.add(alias)
    await db_session.commit()

    response = await client.get(
        "/api/v1/medicines/search", params={"q": "arnika"}, headers=headers_a
    )

    assert response.status_code == 200
    results = response.json()
    assert any(r["id"] == global_medicine.id and r["matched_alias"] == "arnika" for r in results)


# ===== Aliases =====


@pytest.mark.asyncio
async def test_alias_crud(client, headers_a):
    create_response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Ignatia", "system": "homeopathy"},
        headers=headers_a,
    )
    medicine_id = create_response.json()["id"]

    create_alias_response = await client.post(
        f"/api/v1/medicines/{medicine_id}/aliases",
        json={"medicine_id": medicine_id, "alias_en": "Ignatia amara"},
        headers=headers_a,
    )
    assert create_alias_response.status_code == 201
    alias_id = create_alias_response.json()["id"]

    list_response = await client.get(
        f"/api/v1/medicines/{medicine_id}/aliases", headers=headers_a
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = await client.delete(f"/api/v1/medicines/aliases/{alias_id}", headers=headers_a)
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_other_tenants_alias(client, headers_a, headers_b):
    create_response = await client.post(
        "/api/v1/medicines/",
        json={"name_en": "Lycopodium", "system": "homeopathy"},
        headers=headers_a,
    )
    medicine_id = create_response.json()["id"]

    alias_response = await client.post(
        f"/api/v1/medicines/{medicine_id}/aliases",
        json={"medicine_id": medicine_id, "alias_en": "Lyco"},
        headers=headers_a,
    )
    alias_id = alias_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/medicines/aliases/{alias_id}", headers=headers_b)
    assert delete_response.status_code == 404


# ===== Mappings + cross-lookups =====


@pytest.mark.asyncio
async def test_mapping_crud_and_cross_lookups(client, headers_a, db_session, tenant_a):
    medicine = Medicine(
        tenant_id=tenant_a.id, name_en="Aconite", system="homeopathy", is_active=True
    )
    symptom = Symptom(tenant_id=tenant_a.id, name_en="Sudden fever", is_active=True)
    db_session.add_all([medicine, symptom])
    await db_session.commit()
    await db_session.refresh(medicine)
    await db_session.refresh(symptom)

    create_response = await client.post(
        "/api/v1/medicines/mappings",
        json={"medicine_id": medicine.id, "symptom_id": symptom.id, "strength": 7},
        headers=headers_a,
    )
    assert create_response.status_code == 201
    mapping_id = create_response.json()["id"]

    duplicate_response = await client.post(
        "/api/v1/medicines/mappings",
        json={"medicine_id": medicine.id, "symptom_id": symptom.id, "strength": 5},
        headers=headers_a,
    )
    assert duplicate_response.status_code == 400

    update_response = await client.patch(
        f"/api/v1/medicines/mappings/{mapping_id}",
        json={"strength": 9},
        headers=headers_a,
    )
    assert update_response.status_code == 200
    assert update_response.json()["strength"] == 9

    symptoms_for_medicine = await client.get(
        f"/api/v1/medicines/{medicine.id}/symptoms", headers=headers_a
    )
    assert symptoms_for_medicine.status_code == 200
    assert any(s["id"] == symptom.id for s in symptoms_for_medicine.json())

    medicines_for_symptom = await client.get(
        f"/api/v1/medicines/symptoms/{symptom.id}/medicines", headers=headers_a
    )
    assert medicines_for_symptom.status_code == 200
    assert any(m["id"] == medicine.id for m in medicines_for_symptom.json())

    delete_response = await client.delete(
        f"/api/v1/medicines/mappings/{mapping_id}", headers=headers_a
    )
    assert delete_response.status_code == 204
