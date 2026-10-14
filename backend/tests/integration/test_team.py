"""A clinic's staff and roles (ADR 010). Only the platform changes them, acting on a clinic; the clinic itself can only look."""

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core import permission_cache
from app.core.config import settings
from app.core.permissions import SYSTEM_ROLES, system_role_id
from app.core.rbac import sync_catalogue_async
from app.core.security import create_access_token, get_password_hash
from app.shared.models import User
from app.shared.models.rbac import Role, RoleAuditLog, UserRole

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
DOCTOR, RECEPTIONIST = system_role_id("doctor"), system_role_id("receptionist")


def base(tenant_id):
    return f"/api/v1/admin/tenants/{tenant_id}/team"


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


async def _person(db, tenant, role="doctor", name="Person", tenant_id=None):
    """A clinic member: of `tenant`, or of the clinic with id `tenant_id`. A platform user has no clinic: use `_platform`."""
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant_id or tenant.id, email=f"{uuid.uuid4().hex[:8]}@team.test", password_hash=get_password_hash("Test@1234"),
        full_name=name, role=role, is_active=True, is_email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _platform(db, role="admin", name="Platform Admin"):
    user = User(
        id=str(uuid.uuid4()), tenant_id=None, email=f"{uuid.uuid4().hex[:8]}@platform.test", password_hash=get_password_hash("Test@1234"),
        full_name=name, role=role, is_active=True, is_email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _token(user):
    # with token_version, so the deactivation check against the database is exercised too
    return create_access_token(
        {"sub": user.id, "tenant_id": user.tenant_id, "role": user.role, "email": user.email, "plan": "pro", "token_version": user.token_version}
    )


async def _roles_of(db, user_id):
    rows = await db.execute(select(Role.key).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id))
    return sorted(rows.scalars().all())


@pytest.fixture
async def clinic(db_session, seeded, test_tenant):
    """A clinic with one doctor, and the platform admin who manages it. Plain ids and tokens are returned: a refused change
    rolls the (shared) test session back, which expires ORM objects."""
    test_tenant.plan = "pro"  # several practitioner seats
    await db_session.commit()
    doctor = await _person(db_session, test_tenant, "doctor", "Dr Owner")
    admin = await _platform(db_session, "admin", "Platform Admin")
    return SimpleNamespace(
        tenant_id=test_tenant.id, clinic_name=test_tenant.clinic_name, doctor_id=doctor.id, doctor=_token(doctor),
        admin_id=admin.id, admin=_token(admin), base=base(test_tenant.id),
    )


async def _role(client, c, name, permissions, **extra):
    return await client.post(f"{c.base}/roles", json={"name_en": name, "permissions": permissions, **extra}, headers=H(c.admin))


async def _set_roles(client, c, member_id, role_ids, token=None):
    return await client.put(f"{c.base}/members/{member_id}/roles", json={"role_ids": role_ids}, headers=H(token or c.admin))


# ----- who may look and who may change ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_clinic_can_look_at_its_team_but_has_no_way_to_change_it(client, db_session, clinic):
    c = clinic
    for path in ("members", "roles", "permissions", "audit"):
        assert (await client.get(f"/api/v1/team/{path}", headers=H(c.doctor))).status_code == 200, path
    # no write endpoint exists on the clinic side: contacting AltCare is the way to change anything
    for method, path in (("post", "roles"), ("patch", f"roles/{DOCTOR}"), ("delete", f"roles/{DOCTOR}"), ("post", "members"), ("put", f"members/{c.doctor_id}/roles"), ("patch", f"members/{c.doctor_id}/status")):
        r = await getattr(client, method)(f"/api/v1/team/{path}", json={}, headers=H(c.doctor)) if method != "delete" else await client.delete(f"/api/v1/team/{path}", headers=H(c.doctor))
        assert r.status_code in (404, 405), (method, path, r.status_code)
    # and the platform-side endpoints refuse a clinic user, even a doctor
    assert (await client.get(f"{c.base}/members", headers=H(c.doctor))).status_code == 403
    assert (await _role(client, c, "Mine", ["patients.read"])).status_code == 201  # the admin can
    assert (await client.post(f"{c.base}/roles", json={"name_en": "Mine", "permissions": ["patients.read"]}, headers=H(c.doctor))).status_code == 403


