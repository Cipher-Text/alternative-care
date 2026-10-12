"""Patient identity (ADR 009, Phase 1): verified phone, profiles, consent-based links, claim codes."""

import re
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.modules.identity import sms
from app.modules.identity.service import find_or_create_profile
from app.shared.models import (
    ConsentEvent,
    OtpChallenge,
    Patient,
    PatientLink,
    PersonAccount,
    PersonProfile,
    TenantEntitlementOverride,
    User,
)
from app.shared.schemas import NewProfile

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PHONE = "01711111111"
PHONE_E164 = "+8801711111111"


@pytest.fixture
def sent(monkeypatch):
    """Capture the SMS instead of sending; no cooldown so tests can ask for several codes."""
    log = []

    async def capture(phone, message, code):
        log.append({"phone": phone, "message": message, "code": code})

    monkeypatch.setattr(sms, "dispatch_sms", capture)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "OTP_MAX_PER_PHONE_PER_HOUR", 100)
    return log


async def _verify(client, token, sent, phone=PHONE):
    r = await client.post("/api/v1/identity/verify/request", json={"phone": phone}, headers=H(token))
    assert r.status_code == 200, r.text
    code = sent[-1]["code"]
    c = await client.post(
        "/api/v1/identity/verify/confirm",
        json={"challenge_id": r.json()["challenge_id"], "code": code, "script_confirmed": True},
        headers=H(token),
    )
    assert c.status_code == 200, c.text
    return c.json()["verification_token"], c.json()


async def _patient(db, tenant, name, **kw):
    p = Patient(id=str(uuid.uuid4()), tenant_id=tenant.id, full_name=name, phone=PHONE, **kw)
    db.add(p)
    await db.commit()
    return p


def _new_profile(name="Rahim Uddin", **kw):
    return {"display_name": name, "date_of_birth": "1980-05-15", "gender": "male", **kw}


async def _link_new(client, token, vtoken, patient, **profile):
    return await client.post(
        "/api/v1/identity/link",
        json={"verification_token": vtoken, "patient_id": patient.id, "new_profile": _new_profile(**profile)},
        headers=H(token),
    )


def _staff_token(tenant, user_id, role="receptionist"):
    return create_access_token({"sub": user_id, "tenant_id": tenant.id, "role": role, "email": f"{user_id}@x.com", "plan": "free"})


async def _receptionist(db, tenant):
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id, email=f"rec{uuid.uuid4().hex[:6]}@clinic.com",
        password_hash=get_password_hash("RecPass123"), role="receptionist", full_name="Rec", language="en",
        is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db.add(user)
    await db.commit()
    return user, _staff_token(tenant, user.id)


@pytest.mark.asyncio
async def test_phone_verification_links_a_record_with_a_consent_trail(client, doctor_token, db_session, test_tenant, test_patient, sent):
    r = await client.post("/api/v1/identity/verify/request", json={"phone": "0171-111 1111"}, headers=H(doctor_token))
    assert r.status_code == 200 and r.json()["phone_masked"].startswith("+88017")
    assert sent[0]["phone"] == PHONE_E164 and test_tenant.clinic_name in sent[0]["message"]
    code = sent[0]["code"]

    # the code is never stored, only a keyed hash
    row = (await db_session.execute(select(OtpChallenge))).scalar_one()
    assert row.code_hash != code and len(row.code_hash) == 64 and code not in str(row.__dict__.values())

    # the clinic must confirm it read the consent script
    bad = await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": row.id, "code": code, "script_confirmed": False}, headers=H(doctor_token))
    assert bad.status_code == 422

    vtoken, body = await _verify(client, doctor_token, sent)
    assert body["has_profiles"] is False  # a new phone: no profiles yet

    linked = await _link_new(client, doctor_token, vtoken, test_patient)
    assert linked.status_code == 201 and linked.json()["profile_display_name"] == "Rahim Uddin"

    status = (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(doctor_token))).json()
    assert status["level"] == 1 and status["linked"] and status["method"] == "clinic_otp"

    event = (await db_session.execute(select(ConsentEvent))).scalar_one()
    assert (event.kind, event.method, event.staff_confirmed_told, event.script_version) == ("link", "clinic_otp", True, "2026-10-v1")
    assert event.staff_user_id and event.otp_challenge_id


@pytest.mark.asyncio
async def test_unlinked_record_stays_level_zero(client, doctor_token, test_patient):
    s = (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(doctor_token))).json()
    assert (s["level"], s["linked"]) == (0, False)


