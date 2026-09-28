"""Integration tests for the college/institution catalog (Track D)."""

from uuid import uuid4

import pytest

from app.core.security import create_access_token
from app.shared.models import College, Tenant, User


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
def admin_headers(admin):
    return _headers(admin)


@pytest.fixture
async def college(db_session):
    college = College(
        name_en="Government Homeopathic Medical College & Hospital",
        college_type="government",
        disciplines=["homeopathy"],
        courses_offered="DHMS",
        location="Mirpur-14, Dhaka",
        is_active=True,
    )
    db_session.add(college)
    await db_session.commit()
    await db_session.refresh(college)
    return college


# ===== Create =====


@pytest.mark.asyncio
async def test_create_college_requires_admin(client, headers_a):
    response = await client.post(
        "/api/v1/colleges/",
        json={
            "name_en": "Test College",
            "college_type": "private",
            "disciplines": ["unani"],
        },
        headers=headers_a,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_college_as_admin(client, admin_headers):
    response = await client.post(
        "/api/v1/colleges/",
        json={
            "name_en": "Hamdard Unani Medical College & Hospital",
            "college_type": "private",
            "disciplines": ["unani"],
            "courses_offered": "DUMS",
            "source_url": "https://hamdardfoundationbd.org/hamdard-unani-medical-college-hospital/",
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["college_type"] == "private"
    assert data["disciplines"] == ["unani"]
    assert data["is_verified"] is False


# ===== Read =====


@pytest.mark.asyncio
async def test_list_colleges(client, headers_a, college):
    response = await client.get("/api/v1/colleges/", headers=headers_a)

    assert response.status_code == 200
    names = [c["name_en"] for c in response.json()]
    assert college.name_en in names


@pytest.mark.asyncio
async def test_list_colleges_filter_by_discipline(client, headers_a, college):
    response = await client.get(
        "/api/v1/colleges/", params={"discipline": "unani"}, headers=headers_a
    )

    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert college.id not in ids


@pytest.mark.asyncio
async def test_get_college(client, headers_a, college):
    response = await client.get(f"/api/v1/colleges/{college.id}", headers=headers_a)

    assert response.status_code == 200
    assert response.json()["name_en"] == college.name_en


# ===== Update / verification =====


@pytest.mark.asyncio
async def test_update_college_requires_admin(client, headers_a, college):
    response = await client.patch(
        f"/api/v1/colleges/{college.id}",
        json={"location": "Somewhere else"},
        headers=headers_a,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_college_stamps_verified_at(client, admin_headers, college):
    assert college.is_verified is False

    response = await client.patch(
        f"/api/v1/colleges/{college.id}",
        json={"is_verified": True},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] is True
    assert data["verified_at"] is not None
    assert data["verified_by"] is not None


# ===== Deactivate =====


@pytest.mark.asyncio
async def test_deactivate_college_requires_admin(client, headers_a, college):
    response = await client.delete(f"/api/v1/colleges/{college.id}", headers=headers_a)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_deactivate_college_as_admin(client, admin_headers, college):
    response = await client.delete(f"/api/v1/colleges/{college.id}", headers=admin_headers)

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/colleges/{college.id}", headers=admin_headers)
    assert get_response.json()["is_active"] is False


# ===== Public directory (D4) =====


@pytest.mark.asyncio
async def test_public_colleges_requires_no_auth(client, college):
    response = await client.get("/api/v1/public/colleges")

    assert response.status_code == 200
    names = [c["name_en"] for c in response.json()]
    assert college.name_en in names


@pytest.mark.asyncio
async def test_public_college_detail_omits_verified_by(client, college):
    response = await client.get(f"/api/v1/public/colleges/{college.id}")

    assert response.status_code == 200
    assert "verified_by" not in response.json()
