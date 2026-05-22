"""Medicine-Symptom mapping API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.shared.models import Medicine, Symptom, MedicineSymptomMapping
from app.shared.schemas import (
    MedicineSymptomMappingCreate,
    MedicineSymptomMappingUpdate,
    MedicineSymptomMappingResponse,
    SymptomListItem,
    MedicineListItem,
)

router = APIRouter()


# ===== Medicine-Symptom Mapping CRUD =====


@router.post("/mappings", response_model=MedicineSymptomMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: MedicineSymptomMappingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Link medicine to symptom.

    - Create relationship between medicine and symptom
    - Set strength rating (1-10)
    - Add modality notes (e.g., "worse at night")
    """
    # Verify medicine exists and is accessible
    medicine_result = await db.execute(
        select(Medicine).where(
            Medicine.id == data.medicine_id,
            Medicine.deleted_at.is_(None)
        )
    )
    medicine = medicine_result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    # Verify symptom exists and is accessible
    symptom_result = await db.execute(
        select(Symptom).where(
            Symptom.id == data.symptom_id,
            Symptom.deleted_at.is_(None)
        )
    )
    symptom = symptom_result.scalar_one_or_none()

    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )

    # Check if mapping already exists
    existing = await db.execute(
        select(MedicineSymptomMapping).where(
            and_(
                MedicineSymptomMapping.medicine_id == data.medicine_id,
                MedicineSymptomMapping.symptom_id == data.symptom_id,
                MedicineSymptomMapping.deleted_at.is_(None)
            )
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapping already exists between this medicine and symptom"
        )

    # Create mapping
    mapping = MedicineSymptomMapping(
        **data.model_dump(),
        tenant_id=user.tenant_id,
        created_by=user.user_id,
    )

    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    return mapping


@router.get("/mappings/{mapping_id}", response_model=MedicineSymptomMappingResponse)
async def get_mapping(
    mapping_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Get mapping details.

    - Returns medicine-symptom relationship
    - Includes strength and modality
    """
    result = await db.execute(
        select(MedicineSymptomMapping).where(
            MedicineSymptomMapping.id == mapping_id,
            MedicineSymptomMapping.deleted_at.is_(None)
        )
    )

    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    return mapping


@router.patch("/mappings/{mapping_id}", response_model=MedicineSymptomMappingResponse)
async def update_mapping(
    mapping_id: int,
    data: MedicineSymptomMappingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update medicine-symptom mapping.

    - Update strength rating
    - Update modality notes
    - Partial updates supported
    """
    result = await db.execute(
        select(MedicineSymptomMapping).where(
            MedicineSymptomMapping.id == mapping_id,
            MedicineSymptomMapping.deleted_at.is_(None)
        )
    )

    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mapping, field, value)

    mapping.updated_by = user.user_id

    await db.commit()
    await db.refresh(mapping)

    return mapping


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Delete medicine-symptom mapping.

    - Removes relationship
    - Does not delete medicine or symptom
    """
    result = await db.execute(
        select(MedicineSymptomMapping).where(
            MedicineSymptomMapping.id == mapping_id,
            MedicineSymptomMapping.deleted_at.is_(None)
        )
    )

    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    await db.delete(mapping)
    await db.commit()


# ===== Get Symptoms for Medicine =====


@router.get("/{medicine_id}/symptoms", response_model=list[SymptomListItem])
async def get_medicine_symptoms(
    medicine_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get all symptoms linked to a medicine.

    - Returns symptoms ordered by mapping strength
    - Useful for medicine detail pages
    """
    # Verify medicine exists
    medicine_result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.deleted_at.is_(None)
        )
    )

    if not medicine_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    # Get symptoms via mappings
    result = await db.execute(
        select(Symptom).join(
            MedicineSymptomMapping,
            Symptom.id == MedicineSymptomMapping.symptom_id
        ).where(
            MedicineSymptomMapping.medicine_id == medicine_id,
            MedicineSymptomMapping.is_active == True,
            MedicineSymptomMapping.deleted_at.is_(None),
            Symptom.deleted_at.is_(None)
        ).order_by(MedicineSymptomMapping.strength.desc()).limit(limit)
    )

    return result.scalars().all()


# ===== Get Medicines for Symptom =====


@router.get("/symptoms/{symptom_id}/medicines", response_model=list[MedicineListItem])
async def get_symptom_medicines(
    symptom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    system: str | None = Query(None, description="Filter by medical system"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get all medicines linked to a symptom.

    - Returns medicines ordered by mapping strength
    - Filter by medical system
    - Useful for symptom detail pages and AI recommendations
    """
    # Verify symptom exists
    symptom_result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            Symptom.deleted_at.is_(None)
        )
    )

    if not symptom_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )

    # Get medicines via mappings
    query = select(Medicine).join(
        MedicineSymptomMapping,
        Medicine.id == MedicineSymptomMapping.medicine_id
    ).where(
        MedicineSymptomMapping.symptom_id == symptom_id,
        MedicineSymptomMapping.is_active == True,
        MedicineSymptomMapping.deleted_at.is_(None),
        Medicine.deleted_at.is_(None)
    )

    if system:
        query = query.where(Medicine.system == system)

    query = query.order_by(MedicineSymptomMapping.strength.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
