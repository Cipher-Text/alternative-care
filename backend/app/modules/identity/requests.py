"""Appointment requests (ADR 009, Phase 3): a signed-in patient asks a public practitioner for an
appointment; the clinic confirms or declines.

Rules enforced here:
- Only the holder's own profile or a child can ask; only a currently public practitioner can be asked.
- The clinic sees a snapshot of basic details taken at request time, never the live profile.
- Asking is the consent to share those details with that clinic and to link its record to the profile.
- Confirming goes through the normal appointment and patient rules (slot conflicts, plan patient cap), and
  never matches an existing unlinked record automatically: a person not yet linked here gets a new record.
"""

from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import bind_tenant
from app.modules.appointments.service import AppointmentService
from app.modules.directory.service import PublicDirectoryService
from app.modules.identity.portal import PatientContext, PortalService
from app.modules.identity.service import SCRIPT_VERSION, age_years, find_or_create_profile
from app.modules.patient.service import PatientService
from app.shared.models import (
    Appointment,
    AppointmentRequest,
    ConsentEvent,
    PatientLink,
    PersonProfile,
    PractitionerListing,
    Tenant,
    User,
)
from app.shared.schemas import (
    AppointmentRequestCreate,
    ClinicRequestItem,
    ConfirmRequest,
    DeclineRequest,
    PatientRequestResponse,
    PatientCreate,
    PortalProfile,
    PortalProfileCreate,
    RequestedAppointment,
    Requester,
)
from app.shared.schemas.appointment import AppointmentCreate

logger = structlog.get_logger()

MAX_OPEN_PER_ACCOUNT = 5
MAX_DAYS_AHEAD = 60
REQUEST_SCRIPT = "request-2026-10-v1"  # the consent wording shown when asking (see the portal UI)


def _conflict(code: str, message: str, http_status: int = status.HTTP_409_CONFLICT) -> HTTPException:
    return HTTPException(http_status, detail={"code": code, "message": message})


