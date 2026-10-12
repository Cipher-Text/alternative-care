"""Patient identity (ADR 009, Phase 1): in-clinic phone verification, profiles, links, claim codes.

Rules enforced here, not in the UI: nothing is linked without a verified code and a consent record;
records are never matched automatically; a clinic sees a profile only after staff just passed an OTP
and typed the visitor's name; a link shares basic details only; links are per clinic."""

import re
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.phone import mask_phone
from app.modules.identity.otp import OtpService, hash_secret
from app.shared.models import (
    ClaimCode,
    ConsentEvent,
    OtpChallenge,
    Patient,
    PatientLink,
    PersonAccount,
    PersonProfile,
    Tenant,
)
from app.shared.models.identity import MAX_PROFILES_PER_ACCOUNT
from app.shared.schemas import (
    BasicDetails,
    ClaimResult,
    LinkResponse,
    NewProfile,
    PatientIdentityStatus,
    ProfileSummary,
)

# Version of the consent wording staff read aloud / the patient is shown (see ADR 009)
SCRIPT_VERSION = "2026-10-v1"
CLAIM_CODE_TTL = timedelta(days=30)
CLAIM_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I/L: easy to read out and type
MAX_SEARCHES_PER_VERIFICATION = 10
MAX_LINKS_PER_VERIFICATION = 5

_PUNCT = re.compile(r"[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~।]")


def name_key(name: str) -> str:
    """Lower-cased, punctuation-free, single-spaced form for matching a typed name and de-duplication."""
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", name.lower())).strip()


def age_years(profile: PersonProfile) -> int | None:
    today = date.today()
    if profile.date_of_birth:
        dob = profile.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if profile.approx_birth_year:
        return today.year - profile.approx_birth_year
    return None


def _conflict(code: str, message: str, **extra) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, "message": message, **extra})


