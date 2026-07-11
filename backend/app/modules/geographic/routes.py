"""Geographic API endpoints — Bangladesh divisions, districts, upazilas."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, CurrentUser
from app.shared.models.geographic import Division, District, Upazila

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────

class DivisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_bn: str


class DistrictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    division_id: int
    name_en: str
    name_bn: str


class UpazilaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    district_id: int
    name_en: str
    name_bn: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/divisions", response_model=list[DivisionResponse])
async def list_divisions(
    _: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all Bangladesh divisions (8 total)."""
    result = await db.execute(select(Division).order_by(Division.name_en))
    return result.scalars().all()


@router.get("/divisions/{division_id}/districts", response_model=list[DistrictResponse])
async def list_districts(
    division_id: int,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all districts for a given division."""
    result = await db.execute(
        select(District)
        .where(District.division_id == division_id)
        .order_by(District.name_en)
    )
    return result.scalars().all()


@router.get("/districts/{district_id}/upazilas", response_model=list[UpazilaResponse])
async def list_upazilas(
    district_id: int,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all upazilas for a given district."""
    result = await db.execute(
        select(Upazila)
        .where(Upazila.district_id == district_id)
        .order_by(Upazila.name_en)
    )
    return result.scalars().all()
