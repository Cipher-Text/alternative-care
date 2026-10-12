"""Doctor-facing directory API: own listing, contact requests, month-to-date contact numbers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.modules.directory.service import DirectoryService
from app.shared.schemas import (
    ContactRequestResponse,
    ContactRequestUpdate,
    DirectoryStats,
    ListingResponse,
    ListingUpdate,
)

router = APIRouter()

# Tenant doctors only: the listing is the doctor's public face. Receptionists and platform users
# have no access (platform users have no tenant).
Doctor = Annotated[CurrentUser, Depends(require_role("doctor"))]


def get_service(db: Annotated[AsyncSession, Depends(get_db)], user: Doctor) -> DirectoryService:
    return DirectoryService(db, tenant_id=user.tenant_id, user_id=user.user_id)


Service = Annotated[DirectoryService, Depends(get_service)]


@router.get("/listing", response_model=ListingResponse)
async def get_listing(service: Service):
    """Own listing (or an empty default) with the reasons it is or is not public yet."""
    return await service.get_listing()


@router.put("/listing", response_model=ListingResponse)
async def save_listing(data: ListingUpdate, service: Service):
    return await service.upsert_listing(data)


@router.get("/stats", response_model=DirectoryStats)
async def get_stats(service: Service):
    return await service.stats()


@router.get("/requests", response_model=list[ContactRequestResponse])
async def list_requests(
    service: Service,
    status_filter: str | None = Query(None, alias="status", pattern="^(new|contacted|closed)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list_requests(status_filter, limit, offset)


@router.patch("/requests/{request_id}", response_model=ContactRequestResponse)
async def update_request(request_id: str, data: ContactRequestUpdate, service: Service):
    return await service.update_request(request_id, data.status)
