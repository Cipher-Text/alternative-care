"""Practitioner directory: opt-in listing, free admin verification, plan gate, contact requests.

A listing is public only when ALL hold: the doctor opted in, an admin verified the tenant's
credentials (free, and the trust signal), the tenant is approved and active, the plan includes
`feature_directory_listing`, and the listing has a bio. Verification and the plan are separate
gates on purpose: paying never substitutes for being verified.
"""

import html
import re
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import EntitlementService
from app.shared.models import (
    ContactRequest,
    District,
    Division,
    DoctorDegree,
    ListingEvent,
    PractitionerListing,
    Tenant,
    Upazila,
    User,
)
from app.shared.schemas import (
    DirectoryStats,
    Eligibility,
    ListingResponse,
    ListingUpdate,
    PublicDegree,
    PublicPractitioner,
    PublicPractitionerItem,
)

FEATURE_KEY = "feature_directory_listing"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _bdt(paisa: int | None) -> int | None:
    return None if paisa is None else paisa // 100


def _has_text(listing: PractitionerListing | None) -> bool:
    return bool(listing and ((listing.bio_en or "").strip() or (listing.bio_bn or "").strip()))


async def _in_plan(db: AsyncSession, tenant_id: str) -> bool:
    _, _, effective = await EntitlementService(db).resolve(tenant_id)
    entry = effective.get(FEATURE_KEY)
    return bool(entry and entry.enabled)


async def eligibility(db: AsyncSession, tenant: Tenant, listing: PractitionerListing | None) -> Eligibility:
    is_listed = bool(listing and listing.is_listed)
    verified = bool(tenant.is_verified)
    approved = bool(tenant.is_approved and tenant.is_active)
    in_plan = await _in_plan(db, tenant.id)
    has_text = _has_text(listing)
    blockers = []
    if not is_listed:
        blockers.append("not_listed")
    if not verified:
        blockers.append("not_verified")
    if not approved:
        blockers.append("not_approved")
    if not in_plan:
        blockers.append("not_in_plan")
    if not has_text:
        blockers.append("no_profile_text")
    return Eligibility(
        is_listed=is_listed,
        verified=verified,
        approved=approved,
        in_plan=in_plan,
        has_profile_text=has_text,
        public=not blockers,
        blockers=blockers,
    )


class DirectoryService:
    """Doctor-facing: manage the tenant's own listing and its contact requests."""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _tenant(self) -> Tenant:
        t = (await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))).scalar_one()
        return t

    async def _listing(self) -> PractitionerListing | None:
        return (
            await self.db.execute(
                select(PractitionerListing).where(PractitionerListing.tenant_id == self.tenant_id)
            )
        ).scalar_one_or_none()

    async def _unique_slug(self, base: str) -> str:
        base = _slugify(base) or f"doctor-{secrets.token_hex(3)}"
        slug, n = base, 1
        while (
            await self.db.execute(select(PractitionerListing.id).where(PractitionerListing.slug == slug))
        ).first():
            n += 1
            slug = f"{base}-{n}"
        return slug

    async def get_listing(self) -> ListingResponse:
        tenant = await self._tenant()
        listing = await self._listing()
        elig = await eligibility(self.db, tenant, listing)
        if listing is None:
            return ListingResponse(exists=False, eligibility=elig)
        out = ListingResponse.model_validate(listing)
        out.eligibility = elig
        return out

    async def upsert_listing(self, data: ListingUpdate) -> ListingResponse:
        tenant = await self._tenant()
        listing = await self._listing()
        changes = data.model_dump(exclude_unset=True)
        if listing is None:
            user = (await self.db.execute(select(User).where(User.id == self.user_id))).scalar_one()
            listing = PractitionerListing(
                id=str(uuid4()),
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                slug=await self._unique_slug(user.full_name),
                created_by=self.user_id,
            )
            self.db.add(listing)
        for key, value in changes.items():
            if value is not None or key in ("headline_en", "headline_bn", "bio_en", "bio_bn", "consultation_hours"):
                setattr(listing, key, value)
        if changes.get("is_listed") and listing.listed_at is None:
            listing.listed_at = datetime.now(timezone.utc)
        listing.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(listing)
        out = ListingResponse.model_validate(listing)
        out.eligibility = await eligibility(self.db, tenant, listing)
        return out

    async def stats(self) -> DirectoryStats:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        listing = await self._listing()
        calls = whatsapp = 0
        if listing:
            rows = await self.db.execute(
                select(ListingEvent.event_type, func.count())
                .where(ListingEvent.listing_id == listing.id, ListingEvent.created_at >= start)
                .group_by(ListingEvent.event_type)
            )
            counts = dict(rows.all())
            calls, whatsapp = counts.get("call", 0), counts.get("whatsapp", 0)
        requests = (
            await self.db.execute(
                select(func.count())
                .select_from(ContactRequest)
                .where(ContactRequest.tenant_id == self.tenant_id, ContactRequest.created_at >= start)
            )
        ).scalar_one()
        open_requests = (
            await self.db.execute(
                select(func.count())
                .select_from(ContactRequest)
                .where(ContactRequest.tenant_id == self.tenant_id, ContactRequest.status == "new")
            )
        ).scalar_one()
        return DirectoryStats(
            month=start.strftime("%Y-%m"),
            requests=requests,
            calls=calls,
            whatsapp=whatsapp,
            open_requests=open_requests,
        )

    async def list_requests(self, status_filter: str | None, limit: int, offset: int):
        q = select(ContactRequest).where(ContactRequest.tenant_id == self.tenant_id)
        if status_filter:
            q = q.where(ContactRequest.status == status_filter)
        q = q.order_by(ContactRequest.created_at.desc()).limit(limit).offset(offset)
        return (await self.db.execute(q)).scalars().all()

    async def update_request(self, request_id: str, new_status: str) -> ContactRequest:
        req = (
            await self.db.execute(
                select(ContactRequest).where(
                    ContactRequest.id == request_id, ContactRequest.tenant_id == self.tenant_id
                )
            )
        ).scalar_one_or_none()
        if req is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
        req.status = new_status
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)
        return req


