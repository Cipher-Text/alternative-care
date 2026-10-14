"""Institution catalog API endpoints (Track D — always-global, no tenant CRUD)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.institution.service import InstitutionService
from app.shared.schemas import (
    InstitutionCreate,
    InstitutionListItem,
    InstitutionResponse,
    InstitutionUpdate,
)

router = APIRouter()

Needs_institutions_manage = Annotated[CurrentUser, Depends(require_permission("institutions.manage"))]



def get_institution_service(db: Annotated[AsyncSession, Depends(get_db)]) -> InstitutionService:
    return InstitutionService(db=db)


ServiceDep = Annotated[InstitutionService, Depends(get_institution_service)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/", response_model=list[InstitutionListItem])
async def list_institutions(
    service: ServiceDep,
    _: UserDep,
    discipline: str | None = Query(None, description="Filter by discipline"),
    institution_type: str | None = Query(None, description="Filter by government/private"),
    district_id: int | None = Query(None, description="Filter by district"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List educational institutions teaching alternative-medicine disciplines.

    - Every row is admin-curated and visible to every authenticated caller
    - Filter by discipline (homeopathy, ayurveda, unani, herbal), type (government/private), or district
    """
    return await service.list_institutions(
        discipline=discipline,
        institution_type=institution_type,
        district_id=district_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(data: InstitutionCreate, service: ServiceDep, user: Needs_institutions_manage):
    """Create an institution. Admin-only."""
    return await service.create_institution(data, created_by=user.user_id)


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(institution_id: int, service: ServiceDep, _: UserDep):
    """Get institution details."""
    return await service.get_institution(institution_id)


@router.patch("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: int, data: InstitutionUpdate, service: ServiceDep, user: Needs_institutions_manage
):
    """
    Update an institution. Admin-only.

    - Setting `is_verified=true` for the first time stamps `verified_at`/`verified_by`
    """
    return await service.update_institution(institution_id, data, updated_by=user.user_id)


@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_institution(institution_id: int, service: ServiceDep, user: Needs_institutions_manage):
    """Deactivate an institution. Admin-only."""
    await service.deactivate_institution(institution_id, updated_by=user.user_id)