@pytest.mark.asyncio
async def test_wrong_codes_lock_the_challenge_and_errors_are_generic(client, doctor_token, sent, db_session):
    r = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    cid, good = r.json()["challenge_id"], sent[0]["code"]
    wrong = "000000" if good != "000000" else "111111"
    msgs = set()
    for _ in range(3):
        x = await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": cid, "code": wrong, "script_confirmed": True}, headers=H(doctor_token))
        assert x.status_code == 400
        msgs.add(x.json()["detail"]["code"])
    assert msgs == {"otp_invalid"}
    # locked: even the right code no longer works
    ok = await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": cid, "code": good, "script_confirmed": True}, headers=H(doctor_token))
    assert ok.status_code == 400
    # an unknown challenge looks identical to a wrong code
    unknown = await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": str(uuid.uuid4()), "code": good, "script_confirmed": True}, headers=H(doctor_token))
    assert unknown.json()["detail"]["code"] == "otp_invalid"


@pytest.mark.asyncio
async def test_expired_code_is_refused(client, doctor_token, sent, db_session):
    r = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    row = (await db_session.execute(select(OtpChallenge).where(OtpChallenge.id == r.json()["challenge_id"]))).scalar_one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    x = await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": row.id, "code": sent[0]["code"], "script_confirmed": True}, headers=H(doctor_token))
    assert x.status_code == 400 and x.json()["detail"]["code"] == "otp_expired"


@pytest.mark.asyncio
async def test_abuse_limits_per_phone(client, doctor_token, monkeypatch, sent):
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 60)
    first = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    assert first.status_code == 200
    again = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    assert again.status_code == 429 and again.json()["detail"]["code"] == "otp_cooldown" and "retry-after" in again.headers

    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "OTP_MAX_PER_PHONE_PER_HOUR", 2)
    third = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))  # 2nd this hour
    assert third.status_code == 200
    capped = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    assert capped.status_code == 429 and capped.json()["detail"]["code"] == "otp_phone_limit"


@pytest.mark.asyncio
async def test_clinic_daily_cap_and_plan_cap(client, doctor_token, db_session, test_tenant, monkeypatch, sent):
    monkeypatch.setattr(settings, "OTP_MAX_PER_CLINIC_PER_DAY", 1)
    assert (await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))).status_code == 200
    r = await client.post("/api/v1/identity/verify/request", json={"phone": "01822222222"}, headers=H(doctor_token))
    assert r.status_code == 429 and r.json()["detail"]["code"] == "otp_clinic_daily_cap"

    monkeypatch.setattr(settings, "OTP_MAX_PER_CLINIC_PER_DAY", 100)
    db_session.add(TenantEntitlementOverride(tenant_id=test_tenant.id, entitlement_key="monthly_patient_verifications", enabled=True, limit_value=1))
    await db_session.commit()
    r = await client.post("/api/v1/identity/verify/request", json={"phone": "01933333333"}, headers=H(doctor_token))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "plan_limit_reached"  # 1 already used this month


@pytest.mark.asyncio
async def test_a_failed_send_is_not_counted_against_the_plan(client, doctor_token, db_session, test_tenant, monkeypatch):
    from fastapi import HTTPException

    async def broken(phone, message, code):
        raise HTTPException(503, "SMS is not available right now")

    monkeypatch.setattr(sms, "dispatch_sms", broken)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    assert (await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))).status_code == 503
    row = (await db_session.execute(select(OtpChallenge))).scalar_one()
    assert row.status == "send_failed"
    from app.core.entitlements import EntitlementService

    assert await EntitlementService(db_session).used(test_tenant.id, "monthly_patient_verifications") == 0


