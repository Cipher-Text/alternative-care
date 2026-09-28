"""Public API endpoints (D4) — unauthenticated, read-only, global-catalog-only.

No route here takes a `CurrentUser` dependency; that's the whole point of
this router boundary. For medicines/symptoms, visibility is enforced by
constructing the service with `tenant_id=None`, which `GlobalCatalogService`'s
`_visible_query()` / `_fulltext_search()` already narrow to `is_global=True`
rows only — the same mechanism a platform admin's view uses
(`app/core/base_service.py`), reused rather than duplicated for the public
case. Colleges have no tenant scoping at all (they aren't tenants), so
`CollegeService` is exposed here as a straight passthrough instead.

Deliberately not exposed here: `MedicineService.get_medicine_symptoms` /
`get_symptom_medicines` (the cross-lookup endpoints). Both query
`MedicineSymptomMapping` without any `is_global`/tenant filter on the
other side of the join — safe today only because every existing caller is
already authenticated and limited to their own visible rows anyway. Public
callers have no such implicit boundary, so exposing them here would leak
tenant-owned medicines/symptoms through the mapping join. Fixing the
service methods to filter is a separate, focused change; not bundled in
here to keep this router's own change small and reviewable.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.college.service import CollegeService
from app.modules.medicine.service import MedicineService
from app.modules.symptom.service import SymptomService
from app.shared.schemas import (
    CollegeListItem,
    MedicineListItem,
    MedicineResponse,
    MedicineSearchResult,
    SymptomListItem,
    SymptomResponse,
    SymptomSearchResult,
)

router = APIRouter()


def get_public_medicine_service(db: Annotated[AsyncSession, Depends(get_db)]) -> MedicineService:
    """Global-only view — no caller tenant, per this router's whole premise."""
    return MedicineService(db=db, tenant_id=None)


def get_public_symptom_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SymptomService:
    """Global-only view — no caller tenant, per this router's whole premise."""
    return SymptomService(db=db, tenant_id=None)


def get_public_college_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CollegeService:
    """Colleges have no tenant scoping at all — every row is already public data."""
    return CollegeService(db=db)


MedicineServiceDep = Annotated[MedicineService, Depends(get_public_medicine_service)]
SymptomServiceDep = Annotated[SymptomService, Depends(get_public_symptom_service)]
CollegeServiceDep = Annotated[CollegeService, Depends(get_public_college_service)]


# ===== Medicines =====


@router.get("/medicines", response_model=list[MedicineListItem])
async def list_public_medicines(
    service: MedicineServiceDep,
    system: str | None = Query(None, description="Filter by medical system"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Browse the admin-curated global medicine catalog."""
    return await service.list_medicines(
        system=system,
        category=category,
        is_global=True,
        is_active=True,
        limit=limit,
        offset=offset,
    )


@router.get("/medicines/search", response_model=list[MedicineSearchResult])
async def search_public_medicines(
    service: MedicineServiceDep,
    q: str = Query(..., min_length=1, description="Search query"),
    system: str | None = Query(None, description="Filter by medical system"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search the global medicine catalog (unified tsvector search, D5)."""
    return await service.search_medicines(q, system=system, limit=limit)


@router.get("/medicines/{medicine_id:int}", response_model=MedicineResponse)
async def get_public_medicine(medicine_id: int, service: MedicineServiceDep):
    """Get a global medicine's full detail. 404s for a tenant-owned medicine."""
    return await service.get_medicine(medicine_id)


# ===== Symptoms =====


@router.get("/symptoms", response_model=list[SymptomListItem])
async def list_public_symptoms(
    service: SymptomServiceDep,
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Browse the admin-curated global symptom catalog."""
    return await service.list_symptoms(
        category=category,
        is_global=True,
        is_active=True,
        limit=limit,
        offset=offset,
    )


@router.get("/symptoms/search", response_model=list[SymptomSearchResult])
async def search_public_symptoms(
    service: SymptomServiceDep,
    q: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search the global symptom catalog (unified tsvector search, D5)."""
    return await service.search_symptoms(q, category=category, limit=limit)


@router.get("/symptoms/{symptom_id:int}", response_model=SymptomResponse)
async def get_public_symptom(symptom_id: int, service: SymptomServiceDep):
    """Get a global symptom's full detail. 404s for a tenant-owned symptom."""
    return await service.get_symptom(symptom_id)


# ===== Colleges =====
#
# Every row is already admin-curated/global (no tenant scoping exists for
# colleges at all), so this is a straight passthrough onto CollegeService —
# no visibility narrowing needed, unlike medicines/symptoms above.


@router.get("/colleges", response_model=list[CollegeListItem])
async def list_public_colleges(
    service: CollegeServiceDep,
    discipline: str | None = Query(None, description="Filter by discipline"),
    college_type: str | None = Query(None, description="Filter by government/private"),
    district_id: int | None = Query(None, description="Filter by district"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Browse the admin-curated directory of alternative-medicine institutions."""
    return await service.list_colleges(
        discipline=discipline,
        college_type=college_type,
        district_id=district_id,
        is_active=True,
        limit=limit,
        offset=offset,
    )


@router.get("/colleges/{college_id:int}", response_model=CollegeListItem)
async def get_public_college(college_id: int, service: CollegeServiceDep):
    """Get an institution's public detail."""
    return await service.get_college(college_id)
