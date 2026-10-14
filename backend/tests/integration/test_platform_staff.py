"""The platform team: platform staff, platform-level roles and the global audit trail (ADR 010, Phase 4)."""

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core import permission_cache
from app.core.config import settings
from app.core.permissions import PLATFORM_PERMISSIONS, system_role_id
from app.core.rbac import sync_catalogue_async
from app.core.security import create_access_token, get_password_hash
from app.shared.models import User
from app.shared.models.rbac import Role, UserRole

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
ADMIN, OPERATOR = system_role_id("admin"), system_role_id("operator")
BASE = "/api/v1/admin/staff"


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.setattr(settings, "PERMISSION_CACHE_SECONDS", 0)
    permission_cache.invalidate_all()
    sent = []
    monkeypatch.setattr("app.modules.team.service.send_system_email_task.delay", lambda **kw: sent.append(kw))
    return sent


@pytest.fixture
async def seeded(db_session):
    await sync_catalogue_async(db_session)
    await db_session.commit()


async def _staff(db, role="admin", name="Staff"):
    user = User(
        id=str(uuid.uuid4()), tenant_id=None, email=f"{uuid.uuid4().hex[:8]}@platform.test", password_hash=get_password_hash("Test@1234"),
        full_name=name, role=role, is_active=True, is_email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _token(user):
    return create_access_token(
        {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role, "email": user.email, "plan": None, "token_version": user.token_version}
    )


async def _role(client, token, name, permissions, **extra):
    return await client.post(f"{BASE}/roles", json={"name_en": name, "permissions": permissions, **extra}, headers=H(token))


@pytest.fixture
async def admin(db_session, seeded):
    user = await _staff(db_session, "admin", "Root admin")
    return user.id, _token(user)


async def _keys(db, user_id):
    rows = await db.execute(select(Role.key).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id))
    return sorted(rows.scalars().all())


# ----- who may look and who may change ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_operator_can_look_but_not_change_and_clinic_staff_are_refused(client, db_session, admin, test_tenant):
    operator = await _staff(db_session, "operator", "Op")
    op = _token(operator)
    for path in ("roles", "members", "permissions", "audit"):
        assert (await client.get(f"{BASE}/{path}", headers=H(op))).status_code == 200, path
    assert (await _role(client, op, "Nope", ["tenants.read"])).status_code == 403
    assert (await client.post(f"{BASE}/members", json={"email": "x@platformteam.com", "full_name": "X Y", "role_ids": [OPERATOR]}, headers=H(op))).status_code == 403

    clinic_user = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="owner@clinicx.test", password_hash=get_password_hash("Test@1234"),
        full_name="Owner", role="doctor", is_active=True, is_email_verified=True,
    )
    db_session.add(clinic_user)
    await db_session.commit()
    await db_session.refresh(clinic_user)
    assert (await client.get(f"{BASE}/roles", headers=H(_token(clinic_user)))).status_code == 403
    assert (await client.get(f"{BASE}/roles")).status_code == 401


@pytest.mark.asyncio
async def test_the_platform_sees_platform_roles_and_permissions_only(client, admin):
    _, token = admin
    roles = {r["key"]: r for r in (await client.get(f"{BASE}/roles", headers=H(token))).json()}
    assert set(roles) == {"admin", "operator"} and roles["admin"]["is_system"] and not roles["admin"]["can_edit"]
    catalogue = (await client.get(f"{BASE}/permissions", headers=H(token))).json()
    assert {p["key"] for p in catalogue} == {p.key for p in PLATFORM_PERMISSIONS}
    members = (await client.get(f"{BASE}/members", headers=H(token))).json()
    assert [m["full_name"] for m in members] == ["Root admin"] and members[0]["is_you"]


