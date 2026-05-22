"""Medicine API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.shared.models import Medicine, MedicineAlias
from app.shared.schemas import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse,
    MedicineListItem,
    MedicineSearchResult,
    MedicineAliasCreate,
    MedicineAliasUpdate,
    MedicineAliasResponse,
)

router = APIRouter()


# ===== Medicine CRUD =====


@router.get("/", response_model=list[MedicineListItem])
async def list_medicines(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
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
    query = select(Medicine).where(Medicine.deleted_at.is_(None))

    # Include global medicines OR tenant-specific medicines
    query = query.where(
        or_(
            Medicine.is_global == True,
            Medicine.tenant_id == user.tenant_id
        )
    )

    if system:
        query = query.where(Medicine.system == system)

    if category:
        query = query.where(Medicine.category == category)

    if is_global is not None:
        query = query.where(Medicine.is_global == is_global)

    if is_active is not None:
        query = query.where(Medicine.is_active == is_active)

    query = query.order_by(Medicine.name_en).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    data: MedicineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create medicine.

    - Doctors can create tenant-specific medicines
    - Only admins can create global medicines (is_global=true)
    - Bilingual support (name_en, name_bn)
    """
    # Only admins can create global medicines
    if data.is_global and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create global medicines"
        )

    medicine = Medicine(
        **data.model_dump(),
        tenant_id=None if data.is_global else user.tenant_id,
        created_by=user.user_id,
    )

    db.add(medicine)
    await db.commit()
    await db.refresh(medicine)

    return medicine


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(
    medicine_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Get medicine details.

    - Returns full medicine information
    - Includes dosage guidance, indications, contraindications
    """
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.deleted_at.is_(None),
            or_(
                Medicine.is_global == True,
                Medicine.tenant_id == user.tenant_id
            )
        )
    )

    medicine = result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    return medicine


@router.patch("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update medicine.

    - Can only update tenant-specific medicines (not global)
    - Partial updates supported
    """
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.tenant_id == user.tenant_id,
            Medicine.is_global == False,
            Medicine.deleted_at.is_(None)
        )
    )

    medicine = result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or cannot be updated"
        )

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)

    medicine.updated_by = user.user_id

    await db.commit()
    await db.refresh(medicine)

    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(
    medicine_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Delete medicine (soft delete).

    - Can only delete tenant-specific medicines (not global)
    - Soft delete: sets deleted_at timestamp
    """
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.tenant_id == user.tenant_id,
            Medicine.is_global == False,
            Medicine.deleted_at.is_(None)
        )
    )

    medicine = result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found or cannot be deleted"
        )

    medicine.deleted_at = func.now()
    await db.commit()


# ===== Medicine Search =====


@router.get("/search", response_model=list[MedicineSearchResult])
async def search_medicines(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
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
    search_term = f"%{q.lower()}%"

    # Search in medicine names
    name_query = select(Medicine).where(
        Medicine.deleted_at.is_(None),
        Medicine.is_active == True,
        or_(
            Medicine.is_global == True,
            Medicine.tenant_id == user.tenant_id
        ),
        or_(
            func.lower(Medicine.name_en).like(search_term),
            func.lower(Medicine.name_bn).like(search_term)
        )
    )

    if system:
        name_query = name_query.where(Medicine.system == system)

    name_results = await db.execute(name_query.limit(limit))
    medicines_from_name = name_results.scalars().all()

    # Search in aliases
    alias_query = select(Medicine, MedicineAlias.alias_en).join(
        MedicineAlias,
        Medicine.id == MedicineAlias.medicine_id
    ).where(
        Medicine.deleted_at.is_(None),
        Medicine.is_active == True,
        MedicineAlias.is_active == True,
        or_(
            Medicine.is_global == True,
            Medicine.tenant_id == user.tenant_id
        ),
        or_(
            func.lower(MedicineAlias.alias_en).like(search_term),
            func.lower(MedicineAlias.alias_bn).like(search_term)
        )
    )

    if system:
        alias_query = alias_query.where(Medicine.system == system)

    alias_results = await db.execute(alias_query.limit(limit))
    medicines_from_alias = [
        (medicine, alias) for medicine, alias in alias_results.all()
    ]

    # Combine results
    results = []

    # Add name matches
    for medicine in medicines_from_name:
        results.append(MedicineSearchResult(
            id=medicine.id,
            name_en=medicine.name_en,
            name_bn=medicine.name_bn,
            system=medicine.system,
            potency=medicine.potency,
            category=medicine.category,
            matched_alias=None,
            rank=1.0  # Exact name matches get highest rank
        ))

    # Add alias matches
    for medicine, matched_alias in medicines_from_alias:
        # Skip if already added from name match
        if medicine.id not in [r.id for r in results]:
            results.append(MedicineSearchResult(
                id=medicine.id,
                name_en=medicine.name_en,
                name_bn=medicine.name_bn,
                system=medicine.system,
                potency=medicine.potency,
                category=medicine.category,
                matched_alias=matched_alias,
                rank=0.8  # Alias matches get lower rank
            ))

    # Sort by rank and limit
    results.sort(key=lambda x: x.rank, reverse=True)
    return results[:limit]


# ===== Medicine Aliases =====


@router.post("/{medicine_id}/aliases", response_model=MedicineAliasResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine_alias(
    medicine_id: int,
    data: MedicineAliasCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create medicine alias.

    - Add alternative names, brand names, transliterations
    - Improves search results
    """
    # Verify medicine exists and is accessible
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.deleted_at.is_(None),
            or_(
                Medicine.is_global == True,
                Medicine.tenant_id == user.tenant_id
            )
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    alias = MedicineAlias(
        **data.model_dump(),
        medicine_id=medicine_id,
        tenant_id=user.tenant_id,
        created_by=user.user_id,
    )

    db.add(alias)
    await db.commit()
    await db.refresh(alias)

    return alias


@router.get("/{medicine_id}/aliases", response_model=list[MedicineAliasResponse])
async def list_medicine_aliases(
    medicine_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    List aliases for a medicine.

    - Shows all alternative names
    - Includes alias type and priority
    """
    # Verify medicine exists
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.deleted_at.is_(None),
            or_(
                Medicine.is_global == True,
                Medicine.tenant_id == user.tenant_id
            )
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    # Get aliases
    aliases_result = await db.execute(
        select(MedicineAlias).where(
            MedicineAlias.medicine_id == medicine_id,
            MedicineAlias.is_active == True
        ).order_by(MedicineAlias.priority.desc())
    )

    return aliases_result.scalars().all()


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine_alias(
    alias_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Delete medicine alias.

    - Can only delete aliases created by your tenant
    """
    result = await db.execute(
        select(MedicineAlias).where(
            MedicineAlias.id == alias_id,
            MedicineAlias.tenant_id == user.tenant_id
        )
    )

    alias = result.scalar_one_or_none()

    if not alias:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alias not found"
        )

    await db.delete(alias)
    await db.commit()