class PublicDirectoryService:
    """Unauthenticated, read-mostly view of listings that pass every gate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _base(self):
        return (
            select(PractitionerListing, Tenant)
            .join(Tenant, Tenant.id == PractitionerListing.tenant_id)
            .where(
                PractitionerListing.is_listed.is_(True),
                Tenant.is_verified.is_(True),
                Tenant.is_approved.is_(True),
                Tenant.is_active.is_(True),
                or_(
                    func.length(func.trim(func.coalesce(PractitionerListing.bio_en, ""))) > 0,
                    func.length(func.trim(func.coalesce(PractitionerListing.bio_bn, ""))) > 0,
                ),
            )
        )

    async def _visible(self, rows) -> list[tuple[PractitionerListing, Tenant]]:
        """SQL narrows the candidates; the plan gate (plan + overrides + expiry) is resolved per tenant."""
        out = []
        for listing, tenant in rows:
            if await _in_plan(self.db, tenant.id):
                out.append((listing, tenant))
        return out

    async def _names(self, tenants: list[Tenant]):
        d_ids = {t.district_id for t in tenants if t.district_id}
        u_ids = {t.upazila_id for t in tenants if t.upazila_id}
        v_ids = {t.division_id for t in tenants if t.division_id}
        districts = (
            {d.id: d for d in (await self.db.execute(select(District).where(District.id.in_(d_ids)))).scalars()}
            if d_ids
            else {}
        )
        upazilas = (
            {u.id: u for u in (await self.db.execute(select(Upazila).where(Upazila.id.in_(u_ids)))).scalars()}
            if u_ids
            else {}
        )
        divisions = (
            {v.id: v for v in (await self.db.execute(select(Division).where(Division.id.in_(v_ids)))).scalars()}
            if v_ids
            else {}
        )
        return districts, upazilas, divisions

    async def _users(self, listings: list[PractitionerListing]) -> dict[str, User]:
        ids = {listing.user_id for listing in listings}
        if not ids:
            return {}
        rows = (await self.db.execute(select(User).where(User.id.in_(ids)))).scalars()
        return {u.id: u for u in rows}

    def _item_fields(self, listing, tenant, user, districts):
        d = districts.get(tenant.district_id)
        return dict(
            slug=listing.slug,
            display_name=user.full_name if user else (tenant.name or ""),
            clinic_name=tenant.clinic_name,
            headline_en=listing.headline_en,
            headline_bn=listing.headline_bn,
            disciplines=list(tenant.specializations or []),
            registration_body=tenant.registration_body,
            years_of_experience=tenant.years_of_experience,
            district_en=d.name_en if d else None,
            district_bn=d.name_bn if d else None,
            languages=list(listing.languages or []),
            availability=listing.availability,
            fee_bdt=_bdt(tenant.consultation_fee) if listing.show_fee else None,
            verified_at=tenant.verified_at,
            logo_url=tenant.logo_url,
        )

    async def search(
        self,
        discipline: str | None,
        district_id: int | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[PublicPractitionerItem]]:
        query = self._base()
        if discipline:
            query = query.where(Tenant.specializations.any(discipline))
        if district_id:
            query = query.where(Tenant.district_id == district_id)
        if q:
            like = f"%{q.strip()}%"
            query = query.join(User, User.id == PractitionerListing.user_id).where(
                or_(User.full_name.ilike(like), Tenant.clinic_name.ilike(like))
            )
        query = query.order_by(Tenant.verified_at.desc().nulls_last(), PractitionerListing.id)
        visible = await self._visible((await self.db.execute(query)).all())
        page = visible[offset : offset + limit]
        districts, _, _ = await self._names([t for _, t in page])
        users = await self._users([listing for listing, _ in page])
        items = [
            PublicPractitionerItem(**self._item_fields(lst, t, users.get(lst.user_id), districts))
            for lst, t in page
        ]
        return len(visible), items

    async def _find(self, slug: str) -> tuple[PractitionerListing, Tenant]:
        row = (await self.db.execute(self._base().where(PractitionerListing.slug == slug))).first()
        if row is None or not await _in_plan(self.db, row[1].id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Practitioner not found")
        return row[0], row[1]

    async def get(self, slug: str) -> PublicPractitioner:
        listing, tenant = await self._find(slug)
        districts, upazilas, divisions = await self._names([tenant])
        users = await self._users([listing])
        degrees = (
            await self.db.execute(
                select(DoctorDegree)
                .where(DoctorDegree.tenant_id == tenant.id, DoctorDegree.user_id == listing.user_id)
                .order_by(DoctorDegree.display_order, DoctorDegree.completion_year.desc())
            )
        ).scalars().all()
        up, dv = upazilas.get(tenant.upazila_id), divisions.get(tenant.division_id)
        return PublicPractitioner(
            **self._item_fields(listing, tenant, users.get(listing.user_id), districts),
            bio_en=listing.bio_en,
            bio_bn=listing.bio_bn,
            consultation_hours=listing.consultation_hours,
            follow_up_fee_bdt=_bdt(tenant.follow_up_fee) if listing.show_fee else None,
            address_line_1=tenant.address_line_1,
            address_line_2=tenant.address_line_2,
            landmark=tenant.landmark,
            upazila_en=up.name_en if up else None,
            upazila_bn=up.name_bn if up else None,
            division_en=dv.name_en if dv else None,
            division_bn=dv.name_bn if dv else None,
            latitude=tenant.latitude,
            longitude=tenant.longitude,
            phone=tenant.clinic_phone if listing.show_phone else None,
            whatsapp=tenant.clinic_whatsapp if listing.show_whatsapp else None,
            accepts_requests=listing.accepts_requests,
            degrees=[
                PublicDegree(
                    degree_name=d.degree_name,
                    institution_name=d.institution_name,
                    completion_year=d.completion_year,
                    is_verified=d.is_verified,
                )
                for d in degrees
            ],
        )

    async def slugs(self) -> list[str]:
        rows = await self._visible((await self.db.execute(self._base())).all())
        return [listing.slug for listing, _ in rows]

    async def record_event(self, slug: str, event_type: str) -> None:
        listing, _ = await self._find(slug)
        self.db.add(ListingEvent(id=str(uuid4()), listing_id=listing.id, event_type=event_type))
        await self.db.commit()

    async def create_request(self, slug: str, data) -> None:
        listing, tenant = await self._find(slug)
        if not listing.accepts_requests:
            raise HTTPException(status.HTTP_409_CONFLICT, "This practitioner is not taking requests online")
        if data.website:  # honeypot tripped: pretend success, store nothing
            return
        self.db.add(
            ContactRequest(
                id=str(uuid4()),
                tenant_id=tenant.id,
                listing_id=listing.id,
                patient_name=data.patient_name,
                patient_phone=data.patient_phone,
                message=data.message,
                preferred_time=data.preferred_time,
                consented_at=datetime.now(timezone.utc),
            )
        )
        await self.db.commit()
        await self._notify_clinic(tenant, listing, data)

    async def _notify_clinic(self, tenant: Tenant, listing: PractitionerListing, data) -> None:
        """Best-effort email to the clinic; the request is already saved, so a mail failure is not fatal."""
        recipient = tenant.clinic_email or tenant.email
        if not recipient:
            return
        e = html.escape
        try:
            from app.core.system_email import send_system_email_task

            send_system_email_task.delay(
                recipient=recipient,
                subject="New appointment request via AltCare",
                body_html=(
                    "<p>A patient asked to be contacted about an appointment.</p>"
                    f"<p><b>Name:</b> {e(data.patient_name)}<br><b>Phone:</b> {e(data.patient_phone)}<br>"
                    f"<b>Preferred time:</b> {e(data.preferred_time or '-')}<br>"
                    f"<b>Message:</b> {e(data.message or '-')}</p>"
                    f"<p>Open AltCare to mark it contacted: {settings.FRONTEND_URL}/directory</p>"
                ),
                body_text=(
                    f"A patient asked to be contacted.\nName: {data.patient_name}\n"
                    f"Phone: {data.patient_phone}\nPreferred time: {data.preferred_time or '-'}\n"
                    f"Message: {data.message or '-'}\n{settings.FRONTEND_URL}/directory"
                ),
            )
        except Exception:  # noqa: BLE001 — broker down must not lose or fail the request
            import structlog

            structlog.get_logger().warning("directory_request_email_failed", tenant_id=tenant.id)


async def set_verification(
    db: AsyncSession, tenant_id: str, admin_id: str, verified: bool, note: str | None
) -> Tenant:
    """Admin checks a tenant's registration/credentials. Free; required to appear publicly."""
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    tenant.is_verified = verified
    tenant.verified_at = datetime.now(timezone.utc) if verified else None
    tenant.verified_by = admin_id if verified else None
    tenant.verification_note = note
    await db.commit()
    await db.refresh(tenant)
    return tenant