# ----- roles ------------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_support_role_can_be_made_and_given_to_new_staff(client, db_session, admin, _fresh):
    _, token = admin
    created = await _role(client, token, "Support", ["tenants.read", "users.read", "contact.manage"], name_bn="সাপোর্ট")
    assert created.status_code == 201, created.text
    role = created.json()
    assert role["can_edit"] and not role["is_system"]

    invited = await client.post(f"{BASE}/members", json={"email": "Sam@PlatformTeam.com", "full_name": "Sam Support", "role_ids": [role["id"]]}, headers=H(token))
    assert invited.status_code == 201, invited.text
    body = invited.json()
    assert body["email"] == "sam@platformteam.com" and [r["name_en"] for r in body["roles"]] == ["Support"]
    assert _fresh and "reset-password?token=" in _fresh[0]["body_text"] and "platform team" in _fresh[0]["subject"]
    user = (await db_session.execute(select(User).where(User.id == body["id"]))).scalar_one()
    assert user.tenant_id is None and user.role == "operator"
    assert await _keys(db_session, user.id) == [role["key"]]  # the custom role only: no system role came with it

    sam = _token(user)
    assert (await client.get("/api/v1/admin/contact", headers=H(sam))).status_code == 200  # what the role allows
    assert (await client.get("/api/v1/admin/plans", headers=H(sam))).status_code == 403  # what it does not
    assert (await client.get("/api/v1/admin/dashboard", headers=H(sam))).status_code == 200


@pytest.mark.asyncio
async def test_platform_roles_cannot_carry_clinic_permissions(client, admin):
    _, token = admin
    for bad in (["team.read"], ["patients.read"], ["tenants.read", "nonsense.key"]):
        r = await _role(client, token, "Bad", bad)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_permissions", bad


@pytest.mark.asyncio
async def test_sensitive_platform_permissions_need_acknowledgement(client, admin):
    _, token = admin
    r = await _role(client, token, "Finance", ["billing.admin", "tenants.read"])
    assert r.status_code == 422 and r.json()["detail"]["code"] == "sensitive_not_acknowledged"
    assert (await _role(client, token, "Finance", ["billing.admin", "tenants.read"], acknowledge_sensitive=True)).status_code == 201


@pytest.mark.asyncio
async def test_system_platform_roles_are_locked(client, admin):
    _, token = admin
    for role_id in (ADMIN, OPERATOR):
        assert (await client.patch(f"{BASE}/roles/{role_id}", json={"name_en": "Hacked"}, headers=H(token))).status_code == 403
        assert (await client.delete(f"{BASE}/roles/{role_id}", headers=H(token))).status_code == 403


@pytest.mark.asyncio
async def test_clinic_roles_are_not_visible_or_editable_from_the_platform_page(client, db_session, admin, test_tenant):
    _, token = admin
    # the global clinic-level templates exist (doctor, receptionist) but are not platform roles
    for role_id in (system_role_id("doctor"), system_role_id("receptionist")):
        assert (await client.patch(f"{BASE}/roles/{role_id}", json={"name_en": "Hacked"}, headers=H(token))).status_code == 404


# ----- rule 1: no escalation --------------------------------------------------------------------------------------------


@pytest.fixture
async def role_manager(client, db_session, admin):
    """Someone who may manage roles and staff but does not hold billing.admin or content.manage."""
    _, admin_token = admin
    role = (await _role(client, admin_token, "Role manager", ["users.read", "roles.manage_global", "tenants.read", "audit.read"], acknowledge_sensitive=True)).json()
    person = await _staff(db_session, "operator", "Manager")
    assert (await client.put(f"{BASE}/members/{person.id}/roles", json={"role_ids": [role["id"]]}, headers=H(admin_token))).status_code == 200
    return person.id, _token(person), role


@pytest.mark.asyncio
async def test_a_role_manager_cannot_grant_what_they_do_not_hold(client, db_session, role_manager, admin):
    _, token, role = role_manager
    r = await _role(client, token, "Sneaky", ["tenants.read", "billing.admin"], acknowledge_sensitive=True)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "cannot_grant"
    assert (await _role(client, token, "Fine", ["tenants.read"])).status_code == 201
    widen = await client.patch(f"{BASE}/roles/{role['id']}", json={"permissions": ["users.read", "roles.manage_global", "plans.manage"], "acknowledge_sensitive": True}, headers=H(token))
    assert widen.status_code == 403 and widen.json()["detail"]["code"] == "cannot_grant"
    # nor can they assign the admin role, or touch an admin
    other = await _staff(db_session, "operator", "Other")
    assert (await client.put(f"{BASE}/members/{other.id}/roles", json={"role_ids": [ADMIN]}, headers=H(token))).status_code == 403
    admin_id, _ = admin
    assert (await client.patch(f"{BASE}/members/{admin_id}/status", json={"is_active": False}, headers=H(token))).status_code == 403