def normalize_claim_code(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", raw.upper())


async def get_or_create_account(db: AsyncSession, phone: str) -> PersonAccount:
    account = (await db.execute(select(PersonAccount).where(PersonAccount.phone == phone))).scalar_one_or_none()
    if account:
        return account
    account = PersonAccount(id=str(uuid4()), phone=phone, phone_verified_at=datetime.now(timezone.utc))
    db.add(account)
    try:
        await db.flush()
    except IntegrityError:  # a concurrent request created it first
        await db.rollback()
        account = (await db.execute(select(PersonAccount).where(PersonAccount.phone == phone))).scalar_one()
    return account


async def find_or_create_profile(
    db: AsyncSession, account_id: str, data: NewProfile
) -> tuple[PersonProfile, bool]:
    """Reuse a profile with the same name and date of birth (or birth year); else create (max 10)."""
    key = name_key(data.display_name)
    existing = (
        await db.execute(
            select(PersonProfile).where(PersonProfile.account_id == account_id, PersonProfile.status == "active")
        )
    ).scalars().all()
    for p in existing:
        same_name = p.name_key == key
        same_dob = data.date_of_birth is not None and p.date_of_birth == data.date_of_birth
        same_year = (
            data.date_of_birth is None
            and data.approx_birth_year is not None
            and p.approx_birth_year == data.approx_birth_year
        )
        if same_name and (same_dob or same_year):
            return p, True
    if len(existing) >= MAX_PROFILES_PER_ACCOUNT:
        raise _conflict("profile_limit", "This phone already has the maximum number of profiles.")
    profile = PersonProfile(
        id=str(uuid4()),
        account_id=account_id,
        display_name=data.display_name.strip(),
        name_key=key,
        date_of_birth=data.date_of_birth,
        approx_birth_year=data.approx_birth_year,
        gender=data.gender,
        division_id=data.division_id,
        district_id=data.district_id,
        upazila_id=data.upazila_id,
        relationship=data.relationship,
        is_dependent=data.is_dependent if data.is_dependent is not None else data.relationship == "child",
    )
    db.add(profile)
    await db.flush()
    return profile, False


class IdentityService:
    """Clinic side. `tenant_id` and `user_id` come from the signed-in staff member."""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ----- verification ---------------------------------------------------------------------

    async def request_code(self, phone: str):
        return await OtpService(self.db).issue(
            phone=phone, purpose="clinic_verify", tenant_id=self.tenant_id, requested_by=self.user_id
        )

    async def confirm_code(self, challenge_id: str, code: str) -> tuple[str, datetime, bool]:
        challenge = await OtpService(self.db).confirm(
            challenge_id, code, purpose="clinic_verify", tenant_id=self.tenant_id, requested_by=self.user_id
        )
        account = await get_or_create_account(self.db, challenge.phone)
        token = secrets.token_urlsafe(32)
        challenge.account_id = account.id
        challenge.token_hash = hash_secret(token, "token")
        challenge.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.IDENTITY_TOKEN_TTL_SECONDS)
        await self.db.commit()
        has_profiles = (
            await self.db.execute(
                select(PersonProfile.id).where(PersonProfile.account_id == account.id, PersonProfile.status == "active").limit(1)
            )
        ).first() is not None
        return token, challenge.token_expires_at, has_profiles

    async def _session(self, token: str) -> OtpChallenge:
        challenge = (
            await self.db.execute(select(OtpChallenge).where(OtpChallenge.token_hash == hash_secret(token, "token")))
        ).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if (
            challenge is None
            or challenge.status != "verified"
            or challenge.tenant_id != self.tenant_id
            or challenge.requested_by != self.user_id
            or challenge.token_expires_at is None
            or challenge.token_expires_at < now
            or challenge.account_id is None
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"code": "invalid_verification", "message": "Verify the phone again."},
            )
        return challenge

    # ----- profiles -------------------------------------------------------------------------

    async def _linked_profile_ids(self) -> set[str]:
        rows = await self.db.execute(
            select(PatientLink.profile_id).where(PatientLink.tenant_id == self.tenant_id, PatientLink.status == "linked")
        )
        return set(rows.scalars().all())

    async def search(self, token: str, name: str) -> list[ProfileSummary]:
        session = await self._session(token)
        if session.search_count >= MAX_SEARCHES_PER_VERIFICATION:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many searches for this verification.")
        session.search_count += 1
        await self.db.commit()
        key = name_key(name)
        if len(key) < 2:
            return []
        profiles = (
            await self.db.execute(
                select(PersonProfile).where(PersonProfile.account_id == session.account_id, PersonProfile.status == "active")
            )
        ).scalars().all()
        linked = await self._linked_profile_ids()
        return [
            ProfileSummary(
                id=p.id, display_name=p.display_name, age_years=age_years(p), gender=p.gender,
                relationship=p.relationship, is_dependent=p.is_dependent, linked_here=p.id in linked,
            )
            for p in profiles
            if key in p.name_key or p.name_key in key
        ][:5]

    async def _profile(self, session: OtpChallenge, profile_id: str) -> PersonProfile:
        profile = (
            await self.db.execute(
                select(PersonProfile).where(
                    PersonProfile.id == profile_id,
                    PersonProfile.account_id == session.account_id,
                    PersonProfile.status == "active",
                )
            )
        ).scalar_one_or_none()
        if profile is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
        return profile

    async def prefill(self, token: str, profile_id: str) -> BasicDetails:
        session = await self._session(token)
        profile = await self._profile(session, profile_id)
        return BasicDetails(
            profile_id=profile.id, display_name=profile.display_name, date_of_birth=profile.date_of_birth,
            approx_birth_year=profile.approx_birth_year, gender=profile.gender, division_id=profile.division_id,
            district_id=profile.district_id, upazila_id=profile.upazila_id, relationship=profile.relationship,
            is_dependent=profile.is_dependent, phone=session.phone,
        )

    # ----- links ----------------------------------------------------------------------------

    async def _patient(self, patient_id: str) -> Patient:
        patient = (
            await self.db.execute(select(Patient).where(Patient.id == patient_id, Patient.tenant_id == self.tenant_id))
        ).scalar_one_or_none()
        if patient is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
        return patient

    async def _active_link(self, patient_id: str) -> PatientLink | None:
        return (
            await self.db.execute(
                select(PatientLink).where(
                    PatientLink.tenant_id == self.tenant_id, PatientLink.patient_id == patient_id, PatientLink.status == "linked"
                )
            )
        ).scalar_one_or_none()

    async def link(self, token: str, patient_id: str, profile_id: str | None, new_profile: NewProfile | None) -> LinkResponse:
        session = await self._session(token)
        if session.link_count >= MAX_LINKS_PER_VERIFICATION:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many records linked with one verification.")
        patient = await self._patient(patient_id)
        if await self._active_link(patient.id):
            raise _conflict("already_linked", "This patient record is already linked to a verified profile.")

        reused = True
        if profile_id:
            profile = await self._profile(session, profile_id)
        else:
            profile, reused = await find_or_create_profile(self.db, session.account_id, new_profile)

        elsewhere = (
            await self.db.execute(
                select(PatientLink.patient_id).where(
                    PatientLink.tenant_id == self.tenant_id, PatientLink.profile_id == profile.id, PatientLink.status == "linked"
                )
            )
        ).scalar_one_or_none()
        if elsewhere:
            raise _conflict(
                "profile_already_linked_here",
                "This person already has a record at your clinic.",
                existing_patient_id=elsewhere,
            )

        now = datetime.now(timezone.utc)
        consent = ConsentEvent(
            id=str(uuid4()), kind="link", tenant_id=self.tenant_id, patient_id=patient.id, profile_id=profile.id,
            account_id=session.account_id, method="clinic_otp", staff_user_id=self.user_id,
            script_version=SCRIPT_VERSION, staff_confirmed_told=True, otp_challenge_id=session.id,
        )
        self.db.add(consent)
        await self.db.flush()
        link = PatientLink(
            id=str(uuid4()), tenant_id=self.tenant_id, patient_id=patient.id, profile_id=profile.id,
            method="clinic_otp", status="linked", linked_at=now, linked_by=self.user_id, consent_event_id=consent.id,
            created_by=self.user_id,
        )
        self.db.add(link)
        session.link_count += 1
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise _conflict("already_linked", "This record or person is already linked.") from exc
        return LinkResponse(
            link_id=link.id, patient_id=patient.id, profile_id=profile.id,
            profile_display_name=profile.display_name, linked_at=now, profile_reused=reused if not profile_id else True,
        )

    async def status(self, patient_id: str) -> PatientIdentityStatus:
        await self._patient(patient_id)
        link = await self._active_link(patient_id)
        if link is None:
            return PatientIdentityStatus(
                patient_id=patient_id, level=0, linked=False, linked_at=None, method=None, profile_display_name=None
            )
        profile = (await self.db.execute(select(PersonProfile).where(PersonProfile.id == link.profile_id))).scalar_one()
        return PatientIdentityStatus(
            patient_id=patient_id, level=1, linked=True, linked_at=link.linked_at, method=link.method,
            profile_display_name=profile.display_name,
        )

    async def revoke(self, patient_id: str, note: str | None) -> PatientIdentityStatus:
        await self._patient(patient_id)
        link = await self._active_link(patient_id)
        if link is None:
            raise _conflict("not_linked", "This patient record is not linked.")
        profile = (await self.db.execute(select(PersonProfile).where(PersonProfile.id == link.profile_id))).scalar_one()
        now = datetime.now(timezone.utc)
        link.status = "revoked"
        link.revoked_at = now
        link.revoked_by = self.user_id
        self.db.add(
            ConsentEvent(
                id=str(uuid4()), kind="revoke", tenant_id=self.tenant_id, patient_id=patient_id, profile_id=profile.id,
                account_id=profile.account_id, method="clinic_otp", staff_user_id=self.user_id,
                script_version=SCRIPT_VERSION, staff_confirmed_told=False, note=note,
            )
        )
        await self.db.commit()
        return await self.status(patient_id)

    # ----- claim codes ----------------------------------------------------------------------

    async def create_claim_code(self, patient_id: str) -> tuple[str, datetime]:
        """A code the clinic gives the patient to link this record later (verify-later route)."""
        await self._patient(patient_id)
        if await self._active_link(patient_id):
            raise _conflict("already_linked", "This patient record is already linked.")
        now = datetime.now(timezone.utc)
        old = (
            await self.db.execute(
                select(ClaimCode).where(ClaimCode.tenant_id == self.tenant_id, ClaimCode.patient_id == patient_id, ClaimCode.used_at.is_(None))
            )
        ).scalars().all()
        for c in old:  # one live code per record
            c.expires_at = now
        raw = "".join(secrets.choice(CLAIM_ALPHABET) for _ in range(8))
        expires = now + CLAIM_CODE_TTL
        self.db.add(
            ClaimCode(
                id=str(uuid4()), tenant_id=self.tenant_id, patient_id=patient_id,
                code_hash=hash_secret(raw, "claim"), expires_at=expires, created_by=self.user_id,
            )
        )
        await self.db.commit()
        return f"{raw[:4]}-{raw[4:]}", expires


