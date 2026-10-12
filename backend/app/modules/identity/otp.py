"""SMS verification codes: issue with abuse limits, confirm with attempt limits.

The platform pays for every SMS, so limits are layered: a cooldown and an hourly cap per phone, a
daily cap per clinic, and a monthly per-plan cap (`monthly_patient_verifications`). Codes are six
digits, single use, expire in minutes, and only a keyed hash is stored."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import EntitlementService
from app.modules.identity import sms
from app.shared.models import OtpChallenge, Tenant

ENTITLEMENT = "monthly_patient_verifications"


def hash_secret(value: str, salt: str = "") -> str:
    """Keyed hash for codes and tokens: only this is ever stored."""
    return hmac.new(settings.SECRET_KEY.encode(), f"{salt}:{value}".encode(), hashlib.sha256).hexdigest()


def _refuse(code: str, message: str, http_status: int = status.HTTP_429_TOO_MANY_REQUESTS, **extra) -> HTTPException:
    headers = {"Retry-After": str(extra["retry_after"])} if "retry_after" in extra else None
    return HTTPException(http_status, detail={"code": code, "message": message, **extra}, headers=headers)


class OtpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue(
        self, *, phone: str, purpose: str, tenant_id: str | None, requested_by: str | None, claim_code_id: str | None = None
    ) -> tuple[OtpChallenge, int]:
        """Create a challenge and send the code. Returns (challenge, resend_after_seconds)."""
        now = datetime.now(timezone.utc)

        last = (
            await self.db.execute(
                select(OtpChallenge.created_at).where(OtpChallenge.phone == phone).order_by(OtpChallenge.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        if last and (now - last).total_seconds() < settings.OTP_COOLDOWN_SECONDS:
            wait = settings.OTP_COOLDOWN_SECONDS - int((now - last).total_seconds())
            raise _refuse("otp_cooldown", f"Wait {wait} seconds before asking for another code.", retry_after=wait)

        hour_count = (
            await self.db.execute(
                select(func.count()).select_from(OtpChallenge).where(
                    OtpChallenge.phone == phone, OtpChallenge.created_at >= now - timedelta(hours=1)
                )
            )
        ).scalar_one()
        if hour_count >= settings.OTP_MAX_PER_PHONE_PER_HOUR:
            raise _refuse("otp_phone_limit", "Too many codes were requested for this number. Try again later.", retry_after=3600)

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if tenant_id is not None:
            day_count = (
                await self.db.execute(
                    select(func.count()).select_from(OtpChallenge).where(
                        OtpChallenge.tenant_id == tenant_id, OtpChallenge.created_at >= day_start
                    )
                )
            ).scalar_one()
            if day_count >= settings.OTP_MAX_PER_CLINIC_PER_DAY:
                raise _refuse("otp_clinic_daily_cap", "The daily verification limit was reached. Try again tomorrow.", retry_after=3600)
            # The plan's monthly allowance (403 with a structured upgrade message when used up)
            await EntitlementService(self.db).check_limit(tenant_id, ENTITLEMENT)
        else:
            # Patient portal sign-in has no clinic to bill or cap, so a platform-wide daily ceiling applies
            portal_count = (
                await self.db.execute(
                    select(func.count()).select_from(OtpChallenge).where(
                        OtpChallenge.purpose == "portal_login", OtpChallenge.created_at >= day_start
                    )
                )
            ).scalar_one()
            if portal_count >= settings.OTP_MAX_PORTAL_PER_DAY:
                raise _refuse("otp_portal_daily_cap", "Sign-in codes are unavailable right now. Try again later.", retry_after=3600)

        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge_id = str(uuid4())
        challenge = OtpChallenge(
            id=challenge_id,
            purpose=purpose,
            phone=phone,
            tenant_id=tenant_id,
            requested_by=requested_by,
            claim_code_id=claim_code_id,
            code_hash=hash_secret(code, challenge_id),
            expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS),
        )
        self.db.add(challenge)
        await self.db.commit()

        if purpose == "portal_login":
            message = f"AltCare কোড {code}। আপনার অ্যাকাউন্টে ঢুকতে এটি দিন। অন্য কাউকে দেবেন না।"
        else:
            tenant = (await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
            clinic = tenant.clinic_name or tenant.name
            if purpose == "clinic_verify":
                message = f"AltCare: {clinic} আপনার তথ্য যুক্ত করতে চায়। কোড {code}। রাজি হলে কোডটি বলুন।"
            else:
                message = f"AltCare: {clinic}-এর রেকর্ড যুক্ত করতে কোড {code}। অন্য কাউকে দেবেন না।"
        try:
            await sms.dispatch_sms(phone, message, code)
        except HTTPException:
            challenge.status = "send_failed"  # not counted against the clinic's cap
            await self.db.commit()
            raise
        return challenge, settings.OTP_COOLDOWN_SECONDS

    async def confirm(self, challenge_id: str, code: str, *, purpose: str, tenant_id: str | None, requested_by: str | None) -> OtpChallenge:
        """Check a code. Every failure uses the same generic message, so nothing is revealed."""
        challenge = (
            await self.db.execute(select(OtpChallenge).where(OtpChallenge.id == challenge_id))
        ).scalar_one_or_none()
        bad = _refuse("otp_invalid", "That code is not valid. Check it or ask for a new one.", status.HTTP_400_BAD_REQUEST)
        if (
            challenge is None
            or challenge.purpose != purpose
            or (tenant_id is not None and challenge.tenant_id != tenant_id)
            or (requested_by is not None and challenge.requested_by != requested_by)
        ):
            raise bad
        now = datetime.now(timezone.utc)
        if challenge.status != "sent":
            raise bad
        if challenge.expires_at < now:
            challenge.status = "expired"
            await self.db.commit()
            raise _refuse("otp_expired", "That code has expired. Ask for a new one.", status.HTTP_400_BAD_REQUEST)
        if challenge.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise _refuse("otp_locked", "Too many wrong attempts. Ask for a new code.", status.HTTP_400_BAD_REQUEST)

        if not hmac.compare_digest(challenge.code_hash, hash_secret(code, challenge.id)):
            challenge.attempts += 1
            if challenge.attempts >= settings.OTP_MAX_ATTEMPTS:
                challenge.status = "failed"
            await self.db.commit()
            raise bad
        challenge.status = "verified"
        await self.db.commit()
        return challenge
