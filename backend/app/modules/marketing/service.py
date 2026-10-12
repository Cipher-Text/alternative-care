"""Facebook profile promotion workflow.

requested -> drafted -> approved -> posted, with the doctor's approval of the exact text required
before staff can mark it posted (enforced here, not in the UI). A clinic may have one open request at
a time (also a database constraint) and a quarterly quota from its plan; cancelled and rejected
requests give the quota back.
"""

import html
from uuid import uuid4
from datetime import datetime, timezone

import structlog
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.entitlements import EntitlementService
from app.modules.directory.service import eligibility
from app.shared.models import FacebookFeatureRequest, PractitionerListing, Tenant, User
from app.shared.models.marketing import FB_OPEN
from app.shared.schemas import (
    AdminFacebookRequest,
    FacebookRequestResponse,
    FacebookSummary,
)

logger = structlog.get_logger()
KEY = "quarterly_facebook_features"


def quarter_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now(timezone.utc)
    start = datetime(now.year, 3 * ((now.month - 1) // 3) + 1, 1, tzinfo=timezone.utc)
    return start, start + relativedelta(months=3)


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, "message": message})


def _email(recipient: str | None, subject: str, lines: list[str], link: str) -> None:
    """Best-effort system email; the workflow never depends on it."""
    if not recipient:
        return
    try:
        from app.core.system_email import send_system_email_task

        send_system_email_task.delay(
            recipient=recipient,
            subject=subject,
            body_text="\n".join(lines) + f"\n\n{link}",
            body_html="".join(f"<p>{html.escape(x)}</p>" for x in lines)
            + f'<p><a href="{html.escape(link)}">{html.escape(link)}</a></p>',
        )
    except Exception:  # noqa: BLE001
        logger.warning("facebook_email_failed", subject=subject)


