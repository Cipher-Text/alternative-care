"""Patient-controlled sharing between clinics (ADR 009, Phase 4).

The patient, signed in recently, lets ONE clinic read named categories of ANOTHER clinic's records about
them, for 7, 30 or 90 days. Rules enforced here:

- Both clinics must already be linked to the patient's profile and visible in their portal; the share is
  between those two links, so the recipient already knows who the person is.
- Only categories the patient names are readable: issued prescriptions and diagnoses. Never doctors'
  private notes, examination notes, payments or appointments.
- Nothing is copied. The recipient reads the source clinic's rows live, one clinic at a time with row-level
  security bound to it, so revoking, expiry, or removing either clinic from the account stops access at once.
- Only a doctor at the recipient clinic can read shared records. Every read is logged and visible to the
  patient and to the source clinic.
- Granting needs a recent sign-in (a stolen session is not enough) and writes a consent record.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import tenant_context
from app.modules.identity.portal import PatientContext, PortalService
from app.modules.identity.service import SCRIPT_VERSION
from app.shared.models import (
    ConsentEvent,
    DataShare,
    DataShareAccess,
    PatientDiagnosis,
    PatientLink,
    PersonProfile,
    Prescription,
    Tenant,
    User,
)
from app.shared.schemas import (
    PatientSharing,
    PortalShare,
    ShareCreate,
    ShareSummary,
    SharedDiagnosis,
    SharedPrescription,
    SharedPrescriptionItem,
    SharedRecords,
)

SHARE_SCRIPT = "share-2026-10-v1"  # the wording the patient agreed to (shown in the portal)
RECORD_LIMIT = 100


def _refuse(code: str, message: str, http_status: int = status.HTTP_409_CONFLICT) -> HTTPException:
    return HTTPException(http_status, detail={"code": code, "message": message})


def effective_status(share: DataShare, source: PatientLink, recipient: PatientLink, now: datetime) -> str:
    if share.status == "revoked":
        return "revoked"
    if source.status != "linked" or recipient.status != "linked":
        return "ended"  # a clinic was removed from the account, so the share stopped with it
    if share.expires_at <= now:
        return "expired"
    return "active"


async def _access_stats(db: AsyncSession, share_ids: list[str]) -> dict[str, tuple[int, datetime | None]]:
    if not share_ids:
        return {}
    rows = await db.execute(
        select(DataShareAccess.share_id, func.count(), func.max(DataShareAccess.created_at))
        .where(DataShareAccess.share_id.in_(share_ids))
        .group_by(DataShareAccess.share_id)
    )
    return {sid: (count, last) for sid, count, last in rows.all()}


async def _clinic_names(db: AsyncSession, tenant_ids: set[str]) -> dict[str, str]:
    if not tenant_ids:
        return {}
    rows = await db.execute(select(Tenant).where(Tenant.id.in_(tenant_ids)))
    return {t.id: (t.clinic_name or t.name) for t in rows.scalars()}


class PortalSharingService:
    """Patient side."""

    def __init__(self, db: AsyncSession, patient: PatientContext):
        self.db = db
        self.patient = patient
        self.portal = PortalService(db, patient)

    async def create(self, data: ShareCreate) -> PortalShare:
        if not self.patient.recently_signed_in:
            raise _refuse(
                "recent_sign_in_required",
                "For your safety, sign in again with a new code before sharing your records.",
                status.HTTP_403_FORBIDDEN,
            )
        source, source_tenant, source_profile = await self.portal._link(data.source_link_id)
        recipient, recipient_tenant, recipient_profile = await self.portal._link(data.recipient_link_id)
        if source_profile.id != recipient_profile.id:
            raise _refuse("different_people", "Both clinics must hold records for the same person.", 422)
        if source.tenant_id == recipient.tenant_id:
            raise _refuse("same_clinic", "Choose two different clinics.", 422)

        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=data.days)
        consent = ConsentEvent(
            id=str(uuid4()), kind="share_grant", tenant_id=source.tenant_id, patient_id=source.patient_id,
            profile_id=source_profile.id, account_id=self.patient.account_id, method="portal", staff_user_id=None,
            script_version=SHARE_SCRIPT, staff_confirmed_told=False,
            note=f"Shared {', '.join(data.categories)} with {recipient_tenant.clinic_name or recipient_tenant.name} for {data.days} days"[:500],
        )
        self.db.add(consent)
        await self.db.flush()
        share = DataShare(
            id=str(uuid4()), account_id=self.patient.account_id, profile_id=source_profile.id,
            source_link_id=source.id, recipient_link_id=recipient.id, categories=list(data.categories),
            status="active", expires_at=expires, consent_event_id=consent.id,
        )
        self.db.add(share)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise _refuse(
                "share_exists", "These two clinics are already shared. Stop that share first to change it."
            ) from exc
        await self.db.refresh(share)
        return (await self._build([share]))[0]

    async def list_shares(self) -> list[PortalShare]:
        profiles = {p.id for p in await self.portal._visible_profiles()}
        if not profiles:
            return []
        shares = (
            await self.db.execute(
                select(DataShare)
                .where(DataShare.account_id == self.patient.account_id, DataShare.profile_id.in_(profiles))
                .order_by(DataShare.created_at.desc())
                .limit(50)
            )
        ).scalars().all()
        return await self._build(list(shares))

    async def _build(self, shares: list[DataShare]) -> list[PortalShare]:
        if not shares:
            return []
        link_ids = {s.source_link_id for s in shares} | {s.recipient_link_id for s in shares}
        links = {
            l.id: l for l in (await self.db.execute(select(PatientLink).where(PatientLink.id.in_(link_ids)))).scalars()
        }
        names = await _clinic_names(self.db, {l.tenant_id for l in links.values()})
        profile_names = {
            p.id: p.display_name
            for p in (
                await self.db.execute(select(PersonProfile).where(PersonProfile.id.in_({s.profile_id for s in shares})))
            ).scalars()
        }
        stats = await _access_stats(self.db, [s.id for s in shares])
        now = datetime.now(timezone.utc)
        out = []
        for s in shares:
            src, rcp = links[s.source_link_id], links[s.recipient_link_id]
            count, last = stats.get(s.id, (0, None))
            out.append(
                PortalShare(
                    id=s.id, profile_id=s.profile_id, profile_name=profile_names.get(s.profile_id, ""),
                    source_clinic=names.get(src.tenant_id, ""), recipient_clinic=names.get(rcp.tenant_id, ""),
                    categories=list(s.categories), status=effective_status(s, src, rcp, now),
                    created_at=s.created_at, expires_at=s.expires_at, revoked_at=s.revoked_at,
                    access_count=count, last_accessed_at=last,
                )
            )
        return out

    async def revoke(self, share_id: str) -> None:
        share = (
            await self.db.execute(
                select(DataShare).where(DataShare.id == share_id, DataShare.account_id == self.patient.account_id)
            )
        ).scalar_one_or_none()
        visible = {p.id for p in await self.portal._visible_profiles()}
        if share is None or share.profile_id not in visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
        if share.status == "revoked":
            raise _refuse("already_revoked", "This share was already stopped.")
        source = (await self.db.execute(select(PatientLink).where(PatientLink.id == share.source_link_id))).scalar_one()
        now = datetime.now(timezone.utc)
        share.status = "revoked"
        share.revoked_at = now
        self.db.add(
            ConsentEvent(
                id=str(uuid4()), kind="share_revoke", tenant_id=source.tenant_id, patient_id=source.patient_id,
                profile_id=share.profile_id, account_id=self.patient.account_id, method="portal", staff_user_id=None,
                script_version=SHARE_SCRIPT, staff_confirmed_told=False, note="Share stopped by the patient",
            )
        )
        await self.db.commit()


class ClinicSharingService:
    """Clinic side. `tenant_id` and `user_id` come from the signed-in staff member."""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _link(self, patient_id: str) -> PatientLink:
        link = (
            await self.db.execute(
                select(PatientLink).where(
                    PatientLink.tenant_id == self.tenant_id, PatientLink.patient_id == patient_id, PatientLink.status == "linked"
                )
            )
        ).scalar_one_or_none()
        if link is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "This patient has no verified link, so nothing is shared.")
        return link

    async def _summaries(self, link: PatientLink) -> tuple[list[ShareSummary], list[ShareSummary]]:
        shares = (
            await self.db.execute(
                select(DataShare)
                .where((DataShare.source_link_id == link.id) | (DataShare.recipient_link_id == link.id))
                .order_by(DataShare.created_at.desc())
                .limit(40)
            )
        ).scalars().all()
        link_ids = {s.source_link_id for s in shares} | {s.recipient_link_id for s in shares}
        links = {
            l.id: l for l in (await self.db.execute(select(PatientLink).where(PatientLink.id.in_(link_ids)))).scalars()
        } if link_ids else {}
        names = await _clinic_names(self.db, {l.tenant_id for l in links.values()})
        stats = await _access_stats(self.db, [s.id for s in shares])
        now = datetime.now(timezone.utc)
        incoming, outgoing = [], []
        for s in shares:
            src, rcp = links[s.source_link_id], links[s.recipient_link_id]
            count, last = stats.get(s.id, (0, None))
            summary = ShareSummary(
                share_id=s.id,
                clinic_name=names.get(src.tenant_id if s.recipient_link_id == link.id else rcp.tenant_id, ""),
                categories=list(s.categories), status=effective_status(s, src, rcp, now), expires_at=s.expires_at,
                access_count=count, last_accessed_at=last,
            )
            (incoming if s.recipient_link_id == link.id else outgoing).append(summary)
        return incoming, outgoing

    async def sharing(self, patient_id: str) -> PatientSharing:
        link = await self._link(patient_id)
        incoming, outgoing = await self._summaries(link)
        return PatientSharing(incoming=incoming, outgoing=outgoing)

    async def shared_records(self, patient_id: str) -> SharedRecords:
        link = await self._link(patient_id)
        now = datetime.now(timezone.utc)
        shares = (
            await self.db.execute(
                select(DataShare).where(
                    DataShare.recipient_link_id == link.id, DataShare.status == "active", DataShare.expires_at > now
                )
            )
        ).scalars().all()
        prescriptions: list[SharedPrescription] = []
        diagnoses: list[SharedDiagnosis] = []
        for share in shares:
            source = (await self.db.execute(select(PatientLink).where(PatientLink.id == share.source_link_id))).scalar_one()
            if source.status != "linked":
                continue  # the source clinic was removed from the patient's account: the share has ended
            tenant = (await self.db.execute(select(Tenant).where(Tenant.id == source.tenant_id))).scalar_one()
            clinic = tenant.clinic_name or tenant.name
            count = 0
            # Read the source clinic's rows live, with row-level security bound to THAT clinic, then restore ours
            async with tenant_context(self.db, source.tenant_id):
                if "prescriptions" in share.categories:
                    doctors = {
                        u.id: u.full_name
                        for u in (await self.db.execute(select(User).where(User.tenant_id == source.tenant_id))).scalars()
                    }
                    for rx in (
                        await self.db.execute(
                            select(Prescription)
                            .where(
                                Prescription.tenant_id == source.tenant_id,
                                Prescription.patient_id == source.patient_id,
                                Prescription.status == "issued",
                            )
                            .options(selectinload(Prescription.items))
                            .order_by(Prescription.created_at.desc())
                            .limit(RECORD_LIMIT)
                        )
                    ).scalars():
                        count += 1
                        prescriptions.append(
                            SharedPrescription(
                                source_clinic=clinic, shared_until=share.expires_at, date=rx.created_at.date(),
                                doctor_name=doctors.get(rx.prescribed_by), diagnosis=rx.diagnosis, advice=rx.advice,
                                items=[
                                    SharedPrescriptionItem(
                                        medicine=i.medicine_name or "", dosage=i.dosage, frequency=i.frequency,
                                        duration=i.duration, instructions=i.instructions,
                                    )
                                    for i in sorted(rx.items, key=lambda i: i.display_order)
                                ],
                            )
                        )
                if "diagnoses" in share.categories:
                    for d in (
                        await self.db.execute(
                            select(PatientDiagnosis)
                            .where(PatientDiagnosis.tenant_id == source.tenant_id, PatientDiagnosis.patient_id == source.patient_id)
                            .order_by(PatientDiagnosis.diagnosed_at.desc())
                            .limit(RECORD_LIMIT)
                        )
                    ).scalars():
                        count += 1
                        diagnoses.append(
                            SharedDiagnosis(
                                source_clinic=clinic, shared_until=share.expires_at, description=d.description,
                                icd_code=d.icd_code, diagnosed_at=d.diagnosed_at, is_active=d.is_active,
                            )
                        )
            self.db.add(
                DataShareAccess(
                    id=str(uuid4()), share_id=share.id, recipient_tenant_id=self.tenant_id,
                    staff_user_id=self.user_id, record_count=count,
                )
            )
        await self.db.commit()
        incoming, _ = await self._summaries(link)
        prescriptions.sort(key=lambda r: r.date, reverse=True)
        diagnoses.sort(key=lambda d: d.diagnosed_at, reverse=True)
        return SharedRecords(prescriptions=prescriptions, diagnoses=diagnoses, shares=incoming)
