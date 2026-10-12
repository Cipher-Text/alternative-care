"""Route registration regression tests for API path sync."""

from collections import defaultdict

from app.main import app


def _methods_by_path() -> dict[str, set[str]]:
    routes: dict[str, set[str]] = defaultdict(set)
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path and methods:
            routes[path].update(method for method in methods if method not in {"HEAD", "OPTIONS"})
    return routes


def test_appointments_routes_are_not_double_prefixed():
    routes = _methods_by_path()

    assert {"GET", "POST"}.issubset(routes["/api/v1/appointments"])
    assert {"GET", "PATCH", "DELETE"}.issubset(routes["/api/v1/appointments/{appointment_id}"])
    assert {"GET", "POST"}.issubset(routes["/api/v1/appointments/visits"])
    assert "/api/v1/appointments/appointments" not in routes
    assert "/api/v1/appointments/appointments/visits" not in routes


def test_static_search_routes_are_registered_before_dynamic_id_fallbacks():
    routes = _methods_by_path()

    assert routes["/api/v1/medicines/search"] == {"GET"}
    assert routes["/api/v1/symptoms/search"] == {"GET"}
    assert routes["/api/v1/medicines/{medicine_id:int}"] >= {"GET", "PATCH", "DELETE"}
    assert routes["/api/v1/symptoms/{symptom_id:int}"] >= {"GET", "PATCH", "DELETE"}


def test_public_catalogs_are_not_routed_but_stats_is():
    routes = _methods_by_path()

    assert routes["/api/v1/public/stats"] == {"GET"}
    assert not any(p.startswith("/api/v1/public/medicines") for p in routes)
    assert not any(p.startswith("/api/v1/public/symptoms") for p in routes)


def test_current_api_route_count_matches_docs():
    api_method_count = sum(
        len([method for method in getattr(route, "methods", set()) if method not in {"HEAD", "OPTIONS"}])
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1")
    )

    # D4: +6 for the new /api/v1/public/* router (medicines list/search/get,
    # symptoms list/search/get) — 131 -> 137. Institutions (Track D): +5 for
    # /api/v1/institutions (list/create/get/update/delete) +2 for
    # /api/v1/public/institutions (list/get) — 137 -> 144. Plans & entitlements: +1
    # /api/v1/plans, +3 /api/v1/admin/plans (list/audit/update), +3
    # /api/v1/admin/tenants/{id}/entitlements (get/put/delete), +1 /api/v1/entitlements/me
    # — 144 -> 152. Pharmacy directory: +6 (/api/v1/pharmacies list/create/import/get/update/
    # deactivate) — 152 -> 158. PATCH /auth/me/language — 158 -> 159.
    # Public medicine/symptom list/search/get removed (-6) and GET /public/stats added (+1)
    # — 159 -> 154.
    # Editorial content (Phase 1): +9 /api/v1/articles authoring, +2 /public/articles — 154 -> 165.
    # Directory (Phase 2): +5 /directory, +1 admin verification, +5 /public/practitioners — 165 -> 176.
    # Billing (platform messaging credits): +2 /billing, +2 admin (credits adjust, messaging status) — 176 -> 180.
    # Checkout: +6 /billing (subscription, packs, checkout, orders x2, fake-gateway), +4 /admin/billing — 180 -> 190.
    assert api_method_count == 190
