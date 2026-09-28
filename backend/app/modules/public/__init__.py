"""Public module — unauthenticated read-only access to the global catalog (D4)."""

from app.modules.public.routes import router

__all__ = ["router"]
