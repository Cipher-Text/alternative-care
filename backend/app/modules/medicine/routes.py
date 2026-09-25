"""Medicine API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.medicine.service import MedicineService
from app.shared.schemas import (
    MedicineAliasCreate,
    MedicineAliasResponse,
    MedicineCreate,
    MedicineListItem,
    MedicineResponse,
    MedicineSearchResult,
    MedicineSymptomMappingCreate,
    MedicineSymptomMappingResponse,
    MedicineSymptomMappingUpdate,
    MedicineUpdate,
    SymptomListItem,
)

router = APIRouter()


def get_medicine_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> MedicineService:
    """Service for the caller's tenant, or a platform admin's global-only view."""
    return MedicineService(db=db, tenant_id=user.tenant_id)


ServiceDep = Annotated[MedicineService, Depends(get_medicine_service)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]


# ===== Medicine CRUD =====


@router.get("/", response_model=list[MedicineListItem])
async def list_medicines(
    service: ServiceDep,
    system: str | None = Query(None, description="Filter by medical system"),
    category: str | None = Query(None, description="Filter by category"),
    is_global: bool | None = Query(None, description="Filter by global/tenant"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List medicines.

    - Returns global medicines + tenant-specific medicines
    - Filter by medical system (homeopathy, ayurveda, unani, herbal)
    - Filter by category, active status
    - Paginated results
    """
    return await service.list_medicines(
        system=system,
        category=category,
        is_global=is_global,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(data: MedicineCreate, service: ServiceDep, user: UserDep):
    """
    Create medicine.

    - Doctors can create tenant-specific medicines
    - Only admins can create global medicines (is_global=true)
    - Bilingual support (name_en, name_bn)
    """
    return await service.create_medicine(data, created_by=user.user_id, role=user.role)


@router.get("/{medicine_id:int}", response_model=MedicineResponse)
async def get_medicine(medicine_id: int, service: ServiceDep):
    """
    Get medicine details.

    - Returns full medicine information
    - Includes dosage guidance, indications, contraindications
    """
    return await service.get_medicine(medicine_id)


@router.patch("/{medicine_id:int}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int, data: MedicineUpdate, service: ServiceDep, user: UserDep
):
    """
    Update medicine.

    - Can only update tenant-specific medicines (not global)
    - Partial updates supported
    """
    return await service.update_medicine(medicine_id, data, updated_by=user.user_id)


@router.delete("/{medicine_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(medicine_id: int, service: ServiceDep, user: UserDep):
    """
    Deactivate medicine.

    - Can only delete tenant-specific medicines (not global)
    - Marks record inactive
    """
    await service.deactivate_medicine(medicine_id, updated_by=user.user_id)


# ===== Medicine Search =====


@router.get("/search", response_model=list[MedicineSearchResult])
async def search_medicines(
    service: ServiceDep,
    q: str = Query(..., min_length=1, description="Search query"),
    system: str | None = Query(None, description="Filter by medical system"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search medicines with autocomplete support.

    - Searches medicine names (English/Bengali)
    - Searches aliases (brand names, transliterations)
    - Returns ranked results
    - Used for prescription autocomplete
    """
    return await service.search_medicines(q, system=system, limit=limit)


# ===== Medicine Aliases =====


@router.post(
    "/{medicine_id:int}/aliases",
    response_model=MedicineAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medicine_alias(
    medicine_id: int, data: MedicineAliasCreate, service: ServiceDep, user: UserDep
):
    """
    Create medicine alias.

    - Add alternative names, brand names, transliterations
    - Improves search results
    """
    return await service.create_alias(medicine_id, data, created_by=user.user_id)


@router.get("/{medicine_id:int}/aliases", response_model=list[MedicineAliasResponse])
async def list_medicine_aliases(medicine_id: int, service: ServiceDep):
    """
    List aliases for a medicine.

    - Shows all alternative names
    - Includes alias type and priority
    """
    return await service.list_aliases(medicine_id)


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine_alias(alias_id: int, service: ServiceDep):
    """
    Delete medicine alias.

    - Can only delete aliases created by your tenant
    """
    await service.delete_alias(alias_id)


# ===== Medicine-Symptom Mapping CRUD =====


@router.post(
    "/mappings",
    response_model=MedicineSymptomMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mapping(
    data: MedicineSymptomMappingCreate, service: ServiceDep, user: UserDep
):
    """
    Link medicine to symptom.

    - Create relationship between medicine and symptom
    - Set strength rating (1-10)
    - Add modality notes (e.g., "worse at night")
    """
    return await service.create_mapping(data, created_by=user.user_id)


@router.get("/mappings/{mapping_id}", response_model=MedicineSymptomMappingResponse)
async def get_mapping(mapping_id: int, service: ServiceDep):
    """
    Get mapping details.

    - Returns medicine-symptom relationship
    - Includes strength and modality
    """
    return await service.get_mapping(mapping_id)


@router.patch("/mappings/{mapping_id}", response_model=MedicineSymptomMappingResponse)
async def update_mapping(
    mapping_id: int, data: MedicineSymptomMappingUpdate, service: ServiceDep, user: UserDep
):
    """
    Update medicine-symptom mapping.

    - Update strength rating
    - Update modality notes
    - Partial updates supported
    """
    return await service.update_mapping(mapping_id, data, updated_by=user.user_id)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(mapping_id: int, service: ServiceDep):
    """
    Delete medicine-symptom mapping.

    - Removes relationship
    - Does not delete medicine or symptom
    """
    await service.delete_mapping(mapping_id)


# ===== Get Symptoms for Medicine =====


@router.get("/{medicine_id:int}/symptoms", response_model=list[SymptomListItem])
async def get_medicine_symptoms(
    medicine_id: int,
    service: ServiceDep,
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get all symptoms linked to a medicine.

    - Returns symptoms ordered by mapping strength
    - Useful for medicine detail pages
    """
    return await service.get_medicine_symptoms(medicine_id, limit=limit)


# ===== Get Medicines for Symptom =====


@router.get("/symptoms/{symptom_id}/medicines", response_model=list[MedicineListItem])
async def get_symptom_medicines(
    symptom_id: int,
    service: ServiceDep,
    system: str | None = Query(None, description="Filter by medical system"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get all medicines linked to a symptom.

    - Returns medicines ordered by mapping strength
    - Filter by medical system
    - Useful for symptom detail pages and AI recommendations
    """
    return await service.get_symptom_medicines(symptom_id, system=system, limit=limit)
