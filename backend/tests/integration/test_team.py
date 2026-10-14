"""The clinic Team page's backend: staff, clinic roles, and the safety rules of ADR 010 (Phase 3)."""

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core import permission_cache
from app.core.config import settings
from app.core.permissions import SYSTEM_ROLES, system_role_id
from app.core.rbac import sync_catalogue_async
from app.core.security import create_access_token, get_password_hash
from app.shared.models import Tenant, User
from app.shared.models.rbac import Role, RoleAuditLog, UserRole

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
DOCTOR, RECEPTIONIST = system_role_id("doctor"), system_role_id("receptionist")


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


async def _person(db, tenant, role="doctor", name="Person"):
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id, email=f"{uuid.uuid4().hex[:8]}@team.test", password_hash=get_password_hash("Test@1234"),
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


async def _roles_of(db, user):
    rows = await db.execute(select(Role.key).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id))
    return sorted(rows.scalars().all())


async def _role(client, token, name, permissions, **extra):
    return await client.post("/api/v1/team/roles", json={"name_en": name, "permissions": permissions, **extra}, headers=H(token))


@pytest.fixture
async def clinic(db_session, seeded, test_tenant):
    test_tenant.plan = "pro"  # several practitioner seats
    await db_session.commit()
    owner = await _person(db_session, test_tenant, "doctor", "Owner")
    return test_tenant, owner, _token(owner)


# ----- who may look and who may change ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_receptionist_and_platform_staff_cannot_use_the_team_api(client, db_session, clinic, platform_admin, admin_access_token):
    tenant, _, _ = clinic
    rec = await _person(db_session, tenant, "receptionist")
    for token in (_token(rec), admin_access_token):
        assert (await client.get("/api/v1/team/members", headers=H(token))).status_code == 403
        assert (await client.post("/api/v1/team/roles", json={"name_en": "X", "permissions": ["patients.read"]}, headers=H(token))).status_code == 403
    assert (await client.get("/api/v1/team/members")).status_code == 401


@pytest.mark.asyncio
async def test_owner_sees_staff_and_the_roles_they_can_use(client, db_session, clinic):
    tenant, owner, token = clinic
    members = (await client.get("/api/v1/team/members", headers=H(token))).json()
    me = next(m for m in members if m["id"] == owner.id)
    assert me["is_you"] and [r["key"] for r in me["roles"]] == ["doctor"] and me["can_manage"]
    roles = (await client.get("/api/v1/team/roles", headers=H(token))).json()
    keys = {r["key"]: r for r in roles}
    assert {"doctor", "receptionist"} <= set(keys) and "admin" not in keys and "operator" not in keys
    assert keys["doctor"]["is_system"] and not keys["doctor"]["can_edit"] and keys["doctor"]["can_assign"]
    assert sorted(keys["receptionist"]["permissions"]) == sorted(SYSTEM_ROLES["receptionist"].permissions)
    catalogue = (await client.get("/api/v1/team/permissions", headers=H(token))).json()
    assert catalogue and all(p["key"] not in ("tenants.read", "roles.manage_global") for p in catalogue)


# ----- clinic roles ----------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_edit_and_delete_a_clinic_role(client, db_session, clinic):
    tenant, owner, token = clinic
    created = await _role(client, token, "Accountant", ["payments.read", "payments.write", "invoices.read"], name_bn="হিসাবরক্ষক", based_on_role_id=RECEPTIONIST)
    assert created.status_code == 201, created.text
    role = created.json()
    assert role["permissions"] == ["invoices.read", "payments.read", "payments.write"] and role["can_edit"] and not role["is_system"]

    edited = await client.patch(f"/api/v1/team/roles/{role['id']}", json={"permissions": ["payments.read"]}, headers=H(token))
    assert edited.status_code == 200 and edited.json()["permissions"] == ["payments.read"]
    assert (await client.patch(f"/api/v1/team/roles/{role['id']}", json={"name_en": "Billing"}, headers=H(token))).json()["name_en"] == "Billing"

    assert (await client.delete(f"/api/v1/team/roles/{role['id']}", headers=H(token))).status_code == 204
    assert role["id"] not in [r["id"] for r in (await client.get("/api/v1/team/roles", headers=H(token))).json()]
    actions = [a["action"] for a in (await client.get("/api/v1/team/audit", headers=H(token))).json()["items"]]
    assert {"role_created", "role_updated", "role_deleted"} <= set(actions)
    # the deleted role's name survives in the audit trail
    audit = (await client.get("/api/v1/team/audit", headers=H(token))).json()["items"]
    assert next(a for a in audit if a["action"] == "role_deleted")["role_name"] == "Billing"


