"""Moving from role checks to permission checks must change nobody's access (ADR 010, Phase 2).

tests/golden/access_matrix.json froze, route by route and role by role, who was allowed while the guards were still
role checks. This test works the same decisions out from the current guards and requires an exact match. If a change
of access is intended, regenerate the snapshot with scripts/dump_access_matrix.py and review the diff.
"""

import json
from pathlib import Path

from app.main import app
from tests.access_matrix import ROLES, comparable, matrix

GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "access_matrix.json"


def test_every_route_gives_every_role_the_same_answer_as_before():
    problems = comparable(json.loads(GOLDEN.read_text()), matrix(app))
    assert not problems, "Access changed:\n" + "\n".join(problems[:40]) + (f"\n... and {len(problems) - 40} more" if len(problems) > 40 else "")


def test_the_snapshot_itself_is_sane():
    golden = json.loads(GOLDEN.read_text())
    assert len(golden) > 200
    for entry in golden.values():
        assert set(entry) == {"guarded", *ROLES}
    # a few anchors that must always hold
    assert golden["POST /api/v1/prescriptions"]["doctor"] is True and golden["POST /api/v1/prescriptions"]["receptionist"] is False
    assert golden["GET /api/v1/patients"]["receptionist"] is True and golden["POST /api/v1/patients"]["receptionist"] is False
    assert golden["POST /api/v1/admin/tenants"]["admin"] is True and golden["POST /api/v1/admin/tenants"]["operator"] is False
    assert golden["GET /api/v1/admin/tenants"]["operator"] is True and golden["GET /api/v1/admin/tenants"]["doctor"] is False


def test_the_clinic_team_routes_are_read_only_and_for_doctors_only_by_default():
    """Added after the snapshot was frozen, so asserted here: a clinic can only look, and only the doctor role holds team.read."""
    now = matrix(app)
    team = {k: v for k, v in now.items() if k.split(" ", 1)[1].startswith("/api/v1/team")}
    assert len(team) == 4 and all(k.startswith("GET ") for k in team)
    for key, decision in team.items():
        assert decision["doctor"] is True, key
        assert not any(decision[r] for r in ROLES if r != "doctor"), key


def test_the_routes_that_change_a_clinics_team_are_for_platform_admins_only():
    """Clinics ask AltCare for any change to staff or roles; the read-only operator may look but not change."""
    now = matrix(app)
    team = {k: v for k, v in now.items() if "/api/v1/admin/tenants/{tenant_id}/team" in k}
    assert len(team) == 10
    for key, decision in team.items():
        assert decision["admin"] is True, key
        assert decision["operator"] is key.startswith("GET "), key
        assert not decision["doctor"] and not decision["receptionist"], key


def test_the_platform_staff_routes_follow_users_read_and_roles_manage_global():
    """Also added after the freeze. Admin does everything; the read-only operator may look (and read the audit trail) but not change anything."""
    now = matrix(app)
    staff = {k: v for k, v in now.items() if k.split(" ", 1)[1].startswith("/api/v1/admin/staff")}
    assert len(staff) == 10
    for key, decision in staff.items():
        assert decision["admin"] is True, key
        assert decision["operator"] is key.startswith("GET "), key
        assert not decision["doctor"] and not decision["receptionist"], key


# ----- default deny: a route added without a permission guard must fail here, not slip into production ------------------

from fastapi.routing import APIRoute  # noqa: E402

from tests.access_matrix import guards_of  # noqa: E402

# Own authentication or public by design: sign-in and registration, the public site, the patient portal (patients sign in
# with their phone, not a staff account), payment-gateway callbacks, health checks.
FULLY_OPEN = ("/", "/health", "/metrics", "/api/v1/auth", "/api/v1/public", "/api/v1/patient", "/api/v1/billing/gateways")
# Anyone signed in may read; every other method must be guarded.
READ_OPEN = (
    "/api/v1/institutions", "/api/v1/pharmacies", "/api/v1/geographic", "/api/v1/plans", "/api/v1/health-options", "/api/v1/entitlements",
)


def _has_permission_guard(route) -> bool:
    return any(hasattr(g, "permission_all") or hasattr(g, "permission_any") or hasattr(g, "module_read") for g in guards_of(route))


def _under(path: str, prefixes) -> bool:
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes if p != "/") or ("/" in prefixes and path == "/")


def test_no_route_is_left_without_a_permission_guard():
    unguarded = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or _has_permission_guard(route):
            continue
        if _under(route.path, FULLY_OPEN):
            continue
        methods = route.methods - {"HEAD", "OPTIONS"}
        if _under(route.path, READ_OPEN) and methods <= {"GET"}:
            continue
        unguarded.append(f"{sorted(methods)} {route.path}")
    assert not unguarded, "Routes with no permission guard (add one, or list them as open on purpose):\n" + "\n".join(unguarded)
