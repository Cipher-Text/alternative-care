"""Public API endpoints (D4) — unauthenticated, read-only.

No route here takes a `CurrentUser` dependency; that's the whole point of this router boundary.
It serves the admin-curated institutions directory and aggregate site statistics. The medicine and
symptom catalogs are intentionally not served here (gated behind signup — see `get_public_stats`).
Institutions have no tenant scoping at all (they aren't tenants), so `InstitutionService` is
exposed as a straight passthrough.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.institution.service import InstitutionService
from app.shared.models import Institution, Medicine, Symptom, Tenant, User
from app.modules.content.service import PublicContentService
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.modules.directory.service import PublicDirectoryService
from app.shared.schemas import (
    ContactMessageCreate,
    ContactRequestCreate,
    InstitutionListItem,
    ListingEventCreate,
    PublicArticle,
    PublicArticleItem,
    PublicPractitioner,
    PublicPractitionerList,
)

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


# ===== Published articles and videos =====
#
# Only content an admin has reviewed and published (see app/modules/content). Drafts and
# in-review items are never exposed.


@router.get("/articles", response_model=list[PublicArticleItem])
async def list_public_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    kind: str | None = Query(None, pattern="^(article|video)$"),
    discipline: str | None = Query(None, pattern="^(general|homeopathy|ayurveda|unani|herbal)$"),
    limit: int = Query(12, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await PublicContentService(db).list_items(kind, discipline, limit, offset)


@router.get("/articles/{slug}", response_model=PublicArticle)
async def get_public_article(
    slug: str, db: Annotated[AsyncSession, Depends(get_db)], response: Response
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await PublicContentService(db).get(slug)


# ===== Practitioner directory =====
#
# Only listings that pass every gate (opted in, admin-verified, approved, in plan, has a bio).
# The list reports `launched` (>= DIRECTORY_MIN_PROFILES visible profiles, ADR-008); until then the
# site shows a teaser instead of a thin directory.


@router.get("/practitioners", response_model=PublicPractitionerList)
async def list_public_practitioners(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    discipline: str | None = Query(None, pattern="^(homeopathy|ayurveda|unani|herbal)$"),
    district_id: int | None = Query(None, ge=1),
    q: str | None = Query(None, max_length=80),
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    response.headers["Cache-Control"] = "public, max-age=300"
    launched, total, items = await PublicDirectoryService(db).search(discipline, district_id, q, limit, offset)
    return PublicPractitionerList(launched=launched, total=total, items=items)


@router.get("/practitioners/slugs", response_model=list[str])
async def list_public_practitioner_slugs(db: Annotated[AsyncSession, Depends(get_db)], response: Response):
    """For the sitemap. Empty until the directory has launched."""
    response.headers["Cache-Control"] = "public, max-age=300"
    svc = PublicDirectoryService(db)
    slugs = await svc.slugs()
    return slugs if len(slugs) >= settings.DIRECTORY_MIN_PROFILES else []


@router.get("/practitioners/{slug}", response_model=PublicPractitioner)
async def get_public_practitioner(
    slug: str, db: Annotated[AsyncSession, Depends(get_db)], response: Response
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await PublicDirectoryService(db).get(slug)


async def _limit(request: Request, scope: str, limit: int, window: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    result = await enforce_rate_limit(request, scope, limit, window)
    if not result.allowed:
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(result.retry_after)})


@router.post("/practitioners/{slug}/requests", status_code=201)
async def create_contact_request(
    slug: str,
    data: ContactRequestCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """A patient asks the clinic to call back. Not a booking. Consent is mandatory."""
    await _limit(request, "directory_request", settings.RATE_LIMIT_CONTACT_REQUEST_PER_HOUR, 3600)
    await PublicDirectoryService(db).create_request(slug, data)
    return {"ok": True}


@router.post("/practitioners/{slug}/events", status_code=204)
async def record_listing_event(
    slug: str,
    data: ListingEventCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Counts a tap on call / WhatsApp so the doctor can see what the listing earns. No personal data."""
    await _limit(request, "directory_event", 60, 3600)
    await PublicDirectoryService(db).record_event(slug, data.event_type)
    return Response(status_code=204)


# ===== Contact form =====


@router.post("/contact", status_code=201)
async def send_contact_message(
    data: ContactMessageCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """General questions, Enterprise enquiries, billing help, or a report about a profile.
    Consent is mandatory; a hidden honeypot field and an IP rate limit keep bots out."""
    from app.modules.contact.service import ContactService

    await _limit(request, "contact_message", settings.RATE_LIMIT_CONTACT_MESSAGE_PER_HOUR, 3600)
    await ContactService(db).create(data)
    return {"ok": True}
