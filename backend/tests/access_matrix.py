"""Who may call which route, worked out from the route guards without calling anything.

Used to prove the move from role checks to permission checks (ADR 010, Phase 2) changed nobody's access: the decisions
for every route and every role were frozen in tests/golden/access_matrix.json while the guards were still role checks,
and `tests/unit/test_access_matrix.py` requires the migrated guards to produce exactly the same decisions.

A guard is recognised by a tag on its function:
  permission_all / _any      a permission check                 (require_permission / require_any_permission)
  module_read / module_write method-aware router guard          (module_guard / access_guard)
(The role checks that the snapshot was taken from, `require_role` and the receptionist deny-guards, no longer exist.)
Only guards are read. Checks inside a handler or a service (a platform user reaching a clinic route, a plan limit,
"is this your own record") are not role decisions and are out of scope here.
"""

from fastapi.routing import APIRoute

from app.core.permissions import SYSTEM_ROLES

ROLES = ("admin", "operator", "doctor", "receptionist")
SAFE = frozenset({"GET", "HEAD", "OPTIONS"})
PLATFORM_ROLES = ("admin", "operator")


def _calls(dependant):
    for dep in dependant.dependencies:
        yield dep.call
        yield from _calls(dep)


def guards_of(route: APIRoute) -> list:
    return [c for c in _calls(route.dependant) if _is_guard(c)]


def _is_guard(call) -> bool:
    return (
        hasattr(call, "permission_all")
        or hasattr(call, "permission_any")
        or hasattr(call, "module_read")
    )


def _allows(guard, role: str, method: str) -> bool:
    held = SYSTEM_ROLES[role].permissions
    if hasattr(guard, "permission_all"):
        return all(k in held for k in guard.permission_all)
    if hasattr(guard, "permission_any"):
        return any(k in held for k in guard.permission_any)
    wanted = guard.module_read if method in SAFE else guard.module_write
    return any(k in held for k in wanted)


def matrix(app) -> dict[str, dict]:
    """{"METHOD /path": {"guarded": bool, "admin": bool, "operator": bool, "doctor": bool, "receptionist": bool}}"""
    out: dict[str, dict] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        guards = guards_of(route)
        # "guarded" = the route names who may use it (a role or permission allow-list). The receptionist deny-guards
        # and the method-aware module guards only ever said something about clinic staff.
        names_its_users = any(hasattr(g, "permission_all") or hasattr(g, "permission_any") for g in guards)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            out[f"{method} {route.path}"] = {"guarded": names_its_users, **{r: all(_allows(g, r, method) for g in guards) for r in ROLES}}
    return out


def comparable(golden: dict, now: dict) -> list[str]:
    """What differs between the frozen decisions and the current ones, as readable lines.

    A route that did not name its users before (no allow-list) is compared for the two clinic roles only: platform
    staff were turned away later, by the clinic service, and may now be turned away earlier. Same refusal."""
    problems = []
    for key in sorted(set(golden) | set(now)):
        if key not in now:
            problems.append(f"{key}: route removed")
        elif key not in golden:
            problems.append(f"{key}: new route, not in the snapshot")
        else:
            roles = ROLES if golden[key]["guarded"] else tuple(r for r in ROLES if r not in PLATFORM_ROLES)
            for r in roles:
                if golden[key][r] != now[key][r]:
                    problems.append(f"{key}: {r} was {'allowed' if golden[key][r] else 'denied'}, now {'allowed' if now[key][r] else 'denied'}")
    return problems