@pytest.mark.asyncio
async def test_the_receptionist_and_the_platform_have_no_clinic_team_view(client, db_session, clinic, test_tenant):
    c = clinic
    rec = await _person(db_session, test_tenant, "receptionist")
    assert (await client.get("/api/v1/team/members", headers=H(_token(rec)))).status_code == 403
    assert (await client.get("/api/v1/team/members", headers=H(c.admin))).status_code == 403  # a platform user has no clinic of their own
    assert (await client.get("/api/v1/team/members")).status_code == 401


@pytest.mark.asyncio
async def test_the_read_only_operator_can_look_at_a_clinic_team_but_not_change_it(client, db_session, clinic):
    c = clinic
    operator = await _platform(db_session, "operator", "Op")
    op = _token(operator)
    assert (await client.get(f"{c.base}/members", headers=H(op))).status_code == 200
    assert (await client.post(f"{c.base}/roles", json={"name_en": "X", "permissions": ["patients.read"]}, headers=H(op))).status_code == 403
    assert (await client.post(f"{c.base}/members", json={"email": "x@teamclinic.com", "full_name": "X Y", "role_ids": [RECEPTIONIST]}, headers=H(op))).status_code == 403
    assert (await client.get(f"{base(str(uuid.uuid4()))}/members", headers=H(c.admin))).status_code == 404  # no such clinic


@pytest.mark.asyncio
async def test_admin_sees_the_clinics_staff_and_the_roles_it_can_use(client, clinic):
    c = clinic
    members = (await client.get(f"{c.base}/members", headers=H(c.admin))).json()
    me = next(m for m in members if m["id"] == c.doctor_id)
    assert [r["key"] for r in me["roles"]] == ["doctor"] and me["can_manage"] and not me["is_you"]
    keys = {r["key"]: r for r in (await client.get(f"{c.base}/roles", headers=H(c.admin))).json()}
    assert {"doctor", "receptionist"} <= set(keys) and "admin" not in keys
    assert keys["doctor"]["is_system"] and not keys["doctor"]["can_edit"]
    assert sorted(keys["receptionist"]["permissions"]) == sorted(SYSTEM_ROLES["receptionist"].permissions)
    catalogue = {p["key"]: p for p in (await client.get(f"{c.base}/permissions", headers=H(c.admin))).json()}
    assert "team.manage" not in catalogue and "tenants.read" not in catalogue and all(p["can_grant"] for p in catalogue.values())


# ----- clinic roles ----------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_edit_and_delete_a_clinic_role(client, db_session, clinic):
    c = clinic
    created = await _role(client, c, "Accountant", ["payments.read", "payments.write", "invoices.read"], name_bn="হিসাবরক্ষক", based_on_role_id=RECEPTIONIST)
    assert created.status_code == 201, created.text
    role = created.json()
    assert role["permissions"] == ["invoices.read", "payments.read", "payments.write"] and role["can_edit"] and not role["is_system"]

    edited = await client.patch(f"{c.base}/roles/{role['id']}", json={"permissions": ["payments.read"]}, headers=H(c.admin))
    assert edited.status_code == 200 and edited.json()["permissions"] == ["payments.read"]
    assert (await client.patch(f"{c.base}/roles/{role['id']}", json={"name_en": "Billing"}, headers=H(c.admin))).json()["name_en"] == "Billing"
    assert (await client.delete(f"{c.base}/roles/{role['id']}", headers=H(c.admin))).status_code == 204
    assert role["id"] not in [r["id"] for r in (await client.get(f"{c.base}/roles", headers=H(c.admin))).json()]

    # the clinic reads the trail of what AltCare did, with who did it; a deleted role keeps its name there
    audit = (await client.get("/api/v1/team/audit", headers=H(c.doctor))).json()["items"]
    assert {"role_created", "role_updated", "role_deleted"} <= {a["action"] for a in audit}
    assert all(a["actor_name"] == "Platform Admin" for a in audit)
    assert next(a for a in audit if a["action"] == "role_deleted")["role_name"] == "Billing"