class FacebookService:
    """Doctor side: one clinic's own requests."""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _tenant(self) -> Tenant:
        return (await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))).scalar_one()

    async def _listing(self) -> PractitionerListing | None:
        return (
            await self.db.execute(
                select(PractitionerListing).where(PractitionerListing.tenant_id == self.tenant_id)
            )
        ).scalar_one_or_none()

    async def _get(self, request_id: str) -> FacebookFeatureRequest:
        req = (
            await self.db.execute(
                select(FacebookFeatureRequest).where(
                    FacebookFeatureRequest.id == request_id,
                    FacebookFeatureRequest.tenant_id == self.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if req is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
        return req

    async def summary(self) -> FacebookSummary:
        tenant = await self._tenant()
        listing = await self._listing()
        _, _, effective = await EntitlementService(self.db).resolve(self.tenant_id)
        item = effective[KEY]
        start, end = quarter_bounds()
        used = await EntitlementService(self.db).used(self.tenant_id, KEY)
        limit = item.limit
        remaining = None if limit is None else max(0, limit - used)

        history = (
            await self.db.execute(
                select(FacebookFeatureRequest)
                .where(FacebookFeatureRequest.tenant_id == self.tenant_id)
                .order_by(FacebookFeatureRequest.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        open_request = next((r for r in history if r.status in FB_OPEN), None)

        profile_public = bool(listing and (await eligibility(self.db, tenant, listing)).public)
        blockers = []
        if not item.enabled:
            blockers.append("not_in_plan")
        if not profile_public:
            blockers.append("no_public_profile")
        if item.enabled and remaining == 0:
            blockers.append("quota_used")
        if open_request is not None:
            blockers.append("open_request")
        return FacebookSummary(
            in_plan=item.enabled,
            limit=limit if item.enabled else 0,
            used=used,
            remaining=remaining if item.enabled else 0,
            period_start=start,
            period_end=end,
            blockers=blockers,
            can_request=not blockers,
            profile_path=f"/practitioners/{listing.slug}" if profile_public and listing else None,
            open_request=FacebookRequestResponse.model_validate(open_request) if open_request else None,
            history=[FacebookRequestResponse.model_validate(r) for r in history],
        )

    async def create(self, note: str | None) -> FacebookFeatureRequest:
        # Plan and quota first: these raise the same structured 403 as every other limit
        await EntitlementService(self.db).check_limit(self.tenant_id, KEY)
        tenant = await self._tenant()
        listing = await self._listing()
        if listing is None or not (await eligibility(self.db, tenant, listing)).public:
            raise _conflict(
                "no_public_profile",
                "Your public profile must be live before it can be featured. Finish it under Directory.",
            )
        req = FacebookFeatureRequest(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            listing_id=listing.id,
            requested_by=self.user_id,
            doctor_note=(note or "").strip() or None,
            status="requested",
            created_by=self.user_id,
        )
        self.db.add(req)
        try:
            await self.db.commit()
        except IntegrityError as exc:  # the one-open-request-per-clinic constraint
            await self.db.rollback()
            raise _conflict("request_in_progress", "You already have a request in progress.") from exc
        await self.db.refresh(req)

        admins = (
            await self.db.execute(select(User.email).where(User.role == "admin", User.is_active.is_(True)))
        ).scalars().all()
        for address in admins:
            _email(
                address,
                f"Facebook feature requested: {tenant.clinic_name or tenant.name}",
                [f"{tenant.clinic_name or tenant.name} asked to be featured on the AltCare Facebook page."],
                f"{settings.FRONTEND_URL}/admin/marketing",
            )
        return req

    async def cancel(self, request_id: str) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        if req.status not in ("requested", "drafted"):
            raise _conflict("not_cancellable", "This request can no longer be cancelled.")
        req.status = "cancelled"
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def approve(self, request_id: str, comment: str | None) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        if req.status != "drafted" or not req.draft_text:
            raise _conflict("nothing_to_approve", "There is no draft waiting for your approval.")
        req.status = "approved"
        req.approved_text = req.draft_text  # freeze exactly what was approved
        req.approved_at = datetime.now(timezone.utc)
        req.approved_by = self.user_id
        if comment:
            req.doctor_comment = comment
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def request_changes(self, request_id: str, comment: str) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        if req.status != "drafted":
            raise _conflict("nothing_to_change", "There is no draft to comment on.")
        req.status = "requested"  # back to staff, with the doctor's comment
        req.doctor_comment = comment
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)
        return req


class AdminFacebookService:
    """Staff side: the queue, drafting, rejecting, and marking posted."""

    def __init__(self, db: AsyncSession, admin_id: str):
        self.db = db
        self.admin_id = admin_id

    async def _get(self, request_id: str) -> FacebookFeatureRequest:
        req = (
            await self.db.execute(
                select(FacebookFeatureRequest).where(FacebookFeatureRequest.id == request_id)
            )
        ).scalar_one_or_none()
        if req is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
        return req

    async def list(self, status_filter: str | None, limit: int, offset: int) -> list[AdminFacebookRequest]:
        q = (
            select(FacebookFeatureRequest, Tenant, User.full_name, PractitionerListing)
            .join(Tenant, Tenant.id == FacebookFeatureRequest.tenant_id)
            .join(User, User.id == FacebookFeatureRequest.requested_by)
            .outerjoin(PractitionerListing, PractitionerListing.id == FacebookFeatureRequest.listing_id)
        )
        if status_filter:
            q = q.where(FacebookFeatureRequest.status == status_filter)
        rows = (
            await self.db.execute(q.order_by(FacebookFeatureRequest.created_at.desc()).limit(limit).offset(offset))
        ).all()
        out = []
        for req, tenant, requester, listing in rows:
            public = bool(listing and (await eligibility(self.db, tenant, listing)).public)
            out.append(
                AdminFacebookRequest(
                    **FacebookRequestResponse.model_validate(req).model_dump(),
                    tenant_id=tenant.id,
                    tenant_name=tenant.clinic_name or tenant.name,
                    requester_name=requester,
                    profile_path=f"/practitioners/{listing.slug}" if public and listing else None,
                )
            )
        return out

    async def _clinic(self, req: FacebookFeatureRequest) -> Tenant:
        return (await self.db.execute(select(Tenant).where(Tenant.id == req.tenant_id))).scalar_one()

    async def draft(self, request_id: str, text: str) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        if req.status not in ("requested", "drafted"):
            raise _conflict("not_draftable", "Only a request waiting for a draft can be drafted.")
        req.draft_text = text.strip()
        req.drafted_by = self.admin_id
        req.drafted_at = datetime.now(timezone.utc)
        req.status = "drafted"
        req.updated_by = self.admin_id
        await self.db.commit()
        await self.db.refresh(req)
        tenant = await self._clinic(req)
        _email(
            tenant.clinic_email or tenant.email,
            "Your AltCare Facebook post is ready for your approval",
            ["We drafted your Facebook post. Nothing is published until you approve it."],
            f"{settings.FRONTEND_URL}/marketing",
        )
        return req

    async def reject(self, request_id: str, reason: str) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        if req.status not in FB_OPEN:
            raise _conflict("not_rejectable", "This request is already closed.")
        req.status = "rejected"
        req.reject_reason = reason
        req.updated_by = self.admin_id
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def mark_posted(self, request_id: str, post_url: str) -> FacebookFeatureRequest:
        req = await self._get(request_id)
        # The consent rule: nothing is posted until the doctor approved the exact text
        if req.status != "approved" or not req.approved_text or not req.approved_at:
            raise _conflict("not_approved", "The doctor has not approved this post yet.")
        req.status = "posted"
        req.post_url = post_url
        req.posted_at = datetime.now(timezone.utc)
        req.posted_by = self.admin_id
        req.updated_by = self.admin_id
        await self.db.commit()
        await self.db.refresh(req)
        tenant = await self._clinic(req)
        _email(
            tenant.clinic_email or tenant.email,
            "Your profile was featured on the AltCare Facebook page",
            ["Your approved post is live on the AltCare Facebook page."],
            post_url,
        )
        return req
