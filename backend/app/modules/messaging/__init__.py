"""Messaging module: SMS and email a clinic sends through the platform's own providers."""

from fastapi import APIRouter

from app.modules.messaging import routes

router = APIRouter()
router.include_router(routes.router)

__all__ = ["router"]
