"""Symptom API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.shared.models import Symptom, SymptomAlias
from app.shared.schemas import (
    SymptomCreate,
    SymptomUpdate,
    SymptomResponse,
    SymptomListItem,
    SymptomSearchResult,
    SymptomAliasCreate,
    SymptomAliasUpdate,
    SymptomAliasResponse,
)

router = APIRouter()


# ===== Symptom CRUD =====


@router.get("/", response_model=list[SymptomListItem])
async def list_symptoms(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
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
    query = select(Symptom)

    # Include global symptoms OR tenant-specific symptoms
    query = query.where(
        or_(
            Symptom.is_global == True,
            Symptom.tenant_id == user.tenant_id
        )
    )

    if category:
        query = query.where(Symptom.category == category)

    if is_global is not None:
        query = query.where(Symptom.is_global == is_global)

    if is_active is not None:
        query = query.where(Symptom.is_active == is_active)

    query = query.order_by(Symptom.name_en).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=SymptomResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom(
    data: SymptomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create symptom.

    - Doctors can create tenant-specific symptoms
    - Only admins can create global symptoms
    - Bilingual support (name_en, name_bn)
    """
    # Only admins can create global symptoms
    if data.is_global and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create global symptoms"
        )

    symptom = Symptom(
        **data.model_dump(),
        tenant_id=None if data.is_global else user.tenant_id,
        created_by=user.user_id,
    )

    db.add(symptom)
    await db.commit()
    await db.refresh(symptom)

    return symptom


@router.get("/{symptom_id}", response_model=SymptomResponse)
async def get_symptom(
    symptom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Get symptom details.

    - Returns full symptom information
    - Includes description and category
    """
    result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            or_(
                Symptom.is_global == True,
                Symptom.tenant_id == user.tenant_id
            )
        )
    )

    symptom = result.scalar_one_or_none()

    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )

    return symptom


@router.patch("/{symptom_id}", response_model=SymptomResponse)
async def update_symptom(
    symptom_id: int,
    data: SymptomUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update symptom.

    - Can only update tenant-specific symptoms (not global)
    - Partial updates supported
    """
    result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            Symptom.tenant_id == user.tenant_id,
            Symptom.is_global == False
        )
    )

    symptom = result.scalar_one_or_none()

    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found or cannot be updated"
        )

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(symptom, field, value)

    symptom.updated_by = user.user_id

    await db.commit()
    await db.refresh(symptom)

    return symptom


@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom(
    symptom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Deactivate symptom.

    - Can only delete tenant-specific symptoms (not global)
    - Marks record inactive
    """
    result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            Symptom.tenant_id == user.tenant_id,
            Symptom.is_global == False
        )
    )

    symptom = result.scalar_one_or_none()

    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found or cannot be deleted"
        )

    symptom.is_active = False
    symptom.updated_by = user.user_id
    await db.commit()


# ===== Symptom Search =====


@router.get("/search", response_model=list[SymptomSearchResult])
async def search_symptoms(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
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
    search_term = f"%{q.lower()}%"

    # Search in symptom names
    name_query = select(Symptom).where(
        Symptom.is_active == True,
        or_(
            Symptom.is_global == True,
            Symptom.tenant_id == user.tenant_id
        ),
        or_(
            func.lower(Symptom.name_en).like(search_term),
            func.lower(Symptom.name_bn).like(search_term)
        )
    )

    if category:
        name_query = name_query.where(Symptom.category == category)

    name_results = await db.execute(name_query.limit(limit))
    symptoms_from_name = name_results.scalars().all()

    # Search in aliases
    alias_query = select(Symptom, SymptomAlias.alias_en).join(
        SymptomAlias,
        Symptom.id == SymptomAlias.symptom_id
    ).where(
        Symptom.is_active == True,
        SymptomAlias.is_active == True,
        or_(
            Symptom.is_global == True,
            Symptom.tenant_id == user.tenant_id
        ),
        or_(
            func.lower(SymptomAlias.alias_en).like(search_term),
            func.lower(SymptomAlias.alias_bn).like(search_term)
        )
    )

    if category:
        alias_query = alias_query.where(Symptom.category == category)

    alias_results = await db.execute(alias_query.limit(limit))
    symptoms_from_alias = [
        (symptom, alias) for symptom, alias in alias_results.all()
    ]

    # Combine results
    results = []

    # Add name matches
    for symptom in symptoms_from_name:
        results.append(SymptomSearchResult(
            symptom=symptom,
            matched_term=symptom.name_en,
            match_type="exact",
            relevance_score=1.0
        ))

    # Add alias matches
    for symptom, matched_alias in symptoms_from_alias:
        # Skip if already added from name match
        if symptom.id not in [r.symptom.id for r in results]:
            results.append(SymptomSearchResult(
                symptom=symptom,
                matched_term=matched_alias,
                match_type="alias",
                relevance_score=0.8
            ))

    # Sort by relevance and limit
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:limit]


# ===== Symptom Aliases =====


@router.post("/{symptom_id}/aliases", response_model=SymptomAliasResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom_alias(
    symptom_id: int,
    data: SymptomAliasCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create symptom alias.

    - Add alternative names, transliterations, regional variations
    - Improves search results for multilingual support
    """
    # Verify symptom exists and is accessible
    result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            or_(
                Symptom.is_global == True,
                Symptom.tenant_id == user.tenant_id
            )
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )

    alias = SymptomAlias(
        **data.model_dump(),
        symptom_id=symptom_id,
        tenant_id=user.tenant_id,
        created_by=user.user_id,
    )

    db.add(alias)
    await db.commit()
    await db.refresh(alias)

    return alias


@router.get("/{symptom_id}/aliases", response_model=list[SymptomAliasResponse])
async def list_symptom_aliases(
    symptom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    List aliases for a symptom.

    - Shows all alternative names
    - Includes alias type and priority
    """
    # Verify symptom exists
    result = await db.execute(
        select(Symptom).where(
            Symptom.id == symptom_id,
            or_(
                Symptom.is_global == True,
                Symptom.tenant_id == user.tenant_id
            )
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )

    # Get aliases
    aliases_result = await db.execute(
        select(SymptomAlias).where(
            SymptomAlias.symptom_id == symptom_id,
            SymptomAlias.is_active == True
        ).order_by(SymptomAlias.priority.desc())
    )

    return aliases_result.scalars().all()


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom_alias(
    alias_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Delete symptom alias.

    - Can only delete aliases created by your tenant
    """
    result = await db.execute(
        select(SymptomAlias).where(
            SymptomAlias.id == alias_id,
            SymptomAlias.tenant_id == user.tenant_id
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