def age_years_from(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _snapshot_age(snap: dict) -> int | None:
    today = date.today()
    if snap.get("date_of_birth"):
        dob = date.fromisoformat(snap["date_of_birth"])
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if snap.get("approx_birth_year"):
        return today.year - snap["approx_birth_year"]
    return None


async def _sms(db: AsyncSession, tenant_id: str, phone: str, message: str) -> None:
    """Best-effort text to the patient from the clinic's own SMS allowance. It never fails the action."""
    try:
        from app.core.credits import CreditService
        from app.core.messaging import sms_configured
        from app.modules.integration.tasks import send_platform_sms_task

        if not sms_configured():
            return
        source = await CreditService(db, tenant_id).spend("sms")
        send_platform_sms_task.delay(tenant_id=tenant_id, recipient=phone, message=message, source=source)
    except Exception:  # noqa: BLE001 — no credits left, no provider, no broker: the request itself stands
        logger.info("appointment_request_sms_skipped", tenant_id=tenant_id)


class PortalRequestService:
    """Patient side."""

    def __init__(self, db: AsyncSession, patient: PatientContext):
        self.db = db
        self.patient = patient
        self.portal = PortalService(db, patient)

    # ----- profiles the holder adds ----------------------------------------------------------

    async def create_profile(self, data: PortalProfileCreate) -> PortalProfile:
        if data.relationship == "child":
            age = age_years_from(data.date_of_birth) if data.date_of_birth else date.today().year - data.approx_birth_year
            if age >= 18:
                raise _conflict(
                    "child_must_be_under_18",
                    "Only a child under 18 can be added here. Another adult signs in with their own phone.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        from app.shared.schemas import NewProfile

        profile, reused = await find_or_create_profile(
            self.db,
            self.patient.account_id,
            NewProfile(
                display_name=data.display_name, date_of_birth=data.date_of_birth, approx_birth_year=data.approx_birth_year,
                gender=data.gender, division_id=data.division_id, district_id=data.district_id,
                upazila_id=data.upazila_id, relationship=data.relationship,
            ),
        )
        if not reused:
            profile.source = "portal"
        await self.db.commit()
        return PortalProfile(
            id=profile.id, display_name=profile.display_name, age_years=age_years(profile), gender=profile.gender,
            relationship=profile.relationship, is_dependent=profile.is_dependent, clinics=[],
        )

    # ----- requests --------------------------------------------------------------------------

    async def create(self, data: AppointmentRequestCreate) -> PatientRequestResponse:
        profile = await self.portal._profile(data.profile_id)  # own profile or child, else 404
        listing, tenant = await PublicDirectoryService(self.db)._find(data.practitioner_slug)  # 404 unless public
        if not listing.accepts_requests:
            raise _conflict("not_accepting_requests", "This practitioner is not taking online requests.")
        today = date.today()
        if not (today <= data.preferred_date <= today + timedelta(days=MAX_DAYS_AHEAD)):
            raise _conflict(
                "date_out_of_range", f"Choose a date within the next {MAX_DAYS_AHEAD} days.", status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        open_count = (
            await self.db.execute(
                select(func.count()).select_from(AppointmentRequest).where(
                    AppointmentRequest.account_id == self.patient.account_id, AppointmentRequest.status == "requested"
                )
            )
        ).scalar_one()
        if open_count >= MAX_OPEN_PER_ACCOUNT:
            raise _conflict("too_many_open_requests", "You have several requests waiting. Wait for a reply or cancel one.")

        req = AppointmentRequest(
            id=str(uuid4()),
            tenant_id=tenant.id,
            listing_id=listing.id,
            account_id=self.patient.account_id,
            profile_id=profile.id,
            preferred_date=data.preferred_date,
            preferred_window=data.preferred_window,
            reason=data.reason,
            consented_at=datetime.now(timezone.utc),
            snapshot={
                "display_name": profile.display_name,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "approx_birth_year": profile.approx_birth_year,
                "gender": profile.gender,
                "division_id": profile.division_id,
                "district_id": profile.district_id,
                "upazila_id": profile.upazila_id,
                "relationship": profile.relationship,
                "is_dependent": profile.is_dependent,
                "phone": self.patient.phone,
                "consent_wording": REQUEST_SCRIPT,
            },
        )
        self.db.add(req)
        try:
            await self.db.commit()
        except IntegrityError as exc:  # one open request per person per clinic
            await self.db.rollback()
            raise _conflict("request_in_progress", "You already have a request waiting with this clinic.") from exc
        await self.db.refresh(req)
        return await self._response(req)

    async def _appointment(self, req: AppointmentRequest) -> RequestedAppointment | None:
        if not req.appointment_id:
            return None
        try:
            await bind_tenant(self.db, req.tenant_id)
            appt = (
                await self.db.execute(
                    select(Appointment).where(Appointment.id == req.appointment_id, Appointment.tenant_id == req.tenant_id)
                )
            ).scalar_one_or_none()
        finally:
            await bind_tenant(self.db, None)
        if appt is None:
            return None
        return RequestedAppointment(
            date=appt.appointment_date, time=appt.appointment_time.strftime("%H:%M"),
            duration_minutes=appt.duration_minutes, status=appt.status,
        )

    async def _response(self, req: AppointmentRequest) -> PatientRequestResponse:
        tenant = (await self.db.execute(select(Tenant).where(Tenant.id == req.tenant_id))).scalar_one()
        listing = (
            await self.db.execute(select(PractitionerListing).where(PractitionerListing.id == req.listing_id))
        ).scalar_one_or_none() if req.listing_id else None
        doctor = (
            await self.db.execute(select(User.full_name).where(User.id == listing.user_id))
        ).scalar_one_or_none() if listing else None
        return PatientRequestResponse(
            id=req.id, status=req.status, clinic_name=tenant.clinic_name or tenant.name,
            practitioner_slug=listing.slug if listing else None, doctor_name=doctor, profile_id=req.profile_id,
            profile_name=req.snapshot.get("display_name", ""), preferred_date=req.preferred_date,
            preferred_window=req.preferred_window, reason=req.reason, created_at=req.created_at,
            appointment=await self._appointment(req), decline_reason=req.decline_reason, cancelled_by=req.cancelled_by,
        )

    async def list(self) -> list[PatientRequestResponse]:
        visible = {p.id for p in await self.portal._visible_profiles()}
        rows = (
            await self.db.execute(
                select(AppointmentRequest)
                .where(AppointmentRequest.account_id == self.patient.account_id, AppointmentRequest.profile_id.in_(visible))
                .order_by(AppointmentRequest.created_at.desc())
                .limit(50)
            )
        ).scalars().all() if visible else []
        return [await self._response(r) for r in rows]

    async def cancel(self, request_id: str) -> PatientRequestResponse:
        visible = {p.id for p in await self.portal._visible_profiles()}
        req = (
            await self.db.execute(
                select(AppointmentRequest).where(
                    AppointmentRequest.id == request_id, AppointmentRequest.account_id == self.patient.account_id
                )
            )
        ).scalar_one_or_none()
        if req is None or req.profile_id not in visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")

        if req.status == "requested":
            req.status, req.cancelled_by = "cancelled", "patient"
        elif req.status == "confirmed" and req.appointment_id:
            try:
                await bind_tenant(self.db, req.tenant_id)
                appt = (await self.db.execute(select(Appointment).where(Appointment.id == req.appointment_id))).scalar_one_or_none()
                if appt is None or appt.status not in ("scheduled", "confirmed") or appt.appointment_date < date.today():
                    raise _conflict("not_cancellable", "This appointment can no longer be cancelled here. Contact the clinic.")
                appt.status = "cancelled"
                appt.cancelled_at = datetime.now(timezone.utc)
                appt.cancellation_reason = "Cancelled by the patient"
                req.status, req.cancelled_by = "cancelled", "patient"
                await self.db.flush()
            finally:
                await bind_tenant(self.db, None)
        else:
            raise _conflict("not_cancellable", "This request can no longer be cancelled.")
        await self.db.commit()
        await self.db.refresh(req)
        return await self._response(req)


class ClinicRequestService:
    """Clinic side (doctors and receptionists)."""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _get(self, request_id: str) -> AppointmentRequest:
        req = (
            await self.db.execute(
                select(AppointmentRequest).where(AppointmentRequest.id == request_id, AppointmentRequest.tenant_id == self.tenant_id)
            )
        ).scalar_one_or_none()
        if req is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
        return req

    async def _existing_patient(self, profile_id: str) -> str | None:
        return (
            await self.db.execute(
                select(PatientLink.patient_id).where(
                    PatientLink.tenant_id == self.tenant_id, PatientLink.profile_id == profile_id, PatientLink.status == "linked"
                )
            )
        ).scalar_one_or_none()

    async def _items(self, rows: list[AppointmentRequest]) -> list[ClinicRequestItem]:
        listings = {
            l.id: l
            for l in (
                await self.db.execute(
                    select(PractitionerListing).where(PractitionerListing.id.in_([r.listing_id for r in rows if r.listing_id]))
                )
            ).scalars()
        } if rows else {}
        doctors = {u.id: u.full_name for u in (await self.db.execute(select(User).where(User.tenant_id == self.tenant_id))).scalars()}
        out = []
        for r in rows:
            appt = None
            if r.appointment_id:
                a = (await self.db.execute(select(Appointment).where(Appointment.id == r.appointment_id, Appointment.tenant_id == self.tenant_id))).scalar_one_or_none()
                if a:
                    appt = RequestedAppointment(
                        date=a.appointment_date, time=a.appointment_time.strftime("%H:%M"),
                        duration_minutes=a.duration_minutes, status=a.status,
                    )
            snap = r.snapshot
            doctor_id = listings[r.listing_id].user_id if r.listing_id in listings else None
            out.append(
                ClinicRequestItem(
                    id=r.id, status=r.status,
                    requester=Requester(
                        display_name=snap["display_name"], age_years=_snapshot_age(snap), gender=snap.get("gender"),
                        phone=snap["phone"], relationship=snap["relationship"], is_dependent=snap["is_dependent"],
                    ),
                    preferred_date=r.preferred_date, preferred_window=r.preferred_window, reason=r.reason,
                    doctor_id=doctor_id, doctor_name=doctors.get(doctor_id), created_at=r.created_at, appointment=appt,
                    patient_id=r.patient_id,
                    existing_patient_id=await self._existing_patient(r.profile_id) if r.status == "requested" else None,
                    decline_reason=r.decline_reason, cancelled_by=r.cancelled_by,
                )
            )
        return out

    async def list(self, status_filter: str | None, limit: int, offset: int) -> list[ClinicRequestItem]:
        q = select(AppointmentRequest).where(AppointmentRequest.tenant_id == self.tenant_id)
        if status_filter:
            q = q.where(AppointmentRequest.status == status_filter)
        rows = (await self.db.execute(q.order_by(AppointmentRequest.created_at.desc()).limit(limit).offset(offset))).scalars().all()
        return await self._items(list(rows))

    async def confirm(self, request_id: str, data: ConfirmRequest) -> ClinicRequestItem:
        req = await self._get(request_id)
        if req.status != "requested":
            raise _conflict("not_open", "This request is no longer waiting for a reply.")
        if data.appointment_date < date.today():
            raise _conflict("date_in_past", "Choose a date that has not passed.", status.HTTP_422_UNPROCESSABLE_ENTITY)
        listing = (
            await self.db.execute(select(PractitionerListing).where(PractitionerListing.id == req.listing_id))
        ).scalar_one_or_none() if req.listing_id else None
        doctor_id = data.doctor_id or (listing.user_id if listing else None)
        doctor = (
            await self.db.execute(
                select(User).where(User.id == doctor_id, User.tenant_id == self.tenant_id, User.role == "doctor", User.is_active.is_(True))
            )
        ).scalar_one_or_none() if doctor_id else None
        if doctor is None:
            raise _conflict("doctor_not_found", "Choose a doctor of this clinic.", status.HTTP_422_UNPROCESSABLE_ENTITY)

        appointments = AppointmentService(self.db, self.tenant_id)
        # Check the slot BEFORE creating anything, so a conflict leaves no half-made patient record
        if not await appointments.check_time_slot_available(
            doctor_id=doctor.id, appointment_date=data.appointment_date,
            appointment_time=data.appointment_time, duration_minutes=data.duration_minutes,
        ):
            raise _conflict("slot_taken", "That time is not free for this doctor. Choose another time.")

        snap = req.snapshot
        patient_id = await self._existing_patient(req.profile_id)
        if patient_id is None:
            # Never matched automatically: a person not yet linked here gets a new record (plan cap applies)
            patient = await PatientService(self.db, self.tenant_id).create_patient(
                PatientCreate(
                    full_name=snap["display_name"],
                    date_of_birth=date.fromisoformat(snap["date_of_birth"]) if snap.get("date_of_birth") else None,
                    gender=snap["gender"] if snap.get("gender") in ("male", "female", "other") else None,
                    phone=snap["phone"], division_id=snap.get("division_id"), district_id=snap.get("district_id"),
                    upazila_id=snap.get("upazila_id"),
                ),
                created_by=self.user_id,
            )
            patient_id = patient.id
            now = datetime.now(timezone.utc)
            profile = (await self.db.execute(select(PersonProfile).where(PersonProfile.id == req.profile_id))).scalar_one()
            consent = ConsentEvent(
                id=str(uuid4()), kind="link", tenant_id=self.tenant_id, patient_id=patient_id, profile_id=profile.id,
                account_id=profile.account_id, method="appointment", staff_user_id=self.user_id,
                script_version=snap.get("consent_wording", REQUEST_SCRIPT), staff_confirmed_told=False,
            )
            self.db.add(consent)
            await self.db.flush()
            self.db.add(
                PatientLink(
                    id=str(uuid4()), tenant_id=self.tenant_id, patient_id=patient_id, profile_id=profile.id,
                    method="appointment", status="linked", linked_at=now, linked_by=self.user_id,
                    consent_event_id=consent.id, portal_access_at=now,  # the patient asked, so they may see it
                )
            )
            await self.db.commit()

        appointment = await appointments.create_appointment(
            AppointmentCreate(
                patient_id=patient_id, doctor_id=doctor.id, appointment_date=data.appointment_date,
                appointment_time=data.appointment_time, duration_minutes=data.duration_minutes, reason=req.reason,
            ),
            created_by=self.user_id,
        )
        appointment.status = "confirmed"  # the clinic explicitly confirmed it
        req.status = "confirmed"
        req.patient_id = patient_id
        req.appointment_id = appointment.id
        req.confirmed_at = datetime.now(timezone.utc)
        req.confirmed_by = self.user_id
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)

        if data.notify_sms:
            tenant = (await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))).scalar_one()
            await _sms(
                self.db, self.tenant_id, snap["phone"],
                f"{tenant.clinic_name or tenant.name}: আপনার অ্যাপয়েন্টমেন্ট নিশ্চিত হয়েছে। "
                f"{data.appointment_date:%d/%m/%Y} {data.appointment_time:%H:%M}।",
            )
            await self.db.refresh(req)  # a refused credit check rolls the session back and expires objects
        return (await self._items([req]))[0]

    async def decline(self, request_id: str, data: DeclineRequest) -> ClinicRequestItem:
        req = await self._get(request_id)
        if req.status != "requested":
            raise _conflict("not_open", "This request is no longer waiting for a reply.")
        req.status = "declined"
        req.decline_reason = data.reason
        req.updated_by = self.user_id
        await self.db.commit()
        await self.db.refresh(req)
        if data.notify_sms:
            tenant = (await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))).scalar_one()
            await _sms(
                self.db, self.tenant_id, req.snapshot["phone"],
                f"{tenant.clinic_name or tenant.name}: আপনার অ্যাপয়েন্টমেন্টের অনুরোধ এবার সম্ভব হয়নি। অন্য সময় আবার চেষ্টা করুন।",
            )
            await self.db.refresh(req)
        return (await self._items([req]))[0]
