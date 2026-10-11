"""Public API endpoints (D4) — unauthenticated, read-only.

No route here takes a `CurrentUser` dependency; that's the whole point of this router boundary.
It serves the admin-curated institutions directory and aggregate site statistics. The medicine and
symptom catalogs are intentionally not served here (gated behind signup — see `get_public_stats`).
Institutions have no tenant scoping at all (they aren't tenants), so `InstitutionService` is
exposed as a straight passthrough.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.institution.service import InstitutionService
from app.shared.models import Institution, Medicine, Symptom, Tenant, User
from app.shared.schemas import InstitutionListItem

router = APIRouter()


class PublicStats(BaseModel):
    medicines: int
    symptoms: int
    institutions: int
    clinics: int
    practitioners: int


def get_public_institution_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstitutionService:
    """Institutions have no tenant scoping at all — every row is already public data."""
    return InstitutionService(db=db)


InstitutionServiceDep = Annotated[InstitutionService, Depends(get_public_institution_service)]


# ===== Site statistics =====
#
# The medicine and symptom catalogs are deliberately NOT browsable here: they are the product's
# gated value (signup unlocks them) and publishing them wholesale invites scraping and
# self-medication. The public site shows only how big they are.
# See docs/planning/public-site-strategy-2026-10.md.


@router.get("/stats", response_model=PublicStats)
async def get_public_stats(
    db: Annotated[AsyncSession, Depends(get_db)], response: Response
) -> PublicStats:
    """Headline counts for the marketing site. Aggregates only; no catalog content."""

    async def count(query) -> int:
        return (await db.execute(query)).scalar() or 0

    live_clinic = (Tenant.is_active.is_(True)) & (Tenant.is_approved.is_(True))
    stats = PublicStats(
        medicines=await count(
            select(func.count(Medicine.id)).where(
                Medicine.is_global.is_(True), Medicine.is_active.is_(True)
            )
        ),
        symptoms=await count(
            select(func.count(Symptom.id)).where(
                Symptom.is_global.is_(True), Symptom.is_active.is_(True)
            )
        ),
        institutions=await count(
            select(func.count(Institution.id)).where(Institution.is_active.is_(True))
        ),
        clinics=await count(select(func.count(Tenant.id)).where(live_clinic)),
        practitioners=await count(
            select(func.count(User.id))
            .join(Tenant, User.tenant_id == Tenant.id)
            .where(User.role == "doctor", User.is_active.is_(True), live_clinic)
        ),
    )
    response.headers["Cache-Control"] = "public, max-age=300"
    return stats


# ===== Institutions =====
#
# Every row is already admin-curated/global (no tenant scoping exists for
# institutions at all), so this is a straight passthrough onto
# InstitutionService — no visibility narrowing needed, unlike
# medicines/symptoms above.


@router.get("/institutions", response_model=list[InstitutionListItem])
async def list_public_institutions(
    service: InstitutionServiceDep,
    discipline: str | None = Query(None, description="Filter by discipline"),
    institution_type: str | None = Query(None, description="Filter by government/private"),
    district_id: int | None = Query(None, description="Filter by district"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Browse the admin-curated directory of alternative-medicine institutions."""
    return await service.list_institutions(
        discipline=discipline,
        institution_type=institution_type,
        district_id=district_id,
        is_active=True,
        limit=limit,
        offset=offset,
    )


@router.get("/institutions/{institution_id:int}", response_model=InstitutionListItem)
async def get_public_institution(institution_id: int, service: InstitutionServiceDep):
    """Get an institution's public detail."""
    return await service.get_institution(institution_id)
