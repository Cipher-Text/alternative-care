"""Integration tests for the public API (D4) — unauthenticated, global-catalog-only."""

from uuid import uuid4

import pytest

from app.shared.models import Medicine, Symptom, Tenant


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
async def tenant_medicine(db_session, tenant_a):
    medicine = Medicine(
        tenant_id=tenant_a.id,
        name_en="Tenant A Private Medicine",
        system="homeopathy",
        is_global=False,
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)
    return medicine


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
async def tenant_symptom(db_session, tenant_a):
    symptom = Symptom(
        tenant_id=tenant_a.id,
        name_en="Tenant A Private Symptom",
        is_global=False,
        is_active=True,
    )
    db_session.add(symptom)
    await db_session.commit()
    await db_session.refresh(symptom)
    return symptom


# ===== No auth required =====


@pytest.mark.asyncio
async def test_public_medicines_requires_no_auth(client, global_medicine):
    response = await client.get("/api/v1/public/medicines")

    assert response.status_code == 200
    names = [m["name_en"] for m in response.json()]
    assert global_medicine.name_en in names


@pytest.mark.asyncio
async def test_public_symptoms_requires_no_auth(client, global_symptom):
    response = await client.get("/api/v1/public/symptoms")

    assert response.status_code == 200
    names = [s["name_en"] for s in response.json()]
    assert global_symptom.name_en in names


# ===== Tenant-owned data is never visible =====


@pytest.mark.asyncio
async def test_public_medicines_excludes_tenant_owned(
    client, global_medicine, tenant_medicine
):
    response = await client.get("/api/v1/public/medicines")

    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert global_medicine.id in ids
    assert tenant_medicine.id not in ids


@pytest.mark.asyncio
async def test_public_get_tenant_medicine_is_404(client, tenant_medicine):
    response = await client.get(f"/api/v1/public/medicines/{tenant_medicine.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_symptoms_excludes_tenant_owned(
    client, global_symptom, tenant_symptom
):
    response = await client.get("/api/v1/public/symptoms")

    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert global_symptom.id in ids
    assert tenant_symptom.id not in ids


@pytest.mark.asyncio
async def test_public_get_tenant_symptom_is_404(client, tenant_symptom):
    response = await client.get(f"/api/v1/public/symptoms/{tenant_symptom.id}")

    assert response.status_code == 404


# ===== Get global row =====


@pytest.mark.asyncio
async def test_public_get_global_medicine(client, global_medicine):
    response = await client.get(f"/api/v1/public/medicines/{global_medicine.id}")

    assert response.status_code == 200
    assert response.json()["name_en"] == global_medicine.name_en


# ===== Search — unified tsvector search (D5), including prefix matching =====


@pytest.mark.asyncio
async def test_public_medicine_search_full_word(client, global_medicine):
    response = await client.get(
        "/api/v1/public/medicines/search", params={"q": "arnica"}
    )

    assert response.status_code == 200
    names = [r["name_en"] for r in response.json()]
    assert global_medicine.name_en in names


@pytest.mark.asyncio
async def test_public_medicine_search_partial_word_prefix_match(client, global_medicine):
    """Autocomplete-as-you-type: a partial word must match via tsvector prefix search."""
    response = await client.get(
        "/api/v1/public/medicines/search", params={"q": "arni"}
    )

    assert response.status_code == 200
    names = [r["name_en"] for r in response.json()]
    assert global_medicine.name_en in names


@pytest.mark.asyncio
async def test_public_medicine_search_excludes_tenant_owned(
    client, global_medicine, tenant_medicine
):
    response = await client.get(
        "/api/v1/public/medicines/search", params={"q": "medicine"}
    )

    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert tenant_medicine.id not in ids


@pytest.mark.asyncio
async def test_public_symptom_search_partial_word_prefix_match(client, global_symptom):
    response = await client.get(
        "/api/v1/public/symptoms/search", params={"q": "head"}
    )

    assert response.status_code == 200
    names = [r["symptom"]["name_en"] for r in response.json()]
    assert global_symptom.name_en in names
