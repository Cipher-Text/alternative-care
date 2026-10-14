"""Pharmacy directory API (admin-curated, always-global; practitioners read, admins write)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.pharmacy.service import MAX_IMPORT_BYTES, PharmacyService
from app.shared.schemas import (
    PharmacyCreate,
    PharmacyImportResult,
    PharmacyListItem,
    PharmacyResponse,
    PharmacyUpdate,
)

router = APIRouter()

Needs_pharmacies_manage = Annotated[CurrentUser, Depends(require_permission("pharmacies.manage"))]



def get_pharmacy_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PharmacyService:
    return PharmacyService(db=db)


ServiceDep = Annotated[PharmacyService, Depends(get_pharmacy_service)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/", response_model=list[PharmacyListItem])
async def list_pharmacies(
    service: ServiceDep,
    _: UserDep,
    search: str | None = Query(None, description="Match name (English/Bengali) or address"),
    discipline: str | None = Query(None, description="homeopathy, ayurveda, unani or herbal"),
    pharmacy_type: str | None = Query(None, description="retail, wholesale, manufacturer, depot"),
    district_id: int | None = Query(None),
    delivers: bool | None = Query(None, description="Only listings that deliver / courier"),
    lat: float | None = Query(None, ge=-90, le=90, description="Your latitude (near-me search)"),
    lon: float | None = Query(None, ge=-180, le=180, description="Your longitude (near-me search)"),
    radius_km: float = Query(10, gt=0, le=200, description="Near-me radius"),
    is_active: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List pharmacies, wholesalers and depots.

    - Visible to every authenticated user; only admins edit
    - Give `lat` and `lon` for a near-me search: only listings with a map pin within `radius_km`
      are returned, nearest first, each with `distance_km`
    """
    if (lat is None) != (lon is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="lat and lon must be provided together",
        )
    return await service.list_pharmacies(
        search=search,
        discipline=discipline,
        pharmacy_type=pharmacy_type,
        district_id=district_id,
        delivers=delivers,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=PharmacyResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacy(data: PharmacyCreate, service: ServiceDep, user: Needs_pharmacies_manage):
    """Create a pharmacy listing. Admin-only."""
    return await service.create_pharmacy(data, created_by=user.user_id)


@router.post("/import", response_model=PharmacyImportResult)
async def import_pharmacies(
    service: ServiceDep,
    user: Needs_pharmacies_manage,
    file: Annotated[UploadFile, File(description="UTF-8 CSV with a header row")],
):
    """
    Bulk-create pharmacies from a CSV. Admin-only.

    - All-or-nothing: if any row is invalid nothing is saved and every bad row is reported
    - Rows that already exist (same name, same district) are skipped
    - Up to 1000 rows / 2 MB
    """
    raw = await file.read(MAX_IMPORT_BYTES + 1)
    return await service.import_csv(raw, created_by=user.user_id)


@router.get("/{pharmacy_id}", response_model=PharmacyResponse)
async def get_pharmacy(pharmacy_id: int, service: ServiceDep, _: UserDep):
    """Get pharmacy details."""
    return await service.get_pharmacy(pharmacy_id)


@router.patch("/{pharmacy_id}", response_model=PharmacyResponse)
async def update_pharmacy(
    pharmacy_id: int, data: PharmacyUpdate, service: ServiceDep, user: Needs_pharmacies_manage
):
    """
    Update a pharmacy. Admin-only.

    - `is_verified=true` (first time) stamps `verified_at`/`verified_by`
    - `mark_confirmed=true` stamps `last_confirmed_at` ("re-checked today")
    """
    return await service.update_pharmacy(pharmacy_id, data, updated_by=user.user_id)


@router.delete("/{pharmacy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_pharmacy(pharmacy_id: int, service: ServiceDep, user: Needs_pharmacies_manage):
    """Deactivate a pharmacy (hidden from lists, kept for history). Admin-only."""
    await service.deactivate_pharmacy(pharmacy_id, updated_by=user.user_id)
