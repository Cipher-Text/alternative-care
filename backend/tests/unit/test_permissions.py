"""The permission catalogue and the system roles: shapes, scopes, and the pinned sets (ADR 010)."""

import pytest

from app.core.permissions import (
    BY_KEY,
    PERMISSIONS,
    PLATFORM_PERMISSIONS,
    SYSTEM_ROLES,
    TENANT_PERMISSIONS,
    PermissionRuleError,
    check_can_grant,
    system_role_id,
    validate_role_permissions,
)


def test_every_permission_has_a_clean_key_a_scope_and_both_descriptions():
    assert len(BY_KEY) == len(PERMISSIONS)
    for p in PERMISSIONS:
        assert p.key == p.key.lower() and "." in p.key and " " not in p.key
        assert p.scope in ("platform", "tenant") and p.module
        assert p.en.strip() and p.bn.strip()
    assert {p.scope for p in TENANT_PERMISSIONS} == {"tenant"} and {p.scope for p in PLATFORM_PERMISSIONS} == {"platform"}


def test_system_roles_only_hold_real_permissions_of_their_own_scope():
    assert set(SYSTEM_ROLES) == {"admin", "operator", "doctor", "receptionist"}
    for role in SYSTEM_ROLES.values():
        validate_role_permissions(role.scope, role.permissions)  # raises on an unknown or wrong-scope key
    assert {r.scope for r in (SYSTEM_ROLES["admin"], SYSTEM_ROLES["operator"])} == {"platform"}
    assert {r.scope for r in (SYSTEM_ROLES["doctor"], SYSTEM_ROLES["receptionist"])} == {"tenant"}


def test_the_system_role_sets_are_pinned():
    """These sets reproduce the hard-coded roles. Changing one changes what every holder of that role may do."""
    assert SYSTEM_ROLES["admin"].permissions == {p.key for p in PLATFORM_PERMISSIONS}
    assert SYSTEM_ROLES["doctor"].permissions == {p.key for p in TENANT_PERMISSIONS}
    assert SYSTEM_ROLES["operator"].permissions == {"tenants.read", "users.read", "plans.read", "audit.read"}
    assert SYSTEM_ROLES["receptionist"].permissions == {
        "dashboard.view", "patients.read", "health_profile.read", "case_taking.read", "appointments.read", "appointments.write",
        "appointment_requests.manage", "visits.read", "prescriptions.read", "payments.read", "payments.write", "invoices.read",
        "invoices.write", "medicines.read", "symptoms.read", "identity.link", "clinic_profile.read", "billing.view",
    }


def test_the_receptionist_is_read_only_on_clinical_records_and_has_no_clinical_or_staff_powers():
    held = SYSTEM_ROLES["receptionist"].permissions
    clinical_writes = {
        "patients.write", "patients.delete", "diagnoses.write", "health_profile.write", "case_taking.write", "visits.write",
        "prescriptions.write", "prescriptions.issue", "prescriptions.void", "medicines.write", "symptoms.write", "clinic_profile.write",
    }
    assert not (held & clinical_writes)
    assert not (held & {"messaging.send", "messaging.read", "ai.use", "doctor_profile.manage", "billing.manage", "team.read"})


def test_sensitive_permissions_are_flagged_and_never_in_the_receptionist_role():
    sensitive = {p.key for p in PERMISSIONS if p.sensitive}
    assert {"patients.delete", "billing.manage", "users.manage", "billing.admin", "roles.manage_global", "clinic_roles.manage"} <= sensitive
    assert not (SYSTEM_ROLES["receptionist"].permissions & sensitive)
    assert not (SYSTEM_ROLES["operator"].permissions & sensitive)  # read-only staff hold nothing sensitive


def test_system_role_ids_are_fixed_and_distinct():
    ids = {k: system_role_id(k) for k in SYSTEM_ROLES}
    assert len(set(ids.values())) == 4
    assert ids == {k: system_role_id(k) for k in SYSTEM_ROLES}  # the same every time, in every database


def test_a_clinic_role_can_never_carry_a_platform_permission():
    validate_role_permissions("tenant", {"patients.read", "appointments.write"})
    with pytest.raises(PermissionRuleError, match="tenants.manage"):
        validate_role_permissions("tenant", {"patients.read", "tenants.manage"})
    with pytest.raises(PermissionRuleError, match="patients.read"):
        validate_role_permissions("platform", {"tenants.read", "patients.read"})
    with pytest.raises(PermissionRuleError, match="made.up"):
        validate_role_permissions("tenant", {"made.up"})


def test_nobody_can_grant_what_they_do_not_hold():
    receptionist = SYSTEM_ROLES["receptionist"].permissions
    check_can_grant(receptionist, {"patients.read", "payments.write"})
    with pytest.raises(PermissionRuleError, match="prescriptions.issue"):
        check_can_grant(receptionist, {"patients.read", "prescriptions.issue"})
    check_can_grant(SYSTEM_ROLES["doctor"].permissions, SYSTEM_ROLES["receptionist"].permissions)  # an owner can hand out less
