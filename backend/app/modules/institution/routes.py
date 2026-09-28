"""College/institution catalog API endpoints (Track D — always-global, no tenant CRUD)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, RequireAdmin, get_current_user
from app.modules.college.service import CollegeService
from app.shared.schemas import CollegeCreate, CollegeListItem, CollegeResponse, CollegeUpdate

router = APIRouter()


def get_college_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CollegeService:
    return CollegeService(db=db)


ServiceDep = Annotated[CollegeService, Depends(get_college_service)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/", response_model=list[CollegeListItem])
async def list_colleges(
    service: ServiceDep,
    _: UserDep,
    discipline: str | None = Query(None, description="Filter by discipline"),
    college_type: str | None = Query(None, description="Filter by government/private"),
    district_id: int | None = Query(None, description="Filter by district"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List institutions teaching alternative-medicine disciplines.

    - Every row is admin-curated and visible to every authenticated caller
    - Filter by discipline (homeopathy, ayurveda, unani, herbal), type (government/private), or district
    """
    return await service.list_colleges(
        discipline=discipline,
        college_type=college_type,
        district_id=district_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=CollegeResponse, status_code=status.HTTP_201_CREATED)
async def create_college(data: CollegeCreate, service: ServiceDep, user: RequireAdmin):
    """Create a college. Admin-only."""
    return await service.create_college(data, created_by=user.user_id)


@router.get("/{college_id}", response_model=CollegeResponse)
async def get_college(college_id: int, service: ServiceDep, _: UserDep):
    """Get college details."""
    return await service.get_college(college_id)


@router.patch("/{college_id}", response_model=CollegeResponse)
async def update_college(
    college_id: int, data: CollegeUpdate, service: ServiceDep, user: RequireAdmin
):
    """
    Update a college. Admin-only.

    - Setting `is_verified=true` for the first time stamps `verified_at`/`verified_by`
    """
    return await service.update_college(college_id, data, updated_by=user.user_id)


@router.delete("/{college_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_college(college_id: int, service: ServiceDep, user: RequireAdmin):
    """Deactivate a college. Admin-only."""
    await service.deactivate_college(college_id, updated_by=user.user_id)