class ClaimService:
    """Patient side, no login: verify the phone, then link the record the claim code points to."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _claim(self, raw_code: str) -> ClaimCode:
        claim = (
            await self.db.execute(select(ClaimCode).where(ClaimCode.code_hash == hash_secret(normalize_claim_code(raw_code), "claim")))
        ).scalar_one_or_none()
        if claim is None or claim.used_at is not None or claim.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail={"code": "invalid_claim_code", "message": "That code is not valid or has expired."}
            )
        return claim

    async def request(self, phone: str, raw_code: str):
        claim = await self._claim(raw_code)
        try:
            return await OtpService(self.db).issue(
                phone=phone, purpose="claim", tenant_id=claim.tenant_id, requested_by=None, claim_code_id=claim.id
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            if detail.get("code") in ("plan_limit_reached", "feature_not_in_plan", "plan_expired"):
                # Neutral wording: a patient should not learn about the clinic's plan
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    detail={"code": "clinic_unavailable", "message": "This clinic cannot verify right now. Please ask the clinic."},
                ) from exc
            raise

    async def confirm(self, challenge_id: str, code: str, relationship: str) -> ClaimResult:
        challenge = await OtpService(self.db).confirm(challenge_id, code, purpose="claim", tenant_id=None, requested_by=None)
        claim = (await self.db.execute(select(ClaimCode).where(ClaimCode.id == challenge.claim_code_id))).scalar_one_or_none()
        if claim is None or claim.used_at is not None or claim.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "invalid_claim_code", "message": "That code is not valid or has expired."})
        patient = (await self.db.execute(select(Patient).where(Patient.id == claim.patient_id))).scalar_one()
        tenant = (await self.db.execute(select(Tenant).where(Tenant.id == claim.tenant_id))).scalar_one()
        already = (
            await self.db.execute(
                select(PatientLink.id).where(PatientLink.patient_id == patient.id, PatientLink.status == "linked")
            )
        ).first()
        if already:
            raise _conflict("already_linked", "This record is already linked.")

        account = await get_or_create_account(self.db, challenge.phone)
        profile, _reused = await find_or_create_profile(
            self.db,
            account.id,
            NewProfile(
                display_name=patient.full_name, date_of_birth=patient.date_of_birth, gender=patient.gender,
                division_id=patient.division_id, district_id=patient.district_id, upazila_id=patient.upazila_id,
                relationship=relationship,
            ),
        )
        elsewhere = (
            await self.db.execute(
                select(PatientLink.id).where(
                    PatientLink.tenant_id == claim.tenant_id, PatientLink.profile_id == profile.id, PatientLink.status == "linked"
                )
            )
        ).first()
        if elsewhere:
            raise _conflict("profile_already_linked_here", "You already have a linked record at this clinic.")

        now = datetime.now(timezone.utc)
        consent = ConsentEvent(
            id=str(uuid4()), kind="link", tenant_id=claim.tenant_id, patient_id=patient.id, profile_id=profile.id,
            account_id=account.id, method="claim_code", staff_user_id=None, script_version=SCRIPT_VERSION,
            staff_confirmed_told=False, otp_challenge_id=challenge.id,
        )
        self.db.add(consent)
        await self.db.flush()
        self.db.add(
            PatientLink(
                id=str(uuid4()), tenant_id=claim.tenant_id, patient_id=patient.id, profile_id=profile.id,
                method="claim_code", status="linked", linked_at=now, linked_by=None, consent_event_id=consent.id,
            )
        )
        claim.used_at = now
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise _conflict("already_linked", "This record is already linked.") from exc
        return ClaimResult(linked=True, clinic_name=tenant.clinic_name or tenant.name, profile_display_name=profile.display_name)
