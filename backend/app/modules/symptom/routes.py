"""Symptom API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.symptom.service import SymptomService
from app.shared.schemas import (
    SymptomAliasCreate,
    SymptomAliasResponse,
    SymptomCreate,
    SymptomListItem,
    SymptomResponse,
    SymptomSearchResult,
    SymptomUpdate,
)

router = APIRouter()


def get_symptom_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SymptomService:
    """Service for the caller's tenant, or a platform admin's global-only view."""
    return SymptomService(db=db, tenant_id=user.tenant_id)


ServiceDep = Annotated[SymptomService, Depends(get_symptom_service)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]


# ===== Symptom CRUD =====


@router.get("/", response_model=list[SymptomListItem])
async def list_symptoms(
    service: ServiceDep,
    category: str | None = Query(None, description="Filter by category"),
    is_global: bool | None = Query(None, description="Filter by global/tenant"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List symptoms.

    - Returns global symptoms + tenant-specific symptoms
    - Filter by category (respiratory, digestive, etc.)
    - Paginated results
    """
    return await service.list_symptoms(
        category=category,
        is_global=is_global,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=SymptomResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom(data: SymptomCreate, service: ServiceDep, user: UserDep):
    """
    Create symptom.

    - Doctors can create tenant-specific symptoms
    - Only admins can create global symptoms
    - Bilingual support (name_en, name_bn)
    """
    return await service.create_symptom(data, created_by=user.user_id, role=user.role)


@router.get("/{symptom_id:int}", response_model=SymptomResponse)
async def get_symptom(symptom_id: int, service: ServiceDep):
    """
    Get symptom details.

    - Returns full symptom information
    - Includes description and category
    """
    return await service.get_symptom(symptom_id)


@router.patch("/{symptom_id:int}", response_model=SymptomResponse)
async def update_symptom(
    symptom_id: int, data: SymptomUpdate, service: ServiceDep, user: UserDep
):
    """
    Update symptom.

    - Can only update tenant-specific symptoms (not global)
    - Partial updates supported
    """
    return await service.update_symptom(symptom_id, data, updated_by=user.user_id)


@router.delete("/{symptom_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom(symptom_id: int, service: ServiceDep, user: UserDep):
    """
    Deactivate symptom.

    - Can only delete tenant-specific symptoms (not global)
    - Marks record inactive
    """
    await service.deactivate_symptom(symptom_id, updated_by=user.user_id)


# ===== Symptom Search =====


@router.get("/search", response_model=list[SymptomSearchResult])
async def search_symptoms(
    service: ServiceDep,
    q: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search symptoms with autocomplete support.

    - Searches symptom names (English/Bengali)
    - Searches aliases (transliterations, regional variations)
    - Returns ranked results
    - Used for patient intake forms and AI queries
    """
    return await service.search_symptoms(q, category=category, limit=limit)


# ===== Symptom Aliases =====


@router.post(
    "/{symptom_id:int}/aliases",
    response_model=SymptomAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_symptom_alias(
    symptom_id: int, data: SymptomAliasCreate, service: ServiceDep, user: UserDep
):
    """
    Create symptom alias.

    - Add alternative names, transliterations, regional variations
    - Improves search results for multilingual support
    """
    return await service.create_alias(symptom_id, data, created_by=user.user_id)


@router.get("/{symptom_id:int}/aliases", response_model=list[SymptomAliasResponse])
async def list_symptom_aliases(symptom_id: int, service: ServiceDep):
    """
    List aliases for a symptom.

    - Shows all alternative names
    - Includes alias type and priority
    """
    return await service.list_aliases(symptom_id)


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom_alias(alias_id: int, service: ServiceDep):
    """
    Delete symptom alias.

    - Can only delete aliases created by your tenant
    """
    await service.delete_alias(alias_id)