@pytest.mark.asyncio
async def test_second_clinic_gets_basic_details_only_and_clinics_stay_separate(
    client, doctor_token, test_access_token_2, db_session, test_tenant, test_tenant_2, test_patient, test_patient_2, sent
):
    # clinic A verifies and links
    vt_a, _ = await _verify(client, doctor_token, sent)
    await _link_new(client, doctor_token, vt_a, test_patient, upazila_id=7)

    # clinic B verifies the same phone: it learns a profile exists, but not who
    vt_b, body = await _verify(client, test_access_token_2, sent)
    assert body["has_profiles"] is True
    assert (await client.post("/api/v1/identity/profiles/search", json={"verification_token": vt_b, "name": "Karim Ali"}, headers=H(test_access_token_2))).json() == []
    found = (await client.post("/api/v1/identity/profiles/search", json={"verification_token": vt_b, "name": "rahim"}, headers=H(test_access_token_2))).json()
    assert [f["display_name"] for f in found] == ["Rahim Uddin"] and found[0]["linked_here"] is False

    prefill = (await client.post("/api/v1/identity/profiles/prefill", json={"verification_token": vt_b, "profile_id": found[0]["id"]}, headers=H(test_access_token_2))).json()
    assert set(prefill) == {
        "profile_id", "display_name", "date_of_birth", "approx_birth_year", "gender", "division_id",
        "district_id", "upazila_id", "relationship", "is_dependent", "phone",
    }  # basic details only: nothing clinical can be in this shape
    assert prefill["upazila_id"] == 7 and prefill["phone"] == PHONE_E164

    link = await client.post("/api/v1/identity/link", json={"verification_token": vt_b, "patient_id": test_patient_2.id, "profile_id": found[0]["id"]}, headers=H(test_access_token_2))
    assert link.status_code == 201

    # each clinic only ever sees its own links, and cannot touch the other's records
    assert (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(test_access_token_2))).status_code == 404
    assert (await client.get(f"/api/v1/identity/patients/{test_patient_2.id}", headers=H(doctor_token))).status_code == 404
    rows = (await db_session.execute(select(PatientLink))).scalars().all()
    assert {r.tenant_id for r in rows} == {test_tenant.id, test_tenant_2.id} and len({r.profile_id for r in rows}) == 1


@pytest.mark.asyncio
async def test_a_verification_token_only_works_for_its_own_clinic_and_staff_member(
    client, doctor_token, test_access_token_2, db_session, test_tenant, test_patient, sent
):
    vt, _ = await _verify(client, doctor_token, sent)
    body = {"verification_token": vt, "name": "rahim"}
    # another clinic
    assert (await client.post("/api/v1/identity/profiles/search", json=body, headers=H(test_access_token_2))).status_code == 403
    # another staff member of the same clinic
    _, rec_token = await _receptionist(db_session, test_tenant)
    assert (await client.post("/api/v1/identity/profiles/search", json=body, headers=H(rec_token))).status_code == 403
    # a made-up token
    r = await client.post("/api/v1/identity/profiles/search", json={**body, "verification_token": "x" * 40}, headers=H(doctor_token))
    assert r.status_code == 403 and r.json()["detail"]["code"] == "invalid_verification"
    # expired
    row = (await db_session.execute(select(OtpChallenge))).scalar_one()
    row.token_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    assert (await client.post("/api/v1/identity/profiles/search", json=body, headers=H(doctor_token))).status_code == 403


@pytest.mark.asyncio
async def test_search_is_limited_per_verification(client, doctor_token, sent):
    vt, _ = await _verify(client, doctor_token, sent)
    codes = []
    for _ in range(11):
        r = await client.post("/api/v1/identity/profiles/search", json={"verification_token": vt, "name": "anything"}, headers=H(doctor_token))
        codes.append(r.status_code)
    assert codes[:10] == [200] * 10 and codes[10] == 429


@pytest.mark.asyncio
async def test_nothing_links_automatically_and_conflicts_are_refused(
    client, doctor_token, db_session, test_tenant, test_patient, sent
):
    vt, _ = await _verify(client, doctor_token, sent)
    assert (await _link_new(client, doctor_token, vt, test_patient)).status_code == 201
    # the same record again
    again = await _link_new(client, doctor_token, vt, test_patient)
    assert again.status_code == 409 and again.json()["detail"]["code"] == "already_linked"
    # the same person on a second record at the same clinic
    twin = await _patient(db_session, test_tenant, "Rahim Uddin (duplicate)")
    dup = await _link_new(client, doctor_token, vt, twin)
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "profile_already_linked_here"
    assert dup.json()["detail"]["existing_patient_id"] == test_patient.id
    # a record from another clinic is simply not found
    assert (await db_session.execute(select(Patient).where(Patient.id == twin.id))).scalar_one()
    foreign = await client.post("/api/v1/identity/link", json={"verification_token": vt, "patient_id": str(uuid.uuid4()), "new_profile": _new_profile("X Y")}, headers=H(doctor_token))
    assert foreign.status_code == 404


