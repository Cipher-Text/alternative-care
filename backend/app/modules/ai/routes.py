"""AI API routes."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.dependencies import RequireProPlan

router = APIRouter()


@router.post("/query", summary="AI query (stub)")
async def ai_query_stub(user: RequireProPlan):
    """Placeholder AI endpoint until the full AI module is implemented."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": "AI module is planned but not implemented yet.",
            "status": "not_implemented",
        },
    )
