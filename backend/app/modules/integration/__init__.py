"""Integration module - SMS, Email, Payment providers."""

from fastapi import APIRouter

from app.modules.integration import routes

router = APIRouter()
router.include_router(routes.router)

__all__ = ["router"]