@pytest.mark.asyncio
async def test_family_members_share_a_phone_as_separate_profiles(client, doctor_token, db_session, test_tenant, test_patient, sent):
    vt, _ = await _verify(client, doctor_token, sent)
    child = await _patient(db_session, test_tenant, "Little Rahim")
    await _link_new(client, doctor_token, vt, test_patient)
    r = await client.post(
        "/api/v1/identity/link",
        json={"verification_token": vt, "patient_id": child.id, "new_profile": {"display_name": "Little Rahim", "approx_birth_year": date.today().year - 6, "relationship": "child"}},
        headers=H(doctor_token),
    )
    assert r.status_code == 201
    kid = (await db_session.execute(select(PersonProfile).where(PersonProfile.display_name == "Little Rahim"))).scalar_one()
    assert kid.is_dependent is True and kid.relationship == "child"

    # staff searching one name see only that person, not the whole family
    names = lambda res: [p["display_name"] for p in res.json()]  # noqa: E731
    assert names(await client.post("/api/v1/identity/profiles/search", json={"verification_token": vt, "name": "little"}, headers=H(doctor_token))) == ["Little Rahim"]
    assert len((await db_session.execute(select(PersonAccount))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_same_name_and_birth_date_reuse_one_profile_and_profiles_are_capped(db_session):
    account = PersonAccount(id=str(uuid.uuid4()), phone=PHONE_E164, phone_verified_at=datetime.now(timezone.utc))
    db_session.add(account)
    await db_session.flush()
    first, reused = await find_or_create_profile(db_session, account.id, NewProfile(display_name="Rahim Uddin", date_of_birth=date(1980, 5, 15)))
    again, reused2 = await find_or_create_profile(db_session, account.id, NewProfile(display_name="  rahim  UDDIN ", date_of_birth=date(1980, 5, 15)))
    assert (reused, reused2, first.id) == (False, True, again.id)
    for i in range(9):
        await find_or_create_profile(
            db_session, account.id,
            NewProfile(display_name=f"Person {i}", date_of_birth=date(1990, 1, i + 1), relationship="other"),
        )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await find_or_create_profile(
            db_session, account.id, NewProfile(display_name="One too many", date_of_birth=date(2000, 1, 1), relationship="other")
        )
    assert exc.value.detail["code"] == "profile_limit"


@pytest.mark.asyncio
async def test_a_phone_has_only_one_account_holder(db_session):
    account = PersonAccount(id=str(uuid.uuid4()), phone=PHONE_E164, phone_verified_at=datetime.now(timezone.utc))
    db_session.add(account)
    await db_session.flush()
    await find_or_create_profile(db_session, account.id, NewProfile(display_name="Rahim Uddin", date_of_birth=date(1980, 5, 15)))
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await find_or_create_profile(db_session, account.id, NewProfile(display_name="Karim Uddin", date_of_birth=date(1985, 1, 1)))
    assert exc.value.detail["code"] == "self_profile_exists"


@pytest.mark.asyncio
async def test_revoking_removes_the_link_but_keeps_the_record_and_logs_it(client, doctor_token, db_session, test_tenant, test_patient, sent):
    vt, _ = await _verify(client, doctor_token, sent)
    await _link_new(client, doctor_token, vt, test_patient)

    rec, rec_token = await _receptionist(db_session, test_tenant)
    assert (await client.post(f"/api/v1/identity/patients/{test_patient.id}/revoke", json={}, headers=H(rec_token))).status_code == 403  # doctor only

    r = await client.post(f"/api/v1/identity/patients/{test_patient.id}/revoke", json={"note": "Patient asked"}, headers=H(doctor_token))
    assert r.status_code == 200 and r.json()["level"] == 0 and r.json()["linked"] is False
    assert (await db_session.execute(select(Patient).where(Patient.id == test_patient.id))).scalar_one()  # the clinic's record stays
    kinds = [e.kind for e in (await db_session.execute(select(ConsentEvent).order_by(ConsentEvent.created_at))).scalars().all()]
    assert kinds == ["link", "revoke"]
    again = await client.post(f"/api/v1/identity/patients/{test_patient.id}/revoke", json={}, headers=H(doctor_token))
    assert again.status_code == 409

    # it can be linked again after a fresh verification
    vt2, _ = await _verify(client, doctor_token, sent)
    assert (await _link_new(client, doctor_token, vt2, test_patient)).status_code == 201


@pytest.mark.asyncio
async def test_receptionists_can_verify_and_link(client, db_session, test_tenant, test_patient, sent):
    _, token = await _receptionist(db_session, test_tenant)
    vt, _ = await _verify(client, token, sent)
    assert (await _link_new(client, token, vt, test_patient)).status_code == 201


@pytest.mark.asyncio
async def test_access_rules(client, admin_access_token, sent):
    assert (await client.post("/api/v1/identity/verify/request", json={"phone": PHONE})).status_code in (401, 403)
    # a platform admin has no clinic, so it cannot verify patients
    assert (await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(admin_access_token))).status_code == 403


@pytest.mark.asyncio
async def test_phone_must_be_a_bangladesh_mobile(client, doctor_token, sent):
    for bad in ("12345", "0171111", "+14155552671", "abc"):
        assert (await client.post("/api/v1/identity/verify/request", json={"phone": bad}, headers=H(doctor_token))).status_code == 422, bad


# ===== claim codes: link a record later from the patient's own phone =====


async def _claim_code(client, token, patient):
    r = await client.post(f"/api/v1/identity/patients/{patient.id}/claim-code", headers=H(token))
    assert r.status_code == 200, r.text
    return r.json()["code"]


@pytest.mark.asyncio
async def test_claim_code_links_a_record_without_the_clinic(client, doctor_token, db_session, test_patient, sent):
    code = await _claim_code(client, doctor_token, test_patient)
    assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{4}", code)

    from app.shared.models import ClaimCode

    stored = (await db_session.execute(select(ClaimCode))).scalar_one()
    assert stored.code_hash != code and code.replace("-", "") not in str(stored.__dict__.values())  # hashed

    req = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": code.lower()})  # no login
    assert req.status_code == 200
    ok = await client.post(
        "/api/v1/public/identity/claim/confirm",
        json={"challenge_id": req.json()["challenge_id"], "code": sent[-1]["code"], "relationship": "self", "consent": True},
    )
    assert ok.status_code == 200 and ok.json()["linked"] is True and ok.json()["profile_display_name"] == test_patient.full_name

    status = (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(doctor_token))).json()
    assert status["level"] == 1 and status["method"] == "claim_code"
    event = (await db_session.execute(select(ConsentEvent))).scalar_one()
    assert event.method == "claim_code" and event.staff_user_id is None and event.staff_confirmed_told is False

    # single use
    again = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": code})
    assert again.status_code == 404


