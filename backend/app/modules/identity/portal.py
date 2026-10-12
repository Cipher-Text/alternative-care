"""Patient portal (ADR 009, Phase 2): sign-in with a phone code, and a read-only view of the holder's
own linked records across clinics.

Rules enforced here:
- A portal session is its own context (a `patient` token, no tenant, no clinic role). It reaches a
  clinic's data only through a link row, and only the linked patient's own rows.
- A holder sees their own profile and their dependents (children), never another adult's profile.
- A link made before this phone first signed in stays hidden until a clinic code activates it, so a
  recycled number cannot read an earlier owner's history.
- Read-only: no doctor's notes, no examination notes, no unissued drafts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import bind_tenant, get_db
from app.core.dependencies import security
from app.core.phone import mask_phone
from app.core.security import create_patient_token, decode_token
from app.modules.identity.otp import OtpService, hash_secret
from app.modules.identity.service import (
    SCRIPT_VERSION,
    age_years,
    get_or_create_account,
    normalize_claim_code,
)
from app.shared.models import (
    Appointment,
    ClaimCode,
    ConsentEvent,
    Invoice,
    Patient,
    PatientLink,
    Payment,
    PersonAccount,
    PersonProfile,
    Prescription,
    Tenant,
    User,
)
from app.shared.schemas import (
    PortalAppointment,
    PortalClinic,
    PortalMe,
    PortalPrescription,
    PortalPrescriptionItem,
    PortalProfile,
    PortalReceipt,
    PortalRecords,
    PortalToken,
)

RECORD_LIMIT = 50


@dataclass
class PatientContext:
    account_id: str
    phone: str


async def get_current_patient(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientContext:
    """Accepts only a patient-portal token; a staff token is refused, and so is the reverse."""
    unauthorised = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise unauthorised from exc
    if payload.get("type") != "patient" or not payload.get("sub"):
        raise unauthorised
    account = (await db.execute(select(PersonAccount).where(PersonAccount.id == payload["sub"]))).scalar_one_or_none()
    if account is None or account.status != "active":
        raise unauthorised
    await bind_tenant(db, None)  # no clinic is bound; each clinic is bound explicitly, one at a time
    return PatientContext(account_id=account.id, phone=account.phone)


class PortalAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def request(self, phone: str):
        """Send a sign-in code. Answers the same whether or not the phone has an account."""
        return await OtpService(self.db).issue(phone=phone, purpose="portal_login", tenant_id=None, requested_by=None)

    async def verify(self, challenge_id: str, code: str) -> PortalToken:
        challenge = await OtpService(self.db).confirm(
            challenge_id, code, purpose="portal_login", tenant_id=None, requested_by=None
        )
        account = await get_or_create_account(self.db, challenge.phone)
        if account.status != "active":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not available.")
        if account.portal_registered_at is None:
            account.portal_registered_at = datetime.now(timezone.utc)
        await self.db.commit()
        expires = datetime.now(timezone.utc) + timedelta(hours=settings.PATIENT_TOKEN_HOURS)
        return PortalToken(access_token=create_patient_token(account.id), expires_at=expires)


class PortalService:
    def __init__(self, db: AsyncSession, patient: PatientContext):
        self.db = db
        self.account_id = patient.account_id
        self.phone = patient.phone

    # ----- who can be seen ------------------------------------------------------------------

    async def _visible_profiles(self) -> list[PersonProfile]:
        """The holder's own profile and their dependents. Another adult under the same phone is hidden."""
        rows = (
            await self.db.execute(
                select(PersonProfile)
                .where(PersonProfile.account_id == self.account_id, PersonProfile.status == "active")
                .order_by(PersonProfile.created_at)
            )
        ).scalars().all()
        return [p for p in rows if p.relationship == "self" or p.is_dependent]

    async def _profile(self, profile_id: str) -> PersonProfile:
        for p in await self._visible_profiles():
            if p.id == profile_id:
                return p
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")

    async def _links(self, profile_ids: list[str]) -> list[tuple[PatientLink, Tenant]]:
        """Active links the holder may see in the portal (portal access granted)."""
        if not profile_ids:
            return []
        rows = await self.db.execute(
            select(PatientLink, Tenant)
            .join(Tenant, Tenant.id == PatientLink.tenant_id)
            .where(
                PatientLink.profile_id.in_(profile_ids),
                PatientLink.status == "linked",
                PatientLink.portal_access_at.is_not(None),
            )
            .order_by(PatientLink.linked_at)
        )
        return [(link, tenant) for link, tenant in rows.all()]

    async def _link(self, link_id: str) -> tuple[PatientLink, Tenant, PersonProfile]:
        """One portal-visible link that belongs to this holder, or 404 (nothing else is revealed)."""
        profiles = {p.id: p for p in await self._visible_profiles()}
        for link, tenant in await self._links(list(profiles)):
            if link.id == link_id:
                return link, tenant, profiles[link.profile_id]
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")

    # ----- views ----------------------------------------------------------------------------

    async def me(self) -> PortalMe:
        profiles = await self._visible_profiles()
        by_profile: dict[str, list[PortalClinic]] = {p.id: [] for p in profiles}
        for link, tenant in await self._links(list(by_profile)):
            by_profile[link.profile_id].append(
                PortalClinic(link_id=link.id, clinic_name=tenant.clinic_name or tenant.name, linked_at=link.linked_at)
            )
        return PortalMe(
            phone_masked=mask_phone(self.phone),
            profiles=[
                PortalProfile(
                    id=p.id, display_name=p.display_name, age_years=age_years(p), gender=p.gender,
                    relationship=p.relationship, is_dependent=p.is_dependent, clinics=by_profile[p.id],
                )
                for p in profiles
                # A profile with no record the holder has been given access to is not shown at all: a
                # recycled number must not learn an earlier owner's name (activate a record to see it).
                # A profile the holder added themselves in the portal is always theirs to see.
                if by_profile[p.id] or p.source == "portal"
            ],
        )

    async def records(self, profile_id: str) -> PortalRecords:
        profile = await self._profile(profile_id)
        appointments: list[PortalAppointment] = []
        prescriptions: list[PortalPrescription] = []
        receipts: list[PortalReceipt] = []
        try:
            for link, tenant in await self._links([profile.id]):
                # One clinic at a time: bind it for row-level security, then read only this patient's rows
                await bind_tenant(self.db, tenant.id)
                clinic = tenant.clinic_name or tenant.name
                doctors = {
                    u.id: u.full_name
                    for u in (await self.db.execute(select(User).where(User.tenant_id == tenant.id))).scalars()
                }
                for a in (
                    await self.db.execute(
                        select(Appointment)
                        .where(Appointment.tenant_id == tenant.id, Appointment.patient_id == link.patient_id)
                        .order_by(Appointment.appointment_date.desc())
                        .limit(RECORD_LIMIT)
                    )
                ).scalars():
                    appointments.append(
                        PortalAppointment(
                            clinic_name=clinic, doctor_name=doctors.get(a.doctor_id), date=a.appointment_date,
                            time=a.appointment_time.strftime("%H:%M"), duration_minutes=a.duration_minutes,
                            status=a.status, reason=a.reason,
                        )
                    )
                for rx in (
                    await self.db.execute(
                        select(Prescription)
                        .where(
                            Prescription.tenant_id == tenant.id,
                            Prescription.patient_id == link.patient_id,
                            Prescription.status == "issued",
                        )
                        .options(selectinload(Prescription.items))
                        .order_by(Prescription.created_at.desc())
                        .limit(RECORD_LIMIT)
                    )
                ).scalars():
                    prescriptions.append(
                        PortalPrescription(
                            id=rx.id, link_id=link.id, clinic_name=clinic, doctor_name=doctors.get(rx.prescribed_by),
                            date=rx.created_at.date(), diagnosis=rx.diagnosis, advice=rx.advice,
                            items=[
                                PortalPrescriptionItem(
                                    medicine=i.medicine_name or "", dosage=i.dosage, frequency=i.frequency,
                                    duration=i.duration, instructions=i.instructions,
                                )
                                for i in sorted(rx.items, key=lambda i: i.display_order)
                            ],
                        )
                    )
                invoices = {
                    i.payment_id: i.invoice_number
                    for i in (await self.db.execute(select(Invoice).where(Invoice.tenant_id == tenant.id))).scalars()
                }
                for pay in (
                    await self.db.execute(
                        select(Payment)
                        .where(
                            Payment.tenant_id == tenant.id, Payment.patient_id == link.patient_id, Payment.status == "paid"
                        )
                        .order_by(Payment.payment_date.desc())
                        .limit(RECORD_LIMIT)
                    )
                ).scalars():
                    receipts.append(
                        PortalReceipt(
                            clinic_name=clinic, date=pay.payment_date, amount=float(pay.amount), currency=pay.currency,
                            method=pay.payment_method, description=pay.description,
                            invoice_number=invoices.get(pay.id),
                        )
                    )
        finally:
            await bind_tenant(self.db, None)
        appointments.sort(key=lambda a: (a.date, a.time), reverse=True)
        prescriptions.sort(key=lambda r: r.date, reverse=True)
        receipts.sort(key=lambda r: r.date, reverse=True)
        return PortalRecords(
            appointments=appointments[:RECORD_LIMIT], prescriptions=prescriptions[:RECORD_LIMIT], receipts=receipts[:RECORD_LIMIT]
        )

    async def prescription_pdf(self, link_id: str, prescription_id: str) -> tuple[bytes, str]:
        link, tenant, _profile = await self._link(link_id)
        from app.modules.prescription.service import PrescriptionService

        try:
            await bind_tenant(self.db, tenant.id)
            rx = (
                await self.db.execute(
                    select(Prescription).where(
                        Prescription.id == prescription_id,
                        Prescription.tenant_id == tenant.id,
                        Prescription.patient_id == link.patient_id,
                        Prescription.status == "issued",
                    )
                )
            ).scalar_one_or_none()
            if rx is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Prescription not found")
            return await PrescriptionService(self.db, tenant.id).build_pdf(prescription_id)
        finally:
            await bind_tenant(self.db, None)

    # ----- changes --------------------------------------------------------------------------

    async def activate(self, raw_code: str) -> PortalClinic:
        """A clinic code makes an earlier link visible in the portal (the recycled-number defence)."""
        claim = (
            await self.db.execute(
                select(ClaimCode).where(
                    ClaimCode.code_hash == hash_secret(normalize_claim_code(raw_code), "portal"), ClaimCode.purpose == "portal"
                )
            )
        ).scalar_one_or_none()
        invalid = HTTPException(
            status.HTTP_404_NOT_FOUND, detail={"code": "invalid_portal_code", "message": "That code is not valid or has expired."}
        )
        now = datetime.now(timezone.utc)
        if claim is None or claim.used_at is not None or claim.expires_at < now or not claim.link_id:
            raise invalid
        link = (await self.db.execute(select(PatientLink).where(PatientLink.id == claim.link_id))).scalar_one_or_none()
        if link is None or link.status != "linked":
            raise invalid
        profile = (await self.db.execute(select(PersonProfile).where(PersonProfile.id == link.profile_id))).scalar_one()
        if profile.account_id != self.account_id:
            raise invalid  # a code for someone else's record looks exactly like an invalid one
        if not (profile.relationship == "self" or profile.is_dependent):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail={"code": "profile_not_visible", "message": "This record belongs to another adult, who must sign in with their own phone."},
            )
        tenant = (await self.db.execute(select(Tenant).where(Tenant.id == link.tenant_id))).scalar_one()
        if link.portal_access_at is None:
            link.portal_access_at = now
            self.db.add(
                ConsentEvent(
                    id=str(uuid4()), kind="portal_access", tenant_id=link.tenant_id, patient_id=link.patient_id,
                    profile_id=profile.id, account_id=self.account_id, method="portal_code", staff_user_id=None,
                    script_version=SCRIPT_VERSION, staff_confirmed_told=False,
                )
            )
        claim.used_at = now
        await self.db.commit()
        return PortalClinic(link_id=link.id, clinic_name=tenant.clinic_name or tenant.name, linked_at=link.linked_at)

    async def revoke(self, link_id: str) -> None:
        """The patient removes the link. The clinic keeps its own medical record."""
        link, _tenant, profile = await self._link(link_id)
        now = datetime.now(timezone.utc)
        link.status = "revoked"
        link.revoked_at = now
        link.revoked_by = None
        self.db.add(
            ConsentEvent(
                id=str(uuid4()), kind="revoke", tenant_id=link.tenant_id, patient_id=link.patient_id,
                profile_id=profile.id, account_id=self.account_id, method="portal", staff_user_id=None,
                script_version=SCRIPT_VERSION, staff_confirmed_told=False, note="Removed by the patient in the portal",
            )
        )
        await self.db.commit()
