"""Integration tests for the public API (D4) — unauthenticated; counts only for the catalogs."""

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


# ===== Stats: no auth, aggregates only, tenant-owned data excluded =====


@pytest.mark.asyncio
async def test_public_stats_requires_no_auth_and_counts_only_global(
    client, global_medicine, tenant_medicine, global_symptom, tenant_symptom
):
    response = await client.get("/api/v1/public/stats")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"medicines", "symptoms", "institutions", "clinics", "practitioners"}
    assert body["medicines"] == 1  # the tenant-owned one is not counted
    assert body["symptoms"] == 1
    assert body["clinics"] >= 1
    assert "public" in response.headers["cache-control"]


@pytest.mark.asyncio
async def test_public_stats_excludes_unapproved_clinics(client, db_session, tenant_a):
    before = (await client.get("/api/v1/public/stats")).json()["clinics"]
    tenant_a.is_approved = False
    await db_session.commit()

    after = (await client.get("/api/v1/public/stats")).json()["clinics"]
    assert after == before - 1


# ===== The catalogs are no longer public =====


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/public/medicines",
        "/api/v1/public/medicines/search?q=arn",
        "/api/v1/public/medicines/1",
        "/api/v1/public/symptoms",
        "/api/v1/public/symptoms/search?q=head",
        "/api/v1/public/symptoms/1",
    ],
)
async def test_catalog_browse_and_search_are_gone(client, global_medicine, global_symptom, path):
    assert (await client.get(path)).status_code == 404