@pytest.mark.asyncio
async def test_claim_code_rules(client, doctor_token, db_session, test_patient, sent):
    assert (await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": "ZZZZ-ZZZZ"})).status_code == 404
    code = await _claim_code(client, doctor_token, test_patient)
    # a new code replaces the old one
    newer = await _claim_code(client, doctor_token, test_patient)
    assert (await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": code})).status_code == 404
    req = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": newer})
    assert req.status_code == 200
    # consent is mandatory and a wrong phone code is refused
    no_consent = await client.post("/api/v1/public/identity/claim/confirm", json={"challenge_id": req.json()["challenge_id"], "code": sent[-1]["code"], "consent": False})
    assert no_consent.status_code == 422
    wrong = "000000" if sent[-1]["code"] != "000000" else "111111"
    bad = await client.post("/api/v1/public/identity/claim/confirm", json={"challenge_id": req.json()["challenge_id"], "code": wrong, "consent": True})
    assert bad.status_code == 400
    # an expired claim code
    from app.shared.models import ClaimCode

    row = (await db_session.execute(select(ClaimCode).where(ClaimCode.used_at.is_(None)).order_by(ClaimCode.created_at.desc()))).scalars().first()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    assert (await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": newer})).status_code == 404


@pytest.mark.asyncio
async def test_claim_code_cannot_be_made_for_a_linked_or_foreign_record(client, doctor_token, test_access_token_2, test_patient, test_patient_2, sent):
    vt, _ = await _verify(client, doctor_token, sent)
    await _link_new(client, doctor_token, vt, test_patient)
    assert (await client.post(f"/api/v1/identity/patients/{test_patient.id}/claim-code", headers=H(doctor_token))).status_code == 409
    assert (await client.post(f"/api/v1/identity/patients/{test_patient_2.id}/claim-code", headers=H(doctor_token))).status_code == 404


@pytest.mark.asyncio
async def test_claim_hides_the_clinics_plan_from_the_patient(client, doctor_token, db_session, test_tenant, test_patient, sent):
    code = await _claim_code(client, doctor_token, test_patient)
    db_session.add(TenantEntitlementOverride(tenant_id=test_tenant.id, entitlement_key="monthly_patient_verifications", enabled=True, limit_value=0))
    await db_session.commit()
    r = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": code})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "clinic_unavailable"
    assert "plan" not in r.json()["detail"]["message"].lower()
