"""Patient identity across clinics (ADR 009)."""

from app.modules.identity.portal_routes import router as portal_router
from app.modules.identity.routes import public_router, router

__all__ = ["router", "public_router", "portal_router"]