# ----- rule 3: the platform always has someone who can manage roles -----------------------------------------------------


@pytest.mark.asyncio
async def test_the_last_admin_cannot_be_demoted_or_switched_off(client, db_session, admin):
    admin_id, token = admin
    r = await client.put(f"{BASE}/members/{admin_id}/roles", json={"role_ids": [OPERATOR]}, headers=H(token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"
    assert (await client.patch(f"{BASE}/members/{admin_id}/status", json={"is_active": False}, headers=H(token))).status_code == 400  # not yourself
    # the older admin page cannot be used to get around it
    r = await client.patch(f"/api/v1/admin/users/{admin_id}", json={"is_active": False}, headers=H(token))
    assert r.status_code == 400 and "last active person" in r.json()["detail"]


@pytest.mark.asyncio
async def test_with_a_second_admin_the_first_can_step_down(client, db_session, admin):
    admin_id, token = admin
    await _staff(db_session, "admin", "Second admin")
    r = await client.put(f"{BASE}/members/{admin_id}/roles", json={"role_ids": [OPERATOR]}, headers=H(token))
    assert r.status_code == 200 and [x["key"] for x in r.json()["roles"]] == ["operator"]
    await db_session.refresh(await db_session.get(User, admin_id))
    assert (await db_session.get(User, admin_id)).role == "operator"


@pytest.mark.asyncio
async def test_the_legacy_role_follows_whoever_can_manage_roles(client, db_session, admin):
    _, token = admin
    role = (await _role(client, token, "Role manager", ["users.read", "roles.manage_global"], acknowledge_sensitive=True)).json()
    person = await _staff(db_session, "operator", "Becoming admin")
    assert (await client.put(f"{BASE}/members/{person.id}/roles", json={"role_ids": [role["id"]]}, headers=H(token))).status_code == 200
    await db_session.refresh(person)
    assert person.role == "admin"
    assert (await client.put(f"{BASE}/members/{person.id}/roles", json={"role_ids": [OPERATOR]}, headers=H(token))).status_code == 200
    await db_session.refresh(person)
    assert person.role == "operator"


@pytest.mark.asyncio
async def test_platform_roles_can_no_longer_be_changed_through_the_users_page(client, db_session, admin):
    _, token = admin
    other = await _staff(db_session, "operator", "Op2")
    r = await client.patch(f"/api/v1/admin/users/{other.id}", json={"role": "admin"}, headers=H(token))
    assert r.status_code == 400 and "Platform team" in r.json()["detail"]


# ----- audit ----------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_global_audit_shows_platform_and_clinic_changes(client, db_session, admin, test_tenant):
    _, token = admin
    await _role(client, token, "Support", ["tenants.read"])
    owner = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="owner@audit.test", password_hash=get_password_hash("Test@1234"),
        full_name="Clinic owner", role="doctor", is_active=True, is_email_verified=True,
    )
    db_session.add(owner)
    test_tenant.plan = "pro"
    await db_session.commit()
    await db_session.refresh(owner)
    made = await client.post(f"/api/v1/admin/tenants/{test_tenant.id}/team/roles", json={"name_en": "Accountant", "permissions": ["payments.read"]}, headers=H(token))
    assert made.status_code == 201, made.text

    everything = (await client.get(f"{BASE}/audit", headers=H(token))).json()
    assert everything["total"] == 2
    by_name = {a["role_name"]: a for a in everything["items"]}
    assert by_name["Support"]["clinic_name"] is None and by_name["Accountant"]["clinic_name"] == test_tenant.clinic_name
    assert [a["role_name"] for a in (await client.get(f"{BASE}/audit?level=platform", headers=H(token))).json()["items"]] == ["Support"]
    assert [a["role_name"] for a in (await client.get(f"{BASE}/audit?level=clinic", headers=H(token))).json()["items"]] == ["Accountant"]
    # a clinic still sees only its own trail
    own = (await client.get("/api/v1/team/audit", headers=H(_token(owner)))).json()
    assert [a["role_name"] for a in own["items"]] == ["Accountant"]
