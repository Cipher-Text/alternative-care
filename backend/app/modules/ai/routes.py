"""AI API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireProPlan
from app.core.usage_tracking import UsageService

router = APIRouter()


@router.post("/query", summary="AI query (stub)")
async def ai_query_stub(user: RequireProPlan, db: Annotated[AsyncSession, Depends(get_db)]):
    """Placeholder AI endpoint until the full AI module is implemented."""
    await UsageService(db, user.tenant_id).increment("ai_queries_made")
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": "AI module is planned but not implemented yet.",
            "status": "not_implemented",
        },
    )
