"""Roles and permissions as data: the catalogue sync, the role assignment hook, and effective permissions (ADR 010)."""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core import permission_cache
from app.core.config import settings
from app.core.dependencies import CurrentUser, get_permissions, require_any_permission, require_permission
from app.core.permissions import PERMISSIONS, SYSTEM_ROLES, system_role_id
from app.core.rbac import effective_permissions, sync_catalogue_async
from app.core.security import create_access_token, get_password_hash
from app.shared.models import Role, Tenant, User
from app.shared.models.rbac import PermissionRow, RolePermission, UserRole
from fastapi import HTTPException

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731


@pytest.fixture(autouse=True)
def _no_permission_cache(monkeypatch):
    monkeypatch.setattr(settings, "PERMISSION_CACHE_SECONDS", 0)
    permission_cache.invalidate_all()


@pytest.fixture
async def seeded(db_session):
    await sync_catalogue_async(db_session)
    await db_session.commit()


def _user(role, tenant_id=None):
    return User(
        id=str(uuid.uuid4()), tenant_id=tenant_id, email=f"{uuid.uuid4().hex[:8]}@rbac.test", password_hash=get_password_hash("Test@1234"),
        full_name="Person", role=role, is_active=True, is_email_verified=True,
    )


def _tenant(name):
    return Tenant(id=str(uuid.uuid4()), name=name, email=f"{uuid.uuid4().hex[:8]}@clinic.test", specializations=["homeopathy"], is_approved=True, is_active=True, is_verified=True)


async def _held(db, user):
    return await effective_permissions(db, user.id, user.role, user.tenant_id is None)


# ----- the catalogue in the database ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_loads_the_catalogue_and_system_roles_and_is_idempotent(db_session, seeded):
    async def counts():
        return tuple([(await db_session.execute(select(func.count()).select_from(m))).scalar_one() for m in (PermissionRow, Role, RolePermission)])

    first = await counts()
    assert first == (len(PERMISSIONS), 4, sum(len(r.permissions) for r in SYSTEM_ROLES.values()))
    await sync_catalogue_async(db_session)
    await sync_catalogue_async(db_session)
    assert await counts() == first

    for key, role in SYSTEM_ROLES.items():
        row = (await db_session.execute(select(Role).where(Role.id == system_role_id(key)))).scalar_one()
        assert (row.key, row.scope, row.tenant_id, row.is_system) == (key, role.scope, None, True)
        keys = set((await db_session.execute(select(RolePermission.permission_key).where(RolePermission.role_id == row.id))).scalars())
        assert keys == set(role.permissions)


@pytest.mark.asyncio
async def test_sync_repairs_a_system_role_that_drifted(db_session, seeded):
    rid = system_role_id("receptionist")
    db_session.add(RolePermission(role_id=rid, permission_key="prescriptions.issue"))  # something it must never have
    await db_session.execute(RolePermission.__table__.delete().where(RolePermission.role_id == rid, RolePermission.permission_key == "patients.read"))
    await db_session.commit()
    await sync_catalogue_async(db_session)
    keys = set((await db_session.execute(select(RolePermission.permission_key).where(RolePermission.role_id == rid))).scalars())
    assert keys == set(SYSTEM_ROLES["receptionist"].permissions)


@pytest.mark.asyncio
async def test_role_rules_are_enforced_by_the_database(db_session, seeded):
    clinic_a, clinic_b = _tenant("A"), _tenant("B")
    db_session.add_all([clinic_a, clinic_b])
    await db_session.flush()
    a_id, b_id = clinic_a.id, clinic_b.id  # read now: a rollback below expires the objects
    ok = lambda **kw: Role(id=str(uuid.uuid4()), name_en="X", name_bn="X", is_active=True, **kw)  # noqa: E731

    # the same key can exist in two clinics, but not twice in one, and not as a global duplicate
    db_session.add_all([ok(key="assistant", scope="tenant", tenant_id=a_id), ok(key="assistant", scope="tenant", tenant_id=b_id)])
    await db_session.commit()
    db_session.add(ok(key="assistant", scope="tenant", tenant_id=a_id))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
    db_session.add(ok(key="doctor", scope="tenant", tenant_id=None))  # a second global "doctor"
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
    # a platform role is always global
    db_session.add(ok(key="clinic_platform_role", scope="platform", tenant_id=a_id))
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ----- assignment follows users.role ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_new_user_gets_their_system_role_and_a_role_change_swaps_it(db_session, seeded):
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    user = _user("receptionist", clinic.id)
    db_session.add(user)
    await db_session.commit()

    async def role_ids():
        return set((await db_session.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))).scalars())

    assert await role_ids() == {system_role_id("receptionist")}
    user.role = "doctor"
    await db_session.commit()
    assert await role_ids() == {system_role_id("doctor")}  # swapped, not added
    user.full_name = "Renamed"
    await db_session.commit()
    assert await role_ids() == {system_role_id("doctor")}


@pytest.mark.asyncio
async def test_a_user_with_no_assignment_falls_back_to_their_legacy_role(db_session):
    """Not seeded at all: nobody is locked out and nobody gets more than their role gave them."""
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    rec, doc = _user("receptionist", clinic.id), _user("doctor", clinic.id)
    db_session.add_all([rec, doc])
    await db_session.commit()
    assert await _held(db_session, rec) == SYSTEM_ROLES["receptionist"].permissions
    assert await _held(db_session, doc) == SYSTEM_ROLES["doctor"].permissions
    assert await effective_permissions(db_session, "nobody", "mystery_role", False) == frozenset()


