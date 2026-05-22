"""Medicine module."""

from fastapi import APIRouter
from app.modules.medicine.routes import router as medicine_router
from app.modules.medicine.mapping_routes import router as mapping_router

# Combine routers
router = APIRouter()
router.include_router(medicine_router)
router.include_router(mapping_router)

__all__ = ["router"]
