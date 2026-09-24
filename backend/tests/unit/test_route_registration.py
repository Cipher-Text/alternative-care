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


def test_current_api_route_count_matches_docs():
    api_method_count = sum(
        len([method for method in getattr(route, "methods", set()) if method not in {"HEAD", "OPTIONS"}])
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1")
    )

    assert api_method_count == 136