@pytest.mark.asyncio
async def test_the_platform_may_grant_any_clinic_permission_it_is_not_a_clinic_user(client, clinic):
    c = clinic
    r = await _role(client, c, "Assistant doctor", ["patients.read", "prescriptions.issue", "prescriptions.void", "patients.write"])
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_a_clinic_role_cannot_carry_a_platform_permission_or_a_removed_one(client, clinic):
    for bad in (["tenants.manage"], ["roles.manage_global"], ["clinic_roles.manage"], ["team.manage"], ["patients.read", "nonsense.key"]):
        r = await _role(client, clinic, "Bad", bad)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_permissions", bad


@pytest.mark.asyncio
async def test_sensitive_permissions_need_an_explicit_acknowledgement(client, clinic):
    refused = await _role(client, clinic, "Finance lead", ["billing.manage", "billing.view"])
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "sensitive_not_acknowledged"
    assert (await _role(client, clinic, "Finance lead", ["billing.manage", "billing.view"], acknowledge_sensitive=True)).status_code == 201


@pytest.mark.asyncio
async def test_system_roles_cannot_be_changed_or_deleted(client, clinic):
    for role_id in (DOCTOR, RECEPTIONIST):
        assert (await client.patch(f"{clinic.base}/roles/{role_id}", json={"name_en": "Hacked"}, headers=H(clinic.admin))).status_code == 403
        assert (await client.delete(f"{clinic.base}/roles/{role_id}", headers=H(clinic.admin))).status_code == 403


@pytest.mark.asyncio
async def test_a_role_in_use_cannot_be_deleted(client, db_session, clinic, test_tenant):
    c = clinic
    role = (await _role(client, c, "Helper", ["patients.read"])).json()
    member = await _person(db_session, test_tenant, "receptionist")
    member_id = member.id
    assert (await _set_roles(client, c, member_id, [role["id"]])).status_code == 200
    r = await client.delete(f"{c.base}/roles/{role['id']}", headers=H(c.admin))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "role_in_use"


@pytest.mark.asyncio
async def test_a_clinic_cannot_have_more_than_the_allowed_number_of_roles(client, clinic, monkeypatch):
    monkeypatch.setattr("app.modules.team.service.MAX_CLINIC_ROLES", 2)
    assert (await _role(client, clinic, "One", ["patients.read"])).status_code == 201
    assert (await _role(client, clinic, "Two", ["patients.read"])).status_code == 201
    assert (await _role(client, clinic, "Three", ["patients.read"])).status_code == 409
    assert (await _role(client, clinic, "one", ["patients.read"])).status_code == 409