# ----- effective permissions ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_each_system_role_resolves_to_exactly_its_set(db_session, seeded):
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    users = {
        "admin": _user("admin"), "operator": _user("operator"), "doctor": _user("doctor", clinic.id), "receptionist": _user("receptionist", clinic.id),
    }
    db_session.add_all(users.values())
    await db_session.commit()
    for key, user in users.items():
        assert await _held(db_session, user) == SYSTEM_ROLES[key].permissions, key


@pytest.mark.asyncio
async def test_several_roles_combine_and_an_inactive_role_gives_nothing(db_session, seeded):
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    user = _user("receptionist", clinic.id)
    extra = Role(id=str(uuid.uuid4()), key="assistant_doctor", name_en="Assistant doctor", name_bn="সহকারী ডাক্তার", scope="tenant", tenant_id=clinic.id, is_active=True)
    db_session.add_all([user, extra])
    await db_session.flush()
    db_session.add_all([RolePermission(role_id=extra.id, permission_key=k) for k in ("visits.write", "case_taking.write")])
    db_session.add(UserRole(user_id=user.id, role_id=extra.id))
    await db_session.commit()

    assert await _held(db_session, user) == SYSTEM_ROLES["receptionist"].permissions | {"visits.write", "case_taking.write"}

    extra.is_active = False
    await db_session.commit()
    assert await _held(db_session, user) == SYSTEM_ROLES["receptionist"].permissions


@pytest.mark.asyncio
async def test_a_permission_of_the_wrong_level_is_dropped(db_session, seeded):
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    doc = _user("doctor", clinic.id)
    db_session.add(doc)
    await db_session.flush()
    db_session.add(RolePermission(role_id=system_role_id("doctor"), permission_key="tenants.manage"))  # a corrupted grant
    await db_session.commit()
    assert "tenants.manage" not in await _held(db_session, doc)


@pytest.mark.asyncio
async def test_permissions_are_cached_until_something_invalidates_them(db_session, seeded, monkeypatch):
    monkeypatch.setattr(settings, "PERMISSION_CACHE_SECONDS", 60)
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    user = _user("receptionist", clinic.id)
    db_session.add(user)
    await db_session.commit()
    before = await _held(db_session, user)
    db_session.add(RolePermission(role_id=system_role_id("receptionist"), permission_key="visits.write"))
    await db_session.commit()
    assert await _held(db_session, user) == before  # still the cached answer
    permission_cache.invalidate_user(user.id)
    assert await _held(db_session, user) == before | {"visits.write"}


# ----- the dependency and the endpoint ------------------------------------------------------------------------------


def _current(user):
    return CurrentUser(user_id=user.id, tenant_id=user.tenant_id, role=user.role, email=user.email)


@pytest.mark.asyncio
async def test_require_permission_allows_and_refuses(db_session, seeded):
    clinic = _tenant("Clinic")
    db_session.add(clinic)
    await db_session.flush()
    rec = _user("receptionist", clinic.id)
    db_session.add(rec)
    await db_session.commit()

    assert (await require_permission("patients.read", "payments.write")(_current(rec), db_session)).user_id == rec.id
    with pytest.raises(HTTPException) as e:
        await require_permission("patients.read", "prescriptions.issue")(_current(rec), db_session)  # every one is required
    assert e.value.status_code == 403
    assert e.value.detail["code"] == "permission_denied" and e.value.detail["permission"] == "prescriptions.issue"
    assert (await require_any_permission("prescriptions.issue", "payments.write")(_current(rec), db_session)).user_id == rec.id
    with pytest.raises(HTTPException):
        await require_any_permission("prescriptions.issue", "team.manage")(_current(rec), db_session)
    # the answer is kept on the user for the rest of the request
    user = _current(rec)
    await get_permissions(user, db_session)
    assert user.permissions == SYSTEM_ROLES["receptionist"].permissions


@pytest.mark.asyncio
async def test_my_permissions_endpoint(client, doctor_token, admin_access_token, db_session, test_tenant, seeded):
    r = await client.get("/api/v1/auth/me/permissions", headers=H(doctor_token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "doctor" and body["permissions"] == sorted(SYSTEM_ROLES["doctor"].permissions)

    rec = _user("receptionist", test_tenant.id)
    db_session.add(rec)
    await db_session.commit()
    token = create_access_token({"sub": rec.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": rec.email, "plan": "pro"})
    r = await client.get("/api/v1/auth/me/permissions", headers=H(token))
    body = r.json()
    assert body["permissions"] == sorted(SYSTEM_ROLES["receptionist"].permissions)
    assert [x["key"] for x in body["roles"]] == ["receptionist"] and body["roles"][0]["is_system"] is True

    admin = (await client.get("/api/v1/auth/me/permissions", headers=H(admin_access_token))).json()
    assert set(admin["permissions"]) == SYSTEM_ROLES["admin"].permissions
    assert (await client.get("/api/v1/auth/me/permissions")).status_code == 401