@pytest.mark.asyncio
async def test_a_role_cannot_carry_a_permission_of_the_wrong_level_or_one_that_does_not_exist(client, clinic):
    _, _, token = clinic
    for bad in (["tenants.manage"], ["roles.manage_global"], ["patients.read", "nonsense.key"]):
        r = await _role(client, token, "Bad", bad)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_permissions", bad


@pytest.mark.asyncio
async def test_sensitive_permissions_need_an_explicit_acknowledgement(client, clinic):
    _, _, token = clinic
    refused = await _role(client, token, "Finance lead", ["billing.manage", "billing.view"])
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "sensitive_not_acknowledged"
    assert (await _role(client, token, "Finance lead", ["billing.manage", "billing.view"], acknowledge_sensitive=True)).status_code == 201


@pytest.mark.asyncio
async def test_system_roles_cannot_be_changed_or_deleted_by_a_clinic(client, clinic):
    _, _, token = clinic
    for role_id in (DOCTOR, RECEPTIONIST):
        assert (await client.patch(f"/api/v1/team/roles/{role_id}", json={"name_en": "Hacked"}, headers=H(token))).status_code == 403
        assert (await client.delete(f"/api/v1/team/roles/{role_id}", headers=H(token))).status_code == 403


@pytest.mark.asyncio
async def test_a_role_in_use_cannot_be_deleted(client, db_session, clinic):
    tenant, _, token = clinic
    role = (await _role(client, token, "Helper", ["patients.read"])).json()
    member = await _person(db_session, tenant, "receptionist")
    assert (await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [role["id"]]}, headers=H(token))).status_code == 200
    r = await client.delete(f"/api/v1/team/roles/{role['id']}", headers=H(token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "role_in_use"


@pytest.mark.asyncio
async def test_a_clinic_cannot_have_more_than_the_allowed_number_of_roles(client, clinic, monkeypatch):
    _, _, token = clinic
    monkeypatch.setattr("app.modules.team.service.MAX_CLINIC_ROLES", 2)
    assert (await _role(client, token, "One", ["patients.read"])).status_code == 201
    assert (await _role(client, token, "Two", ["patients.read"])).status_code == 201
    assert (await _role(client, token, "Three", ["patients.read"])).status_code == 409
    assert (await _role(client, token, "one", ["patients.read"])).status_code == 409  # a duplicate name is refused first or second, never created


# ----- rule 1: no escalation -------------------------------------------------------------------------------------------


@pytest.fixture
async def manager(client, db_session, clinic):
    """A staff member who can manage the team but holds only a few other permissions."""
    tenant, owner, owner_token = clinic
    role = (await _role(client, owner_token, "Team lead", ["team.read", "team.manage", "patients.read", "appointments.read"], acknowledge_sensitive=True)).json()
    person = await _person(db_session, tenant, "receptionist", "Lead")
    assert (await client.put(f"/api/v1/team/members/{person.id}/roles", json={"role_ids": [role["id"]]}, headers=H(owner_token))).status_code == 200
    return person, _token(person), role


@pytest.mark.asyncio
async def test_a_manager_cannot_grant_permissions_they_do_not_hold(client, manager, clinic):
    _, token, _ = manager
    r = await _role(client, token, "Sneaky", ["patients.read", "prescriptions.issue"])
    assert r.status_code == 403 and r.json()["detail"]["code"] == "cannot_grant"
    assert (await _role(client, token, "Fine", ["patients.read"])).status_code == 201
    catalogue = {p["key"]: p["can_grant"] for p in (await client.get("/api/v1/team/permissions", headers=H(token))).json()}
    assert catalogue["patients.read"] and not catalogue["prescriptions.issue"]


@pytest.mark.asyncio
async def test_a_manager_cannot_widen_a_role_beyond_their_own_permissions(client, manager, clinic):
    _, owner_token = clinic[1], clinic[2]
    _, token, role = manager
    r = await client.patch(f"/api/v1/team/roles/{role['id']}", json={"permissions": ["team.manage", "team.read", "prescriptions.issue"], "acknowledge_sensitive": True}, headers=H(token))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "cannot_grant"


@pytest.mark.asyncio
async def test_a_manager_cannot_assign_the_doctor_role_or_touch_someone_who_holds_it(client, db_session, manager, clinic):
    tenant, owner, owner_token = clinic
    _, token, _ = manager
    reader = (await _role(client, owner_token, "Reader", ["patients.read"])).json()
    helper = await _person(db_session, tenant, "receptionist")
    assert (await client.put(f"/api/v1/team/members/{helper.id}/roles", json={"role_ids": [reader["id"]]}, headers=H(owner_token))).status_code == 200
    r = await client.put(f"/api/v1/team/members/{helper.id}/roles", json={"role_ids": [DOCTOR]}, headers=H(token))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "cannot_assign_role"
    assert await _roles_of(db_session, helper) == [reader["key"]]
    # a plain receptionist holds more than the manager does (payments), so the manager cannot manage them either
    rec = await _person(db_session, tenant, "receptionist")
    assert (await client.put(f"/api/v1/team/members/{rec.id}/roles", json={"role_ids": [reader["id"]]}, headers=H(token))).status_code == 403
    # nor can they strip or switch off the owner, whose roles carry more than they hold
    assert (await client.put(f"/api/v1/team/members/{owner.id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))).status_code == 403
    assert (await client.patch(f"/api/v1/team/members/{owner.id}/status", json={"is_active": False}, headers=H(token))).status_code == 403
    members = {m["id"]: m for m in (await client.get("/api/v1/team/members", headers=H(token))).json()}
    assert members[owner.id]["can_manage"] is False and members[helper.id]["can_manage"] is True


@pytest.mark.asyncio
async def test_a_manager_cannot_invite_someone_into_a_role_they_do_not_hold(client, manager):
    _, token, _ = manager
    r = await client.post("/api/v1/team/members", json={"email": "new@teamclinic.com", "full_name": "New Person", "role_ids": [DOCTOR]}, headers=H(token))
    assert r.status_code == 403


# ----- rule 3: a clinic always has someone who can manage it ------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_last_person_who_can_manage_the_team_cannot_be_demoted_or_deactivated(client, db_session, clinic):
    tenant, owner, token = clinic
    # a refused change rolls the (shared) test session back, which expires ORM objects: keep plain ids and tokens
    owner_id, tenant_ref = owner.id, SimpleNamespace(id=tenant.id)
    r = await client.put(f"/api/v1/team/members/{owner_id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"
    assert [x["key"] for x in (await client.get("/api/v1/team/members", headers=H(token))).json()[0]["roles"]] == ["doctor"]
    assert (await client.patch(f"/api/v1/team/members/{owner_id}/status", json={"is_active": False}, headers=H(token))).status_code == 400  # not yourself

    # a role edit that would take team.manage from the only person who has it is refused as well
    lead = (await _role(client, token, "Lead", ["team.read", "team.manage", "patients.read"], acknowledge_sensitive=True)).json()
    other = await _person(db_session, tenant_ref, "receptionist")
    other_token, other_id = _token(other), other.id
    assert (await client.put(f"/api/v1/team/members/{other_id}/roles", json={"role_ids": [lead["id"]]}, headers=H(token))).status_code == 200
    assert (await client.put(f"/api/v1/team/members/{owner_id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))).status_code == 200  # a second owner exists now
    r = await client.patch(f"/api/v1/team/roles/{lead['id']}", json={"permissions": ["team.read", "patients.read"]}, headers=H(other_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_owner"
    kept = next(x for x in (await client.get("/api/v1/team/roles", headers=H(other_token))).json() if x["id"] == lead["id"])
    assert "team.manage" in kept["permissions"]
    # nor can they drop their own role for one they could not otherwise hold
    assert (await client.put(f"/api/v1/team/members/{other_id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(other_token))).status_code == 403


@pytest.mark.asyncio
async def test_with_a_second_owner_the_first_can_step_down(client, db_session, clinic):
    tenant, owner, token = clinic
    second = await _person(db_session, tenant, "doctor", "Second")
    r = await client.put(f"/api/v1/team/members/{owner.id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))
    assert r.status_code == 200 and [x["key"] for x in r.json()["roles"]] == ["receptionist"]
    assert await _roles_of(db_session, second) == ["doctor"]


# ----- members ---------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inviting_a_member_creates_the_account_and_emails_a_set_password_link(client, db_session, clinic, _fresh):
    tenant, owner, token = clinic
    r = await client.post(
        "/api/v1/team/members",
        json={"email": "Nurse@TeamClinic.com", "full_name": "Nurse Nila", "phone": "+8801700000000", "role_ids": [RECEPTIONIST]},
        headers=H(token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "nurse@teamclinic.com" and [x["key"] for x in body["roles"]] == ["receptionist"] and body["is_active"]
    user = (await db_session.execute(select(User).where(User.id == body["id"]))).scalar_one()
    assert user.tenant_id == tenant.id and user.role == "receptionist" and user.password_reset_token_hash
    assert _fresh and _fresh[0]["recipient"] == "nurse@teamclinic.com" and "reset-password?token=" in _fresh[0]["body_text"]
    assert await _roles_of(db_session, user) == ["receptionist"]

    # the same address cannot be added twice, here or anywhere
    again = await client.post("/api/v1/team/members", json={"email": "nurse@teamclinic.com", "full_name": "Nila Two", "role_ids": [RECEPTIONIST]}, headers=H(token))
    assert again.status_code == 400
    # the new member can read the schedule but not the team
    assert (await client.get("/api/v1/team/members", headers=H(_token(user)))).status_code == 403


@pytest.mark.asyncio
async def test_roles_are_the_union_and_changes_take_effect_at_once(client, db_session, clinic):
    tenant, owner, token = clinic
    pay = (await _role(client, token, "Payments clerk", ["payments.write", "payments.read"])).json()
    member = await _person(db_session, tenant, "receptionist")
    member_token = _token(member)
    # the receptionist already writes payments; remove the receptionist role and keep only a role without them
    only_read = (await _role(client, token, "Reader", ["patients.read"])).json()
    assert (await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [only_read["id"]]}, headers=H(token))).status_code == 200
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code == 200
    assert (await client.get("/api/v1/appointments", headers=H(member_token))).status_code == 403
    r = await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [only_read["id"], pay["id"]]}, headers=H(token))
    assert [x["name_en"] for x in r.json()["roles"]] == ["Payments clerk", "Reader"]
    assert (await client.get("/api/v1/payments", headers=H(member_token))).status_code != 403
    # taking a permission off the role is felt by everyone who holds it, immediately
    assert (await client.patch(f"/api/v1/team/roles/{pay['id']}", json={"permissions": ["payments.read"]}, headers=H(token))).status_code == 200
    assert (await client.post("/api/v1/payments", json={}, headers=H(member_token))).status_code == 403


@pytest.mark.asyncio
async def test_a_member_must_keep_at_least_one_role(client, db_session, clinic):
    tenant, _, token = clinic
    member = await _person(db_session, tenant, "receptionist")
    assert (await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": []}, headers=H(token))).status_code == 422


@pytest.mark.asyncio
async def test_whoever_can_issue_prescriptions_counts_as_a_doctor_seat(client, db_session, clinic):
    tenant, _, token = clinic
    prescriber = (await _role(client, token, "Assistant doctor", ["patients.read", "prescriptions.read", "prescriptions.write", "prescriptions.issue"])).json()
    member = await _person(db_session, tenant, "receptionist")
    r = await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [prescriber["id"]]}, headers=H(token))
    assert r.status_code == 200, r.text
    await db_session.refresh(member)
    assert member.role == "doctor"
    assert await _roles_of(db_session, member) == [prescriber["key"]]  # the custom role only: no doctor system role came with it
    # and back
    assert (await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))).status_code == 200
    await db_session.refresh(member)
    assert member.role == "receptionist"


@pytest.mark.asyncio
async def test_deactivating_a_member_locks_them_out_and_reactivating_restores_access(client, db_session, clinic):
    tenant, _, token = clinic
    member = await _person(db_session, tenant, "receptionist")
    member_token = _token(member)
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code == 200
    r = await client.patch(f"/api/v1/team/members/{member.id}/status", json={"is_active": False}, headers=H(token))
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await client.get("/api/v1/patients", headers=H(member_token))).status_code in (401, 403)
    assert (await client.patch(f"/api/v1/team/members/{member.id}/status", json={"is_active": True}, headers=H(token))).json()["is_active"] is True
    actions = [a["action"] for a in (await client.get("/api/v1/team/audit", headers=H(token))).json()["items"]]
    assert "member_deactivated" in actions and "member_activated" in actions


# ----- isolation and audit ---------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_one_clinic_cannot_see_or_use_another_clinics_roles_or_staff(client, db_session, clinic, test_tenant_2):
    tenant, _, token = clinic
    other_owner = await _person(db_session, test_tenant_2, "doctor", "Other owner")
    other_token = _token(other_owner)
    theirs = (await _role(client, other_token, "Their secret role", ["patients.read"])).json()

    assert theirs["id"] not in [r["id"] for r in (await client.get("/api/v1/team/roles", headers=H(token))).json()]
    assert other_owner.id not in [m["id"] for m in (await client.get("/api/v1/team/members", headers=H(token))).json()]
    mine = await _person(db_session, tenant, "receptionist")
    assert (await client.put(f"/api/v1/team/members/{mine.id}/roles", json={"role_ids": [theirs["id"]]}, headers=H(token))).status_code == 404
    assert (await client.patch(f"/api/v1/team/roles/{theirs['id']}", json={"name_en": "Mine now"}, headers=H(token))).status_code == 404
    assert (await client.delete(f"/api/v1/team/roles/{theirs['id']}", headers=H(token))).status_code == 404
    assert (await client.put(f"/api/v1/team/members/{other_owner.id}/roles", json={"role_ids": [RECEPTIONIST]}, headers=H(token))).status_code == 404
    assert (await client.patch(f"/api/v1/team/members/{other_owner.id}/status", json={"is_active": False}, headers=H(token))).status_code == 404
    assert not any(a["role_name"] == "Their secret role" for a in (await client.get("/api/v1/team/audit", headers=H(token))).json()["items"])


@pytest.mark.asyncio
async def test_every_change_is_audited_with_who_and_before_after(client, db_session, clinic):
    tenant, owner, token = clinic
    member = await _person(db_session, tenant, "receptionist", "Rina")
    role = (await _role(client, token, "Reader", ["patients.read"])).json()
    await client.put(f"/api/v1/team/members/{member.id}/roles", json={"role_ids": [role["id"]]}, headers=H(token))
    page = (await client.get("/api/v1/team/audit", headers=H(token))).json()
    assert page["total"] == 2
    change = next(a for a in page["items"] if a["action"] == "roles_assigned")
    assert change["actor_name"] == "Owner" and change["member_name"] == "Rina"
    assert change["before"] == {"roles": ["Receptionist"]} and change["after"] == {"roles": ["Reader"]}
    rows = (await db_session.execute(select(RoleAuditLog).where(RoleAuditLog.tenant_id == tenant.id))).scalars().all()
    assert len(rows) == 2 and all(r.actor_user_id == owner.id for r in rows)


@pytest.mark.asyncio
async def test_a_prescriber_needs_a_practitioner_seat_on_the_plan(client, db_session, clinic):
    tenant, _, token = clinic
    tenant.plan = "free"  # one practitioner seat, already used by the owner
    await db_session.commit()
    prescriber = (await _role(client, token, "Assistant doctor", ["patients.read", "prescriptions.issue", "prescriptions.read"])).json()
    r = await client.post("/api/v1/team/members", json={"email": "assistant@teamclinic.com", "full_name": "Assistant Doc", "role_ids": [prescriber["id"]]}, headers=H(token))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "plan_limit_reached"
    # somebody who cannot prescribe is not a seat
    assert (await client.post("/api/v1/team/members", json={"email": "desk@teamclinic.com", "full_name": "Front Desk", "role_ids": [RECEPTIONIST]}, headers=H(token))).status_code == 201