# ----- members ---------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inviting_a_member_creates_the_account_and_emails_a_set_password_link(client, db_session, clinic, _fresh):
    c = clinic
    r = await client.post(
        f"{c.base}/members",
        json={"email": "Nurse@TeamClinic.com", "full_name": "Nurse Nila", "phone": "+8801700000000", "role_ids": [RECEPTIONIST]},
        headers=H(c.admin),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "nurse@teamclinic.com" and [x["key"] for x in body["roles"]] == ["receptionist"] and body["is_active"]
    user = (await db_session.execute(select(User).where(User.id == body["id"]))).scalar_one()
    assert user.tenant_id == c.tenant_id and user.role == "receptionist" and user.password_reset_token_hash
    assert _fresh and _fresh[0]["recipient"] == "nurse@teamclinic.com" and "reset-password?token=" in _fresh[0]["body_text"]
    assert await _roles_of(db_session, user.id) == ["receptionist"]

    again = await client.post(f"{c.base}/members", json={"email": "nurse@teamclinic.com", "full_name": "Nila Two", "role_ids": [RECEPTIONIST]}, headers=H(c.admin))
    assert again.status_code == 400
    # the new member can work as a receptionist, but has no say over the team
    assert (await client.get("/api/v1/patients", headers=H(_token(user)))).status_code == 200
    assert (await client.get("/api/v1/team/members", headers=H(_token(user)))).status_code == 403


@pytest.mark.asyncio
async def test_roles_are_the_union_and_changes_take_effect_at_once(client, db_session, clinic, test_tenant):
    c = clinic
    pay = (await _role(client, c, "Payments clerk", ["payments.write", "payments.read"])).json()
    only_read = (await _role(client, c, "Reader", ["patients.read"])).json()
    member = await _person(db_session, test_tenant, "receptionist")
    member_id, member_token = member.id, _token(member)
    assert (await _set_roles(client, c, member_id, [only_read["id"]])).status_code == 200
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code == 200
    assert (await client.get("/api/v1/appointments", headers=H(member_token))).status_code == 403
    r = await _set_roles(client, c, member_id, [only_read["id"], pay["id"]])
    assert [x["name_en"] for x in r.json()["roles"]] == ["Payments clerk", "Reader"]
    assert (await client.get("/api/v1/payments", headers=H(member_token))).status_code != 403
    assert (await client.patch(f"{c.base}/roles/{pay['id']}", json={"permissions": ["payments.read"]}, headers=H(c.admin))).status_code == 200
    assert (await client.post("/api/v1/payments", json={}, headers=H(member_token))).status_code == 403


@pytest.mark.asyncio
async def test_a_member_must_keep_at_least_one_role(client, db_session, clinic, test_tenant):
    member = await _person(db_session, test_tenant, "receptionist")
    assert (await _set_roles(client, clinic, member.id, [])).status_code == 422


@pytest.mark.asyncio
async def test_whoever_can_issue_prescriptions_counts_as_a_doctor_seat(client, db_session, clinic, test_tenant):
    c = clinic
    prescriber = (await _role(client, c, "Assistant doctor", ["patients.read", "prescriptions.read", "prescriptions.write", "prescriptions.issue"])).json()
    member = await _person(db_session, test_tenant, "receptionist")
    member_id = member.id
    r = await _set_roles(client, c, member_id, [prescriber["id"]])
    assert r.status_code == 200, r.text
    user = await db_session.get(User, member_id)
    await db_session.refresh(user)
    assert user.role == "doctor"
    assert await _roles_of(db_session, member_id) == [prescriber["key"]]  # the custom role only: no doctor system role came with it
    assert (await _set_roles(client, c, member_id, [RECEPTIONIST])).status_code == 200
    await db_session.refresh(user)
    assert user.role == "receptionist"


@pytest.mark.asyncio
async def test_a_prescriber_needs_a_practitioner_seat_on_the_plan(client, db_session, clinic, test_tenant):
    c = clinic
    test_tenant.plan = "free"  # one practitioner seat, already used by the doctor
    await db_session.commit()
    prescriber = (await _role(client, c, "Assistant doctor", ["patients.read", "prescriptions.issue", "prescriptions.read"])).json()
    r = await client.post(f"{c.base}/members", json={"email": "assistant@teamclinic.com", "full_name": "Assistant Doc", "role_ids": [prescriber["id"]]}, headers=H(c.admin))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "plan_limit_reached"
    assert (await client.post(f"{c.base}/members", json={"email": "desk@teamclinic.com", "full_name": "Front Desk", "role_ids": [RECEPTIONIST]}, headers=H(c.admin))).status_code == 201


@pytest.mark.asyncio
async def test_a_clinic_keeps_at_least_one_active_practitioner(client, db_session, clinic, test_tenant):
    c = clinic
    r = await _set_roles(client, c, c.doctor_id, [RECEPTIONIST])
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"
    r = await client.patch(f"{c.base}/members/{c.doctor_id}/status", json={"is_active": False}, headers=H(c.admin))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"
    assert [x["key"] for x in (await client.get(f"{c.base}/members", headers=H(c.admin))).json()[0]["roles"]] == ["doctor"]

    second = await _person(db_session, None, "doctor", "Second doctor", tenant_id=c.tenant_id)  # ids only: the 409 above expired the ORM objects
    second_id = second.id
    r = await _set_roles(client, c, c.doctor_id, [RECEPTIONIST])
    assert r.status_code == 200 and [x["key"] for x in r.json()["roles"]] == ["receptionist"]
    assert await _roles_of(db_session, second_id) == ["doctor"]
    # editing a role so nobody can prescribe any more is refused as well
    prescriber = (await _role(client, c, "Prescriber", ["prescriptions.issue", "patients.read"])).json()
    assert (await _set_roles(client, c, second_id, [prescriber["id"]])).status_code == 200
    r = await client.patch(f"{c.base}/roles/{prescriber['id']}", json={"permissions": ["patients.read"]}, headers=H(c.admin))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"


@pytest.mark.asyncio
async def test_deactivating_a_member_locks_them_out_and_reactivating_restores_access(client, db_session, clinic, test_tenant):
    c = clinic
    member = await _person(db_session, test_tenant, "receptionist")
    member_id, member_token = member.id, _token(member)
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code == 200
    r = await client.patch(f"{c.base}/members/{member_id}/status", json={"is_active": False}, headers=H(c.admin))
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code in (401, 403)
    assert (await client.patch(f"{c.base}/members/{member_id}/status", json={"is_active": True}, headers=H(c.admin))).json()["is_active"] is True
    actions = [a["action"] for a in (await client.get("/api/v1/team/audit", headers=H(c.doctor))).json()["items"]]
    assert "member_deactivated" in actions and "member_activated" in actions


# ----- isolation and audit ---------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_acting_on_one_clinic_never_touches_another(client, db_session, clinic, test_tenant_2):
    c = clinic
    other = SimpleNamespace(**{**vars(c), "base": base(test_tenant_2.id), "tenant_id": test_tenant_2.id})
    theirs = (await _role(client, other, "Their secret role", ["patients.read"])).json()
    their_member = await _person(db_session, test_tenant_2, "receptionist")
    their_member_id = their_member.id

    assert theirs["id"] not in [r["id"] for r in (await client.get(f"{c.base}/roles", headers=H(c.admin))).json()]
    assert their_member_id not in [m["id"] for m in (await client.get(f"{c.base}/members", headers=H(c.admin))).json()]
    mine = await _person(db_session, None, "receptionist", tenant_id=c.tenant_id)
    mine_id = mine.id
    assert (await _set_roles(client, c, mine_id, [theirs["id"]])).status_code == 404
    assert (await client.patch(f"{c.base}/roles/{theirs['id']}", json={"name_en": "Mine now"}, headers=H(c.admin))).status_code == 404
    assert (await client.delete(f"{c.base}/roles/{theirs['id']}", headers=H(c.admin))).status_code == 404
    assert (await _set_roles(client, c, their_member_id, [RECEPTIONIST])).status_code == 404
    assert (await client.patch(f"{c.base}/members/{their_member_id}/status", json={"is_active": False}, headers=H(c.admin))).status_code == 404
    assert not any(a["role_name"] == "Their secret role" for a in (await client.get("/api/v1/team/audit", headers=H(c.doctor))).json()["items"])


@pytest.mark.asyncio
async def test_every_change_is_audited_in_the_clinics_trail_and_the_global_one(client, db_session, clinic, test_tenant):
    c = clinic
    member = await _person(db_session, test_tenant, "receptionist", "Rina")
    member_id = member.id
    role = (await _role(client, c, "Reader", ["patients.read"])).json()
    await _set_roles(client, c, member_id, [role["id"]])

    page = (await client.get("/api/v1/team/audit", headers=H(c.doctor))).json()
    assert page["total"] == 2
    change = next(a for a in page["items"] if a["action"] == "roles_assigned")
    assert change["actor_name"] == "Platform Admin" and change["member_name"] == "Rina"
    assert change["before"] == {"roles": ["Receptionist"]} and change["after"] == {"roles": ["Reader"]}
    rows = (await db_session.execute(select(RoleAuditLog).where(RoleAuditLog.tenant_id == c.tenant_id))).scalars().all()
    assert len(rows) == 2 and all(r.actor_user_id == c.admin_id for r in rows)

    global_trail = (await client.get("/api/v1/admin/staff/audit?level=clinic", headers=H(c.admin))).json()
    assert global_trail["total"] == 2 and {a["clinic_name"] for a in global_trail["items"]} == {c.clinic_name}
