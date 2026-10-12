"""Patient portal (ADR 009, Phase 2): phone sign-in and a read-only view across clinics."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_patient_token
from app.modules.identity import sms
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
    PrescriptionItem,
)

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PHONE = "01711111111"
PHONE_E164 = "+8801711111111"


@pytest.fixture
def sent(monkeypatch):
    log = []

    async def capture(phone, message, code):
        log.append({"phone": phone, "message": message, "code": code})

    monkeypatch.setattr(sms, "dispatch_sms", capture)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "OTP_MAX_PER_PHONE_PER_HOUR", 100)
    return log


async def _staff_link(client, staff_token, sent, patient, relationship="self", name="Rahim Uddin", dob="1980-05-15", phone=PHONE):
    """Clinic staff verify the phone at the clinic and link `patient` to a (new or existing) profile."""
    r = await client.post("/api/v1/identity/verify/request", json={"phone": phone}, headers=H(staff_token))
    c = await client.post(
        "/api/v1/identity/verify/confirm",
        json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"], "script_confirmed": True},
        headers=H(staff_token),
    )
    vt = c.json()["verification_token"]
    link = await client.post(
        "/api/v1/identity/link",
        json={"verification_token": vt, "patient_id": patient.id,
              "new_profile": {"display_name": name, "date_of_birth": dob, "relationship": relationship}},
        headers=H(staff_token),
    )
    assert link.status_code == 201, link.text
    return link.json()


async def _portal_login(client, sent, phone=PHONE):
    r = await client.post("/api/v1/patient/auth/request", json={"phone": phone})
    assert r.status_code == 200, r.text
    v = await client.post("/api/v1/patient/auth/verify", json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"]})
    assert v.status_code == 200, v.text
    return v.json()["access_token"]


async def _patient(db, tenant, name):
    p = Patient(id=str(uuid.uuid4()), tenant_id=tenant.id, full_name=name, phone=PHONE)
    db.add(p)
    await db.commit()
    return p


async def _portal_code(client, staff_token, patient):
    r = await client.post(f"/api/v1/identity/patients/{patient.id}/portal-code", headers=H(staff_token))
    assert r.status_code == 200, r.text
    return r.json()["code"]


async def _records(db, tenant, patient, doctor):
    """An appointment, one issued + one draft + one voided prescription, and a paid + a pending payment."""
    db.add(Appointment(
        id=str(uuid.uuid4()), tenant_id=tenant.id, patient_id=patient.id, doctor_id=doctor.id,
        appointment_date=date(2026, 10, 20), appointment_time=time(10, 30), duration_minutes=20,
        status="scheduled", reason="Fever", notes="INTERNAL: suspect malaria, do not tell family",
    ))
    for status, secret in (("issued", "visible"), ("draft", "draft"), ("voided", "voided")):
        rx = Prescription(
            id=str(uuid.uuid4()), tenant_id=tenant.id, patient_id=patient.id, prescribed_by=doctor.id,
            diagnosis=f"Diagnosis {secret}", doctors_notes="PRIVATE doctor note", advice="Rest", status=status,
        )
        db.add(rx)
        await db.flush()
        db.add(PrescriptionItem(
            tenant_id=tenant.id, prescription_id=rx.id, medicine_name=f"Medicine {secret}", dosage="1 tab",
            frequency="twice daily", duration="5 days", display_order=0,
        ))
    paid = Payment(
        id=str(uuid.uuid4()), tenant_id=tenant.id, patient_id=patient.id, amount=500.0, currency="BDT",
        payment_method="cash", status="paid", description="Consultation", payment_date=date(2026, 10, 20), received_by=doctor.id,
    )
    db.add(paid)
    db.add(Payment(
        id=str(uuid.uuid4()), tenant_id=tenant.id, patient_id=patient.id, amount=900.0, currency="BDT",
        payment_method="cash", status="pending", description="Unpaid", payment_date=date(2026, 10, 21), received_by=doctor.id,
    ))
    await db.flush()
    db.add(Invoice(id=str(uuid.uuid4()), tenant_id=tenant.id, payment_id=paid.id, invoice_number="INV-0001", status="issued"))
    await db.commit()


@pytest.mark.asyncio
async def test_sign_in_with_a_phone_code_creates_an_account_and_a_patient_only_token(client, sent, db_session):
    token = await _portal_login(client, sent)
    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert me["phone_masked"].startswith("+88017") and me["profiles"] == []
    account = (await db_session.execute(select(PersonAccount))).scalar_one()
    assert account.phone == PHONE_E164 and account.portal_registered_at is not None
    assert "AltCare" in sent[0]["message"] and sent[0]["code"] in sent[0]["message"]


@pytest.mark.asyncio
async def test_the_code_request_looks_the_same_for_any_phone(client, sent):
    known = await client.post("/api/v1/patient/auth/request", json={"phone": PHONE})
    unknown = await client.post("/api/v1/patient/auth/request", json={"phone": "01899999999"})
    assert known.status_code == unknown.status_code == 200
    assert set(known.json()) == set(unknown.json())


@pytest.mark.asyncio
async def test_wrong_code_is_refused_and_phone_must_be_a_bangladesh_mobile(client, sent):
    r = await client.post("/api/v1/patient/auth/request", json={"phone": PHONE})
    wrong = "000000" if sent[-1]["code"] != "000000" else "111111"
    assert (await client.post("/api/v1/patient/auth/verify", json={"challenge_id": r.json()["challenge_id"], "code": wrong})).status_code == 400
    assert (await client.post("/api/v1/patient/auth/request", json={"phone": "12345"})).status_code == 422


@pytest.mark.asyncio
async def test_staff_and_patient_tokens_are_never_interchangeable(client, doctor_token, sent, db_session):
    patient_token = await _portal_login(client, sent)
    assert (await client.get("/api/v1/patient/me", headers=H(doctor_token))).status_code == 401  # staff token
    assert (await client.get("/api/v1/patient/me")).status_code in (401, 403)
    for path in ("/api/v1/patients", "/api/v1/directory/listing", "/api/v1/billing/subscription"):
        assert (await client.get(path, headers=H(patient_token))).status_code in (401, 403), path
    assert (await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(patient_token))).status_code in (401, 403)
    # a forged token for an account that does not exist is refused
    assert (await client.get("/api/v1/patient/me", headers=H(create_patient_token(str(uuid.uuid4()))))).status_code == 401


@pytest.mark.asyncio
async def test_a_record_linked_before_signing_in_stays_hidden_until_a_clinic_code_activates_it(
    client, doctor_token, sent, db_session, test_tenant, test_patient
):
    await _staff_link(client, doctor_token, sent, test_patient)  # linked at the clinic first
    token = await _portal_login(client, sent)                       # the patient signs in afterwards
    assert (await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"] == []  # nothing, not even the name

    code = await _portal_code(client, doctor_token, test_patient)
    act = await client.post("/api/v1/patient/links/activate", json={"code": code.lower()}, headers=H(token))
    assert act.status_code == 200 and act.json()["clinic_name"] == test_tenant.clinic_name
    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert [p["display_name"] for p in me["profiles"]] == ["Rahim Uddin"] and len(me["profiles"][0]["clinics"]) == 1
    event = (await db_session.execute(select(ConsentEvent).where(ConsentEvent.kind == "portal_access"))).scalar_one()
    assert event.method == "portal_code"
    status = (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(doctor_token))).json()
    assert status["portal_access"] is True


@pytest.mark.asyncio
async def test_a_record_linked_after_signing_in_is_visible_at_once(client, doctor_token, sent, test_patient):
    token = await _portal_login(client, sent)
    await _staff_link(client, doctor_token, sent, test_patient)
    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert len(me["profiles"]) == 1 and me["profiles"][0]["clinics"][0]["clinic_name"]


@pytest.mark.asyncio
async def test_a_recycled_number_sees_nothing_of_the_previous_owner(client, doctor_token, sent, test_patient, test_user, db_session, test_tenant):
    # the previous owner: linked at a clinic, with history, never used the portal
    await _staff_link(client, doctor_token, sent, test_patient, name="Previous Owner")
    await _records(db_session, test_tenant, test_patient, test_user)
    # a new holder of the same number signs in
    token = await _portal_login(client, sent)
    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert me["profiles"] == []
    profile = (await db_session.execute(select(PersonProfile))).scalar_one()
    assert (await client.get(f"/api/v1/patient/profiles/{profile.id}/records", headers=H(token))).json() == {
        "appointments": [], "prescriptions": [], "receipts": [],
    }


@pytest.mark.asyncio
async def test_records_are_read_only_safe_and_come_from_every_linked_clinic(
    client, doctor_token, test_access_token_2, sent, db_session, test_tenant, test_tenant_2, test_user, test_user_2, test_patient, test_patient_2
):
    token = await _portal_login(client, sent)
    await _staff_link(client, doctor_token, sent, test_patient)
    await _staff_link(client, test_access_token_2, sent, test_patient_2)  # same person at a second clinic
    await _records(db_session, test_tenant, test_patient, test_user)
    await _records(db_session, test_tenant_2, test_patient_2, test_user_2)
    # data that must never appear: another patient at the same clinic, and an unlinked clinic's patient
    stranger = await _patient(db_session, test_tenant, "Someone Else")
    await _records(db_session, test_tenant, stranger, test_user)

    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert len(me["profiles"]) == 1 and len(me["profiles"][0]["clinics"]) == 2
    out = await client.get(f"/api/v1/patient/profiles/{me['profiles'][0]['id']}/records", headers=H(token))
    assert out.status_code == 200
    body = out.json()

    assert len(body["appointments"]) == 2 and {a["clinic_name"] for a in body["appointments"]} == {test_tenant.clinic_name, test_tenant_2.clinic_name}
    assert {a["reason"] for a in body["appointments"]} == {"Fever"}
    assert len(body["prescriptions"]) == 2  # issued only, one per clinic
    assert all(rx["items"][0]["medicine"] == "Medicine visible" for rx in body["prescriptions"])
    assert len(body["receipts"]) == 2 and all(r["amount"] == 500.0 and r["invoice_number"] == "INV-0001" for r in body["receipts"])

    raw = out.text
    for secret in ("INTERNAL", "PRIVATE doctor note", "Medicine draft", "Medicine voided", "Unpaid"):
        assert secret not in raw, secret


@pytest.mark.asyncio
async def test_only_your_own_profile_and_your_children_are_visible(client, doctor_token, sent, db_session, test_tenant, test_patient):
    token = await _portal_login(client, sent)
    child = await _patient(db_session, test_tenant, "Little Rahim")
    spouse = await _patient(db_session, test_tenant, "Fatema Begum")
    await _staff_link(client, doctor_token, sent, test_patient)
    await _staff_link(client, doctor_token, sent, child, relationship="child", name="Little Rahim", dob="2019-03-01")
    await _staff_link(client, doctor_token, sent, spouse, relationship="spouse", name="Fatema Begum", dob="1984-02-02")

    me = (await client.get("/api/v1/patient/me", headers=H(token))).json()
    assert {p["display_name"] for p in me["profiles"]} == {"Rahim Uddin", "Little Rahim"}  # not the other adult
    assert next(p for p in me["profiles"] if p["display_name"] == "Little Rahim")["is_dependent"] is True

    adult = (await db_session.execute(select(PersonProfile).where(PersonProfile.display_name == "Fatema Begum"))).scalar_one()
    assert (await client.get(f"/api/v1/patient/profiles/{adult.id}/records", headers=H(token))).status_code == 404
    # a code for another adult's record cannot be used to open it either
    code = await _portal_code(client, doctor_token, spouse)
    r = await client.post("/api/v1/patient/links/activate", json={"code": code}, headers=H(token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "profile_not_visible"


@pytest.mark.asyncio
async def test_portal_code_rules(client, doctor_token, test_access_token_2, sent, db_session, test_patient, test_patient_2):
    # a code needs a linked patient
    assert (await client.post(f"/api/v1/identity/patients/{test_patient.id}/portal-code", headers=H(doctor_token))).status_code == 409
    await _staff_link(client, doctor_token, sent, test_patient)
    token = await _portal_login(client, sent)
    code = await _portal_code(client, doctor_token, test_patient)

    assert (await client.post("/api/v1/patient/links/activate", json={"code": "ZZZZ-ZZZZ"}, headers=H(token))).status_code == 404
    # someone else's account cannot use it: it looks exactly like an invalid code
    other_token = await _portal_login(client, sent, phone="01822222222")
    r = await client.post("/api/v1/patient/links/activate", json={"code": code}, headers=H(other_token))
    assert r.status_code == 404 and r.json()["detail"]["code"] == "invalid_portal_code"
    # the rightful account can, once
    assert (await client.post("/api/v1/patient/links/activate", json={"code": code}, headers=H(token))).status_code == 200
    assert (await client.post("/api/v1/patient/links/activate", json={"code": code}, headers=H(token))).status_code == 404
    # codes are hashed and a newer code replaces the older one
    stored = (await db_session.execute(select(ClaimCode).where(ClaimCode.purpose == "portal"))).scalars().all()
    assert all(c.code_hash != code.replace("-", "") for c in stored)
    # an expired code
    new_code = await _portal_code(client, doctor_token, test_patient)
    row = (await db_session.execute(select(ClaimCode).where(ClaimCode.purpose == "portal", ClaimCode.used_at.is_(None)))).scalars().first()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    assert (await client.post("/api/v1/patient/links/activate", json={"code": new_code}, headers=H(token))).status_code == 404


@pytest.mark.asyncio
async def test_the_two_kinds_of_code_are_not_interchangeable(client, doctor_token, sent, db_session, test_tenant, test_patient):
    await _staff_link(client, doctor_token, sent, test_patient)
    portal_code = await _portal_code(client, doctor_token, test_patient)
    # a portal code cannot be used to link a record through the public claim page
    req = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": portal_code})
    assert req.status_code == 404
    # and a link code cannot activate portal access
    unlinked = await _patient(db_session, test_tenant, "Unlinked Person")
    link_code = (await client.post(f"/api/v1/identity/patients/{unlinked.id}/claim-code", headers=H(doctor_token))).json()["code"]
    token = await _portal_login(client, sent)
    assert (await client.post("/api/v1/patient/links/activate", json={"code": link_code}, headers=H(token))).status_code == 404


@pytest.mark.asyncio
async def test_a_record_linked_through_the_claim_page_is_visible_without_a_second_step(client, doctor_token, sent, test_patient):
    code = (await client.post(f"/api/v1/identity/patients/{test_patient.id}/claim-code", headers=H(doctor_token))).json()["code"]
    req = await client.post("/api/v1/public/identity/claim/request", json={"phone": PHONE, "claim_code": code})
    await client.post(
        "/api/v1/public/identity/claim/confirm",
        json={"challenge_id": req.json()["challenge_id"], "code": sent[-1]["code"], "relationship": "self", "consent": True},
    )
    token = await _portal_login(client, sent)
    assert len((await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"]) == 1


@pytest.mark.asyncio
async def test_the_patient_can_remove_a_clinic_and_the_clinic_keeps_its_record(
    client, doctor_token, sent, db_session, test_tenant, test_patient
):
    token = await _portal_login(client, sent)
    await _staff_link(client, doctor_token, sent, test_patient)
    link_id = (await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"][0]["clinics"][0]["link_id"]

    assert (await client.post(f"/api/v1/patient/links/{link_id}/revoke", headers=H(token))).status_code == 204
    assert (await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"] == []
    assert (await client.post(f"/api/v1/patient/links/{link_id}/revoke", headers=H(token))).status_code == 404  # gone
    assert (await db_session.execute(select(Patient).where(Patient.id == test_patient.id))).scalar_one()  # clinic's record stays
    assert (await client.get(f"/api/v1/identity/patients/{test_patient.id}", headers=H(doctor_token))).json()["level"] == 0
    revoke = (await db_session.execute(select(ConsentEvent).where(ConsentEvent.kind == "revoke"))).scalar_one()
    assert revoke.method == "portal" and revoke.staff_user_id is None


@pytest.mark.asyncio
async def test_someone_elses_link_cannot_be_touched(client, doctor_token, sent, test_patient):
    mine = await _portal_login(client, sent)  # signed in first, so the clinic's link is visible at once
    await _staff_link(client, doctor_token, sent, test_patient)
    link_id = (await client.get("/api/v1/patient/me", headers=H(mine))).json()["profiles"][0]["clinics"][0]["link_id"]
    stranger = await _portal_login(client, sent, phone="01922222222")
    assert (await client.post(f"/api/v1/patient/links/{link_id}/revoke", headers=H(stranger))).status_code == 404
    assert (await client.get("/api/v1/patient/me", headers=H(mine))).json()["profiles"][0]["clinics"]  # still there


@pytest.mark.asyncio
async def test_prescription_pdf_only_for_issued_prescriptions_of_your_own_record(
    client, doctor_token, sent, db_session, test_tenant, test_user, test_patient, monkeypatch
):
    from app.modules.prescription.service import PrescriptionService

    async def fake_pdf(self, prescription_id):
        return b"%PDF-1.4 fake", "prescription.pdf"

    monkeypatch.setattr(PrescriptionService, "build_pdf", fake_pdf)
    token = await _portal_login(client, sent)
    await _staff_link(client, doctor_token, sent, test_patient)
    other = await _patient(db_session, test_tenant, "Someone Else")
    await _records(db_session, test_tenant, test_patient, test_user)
    await _records(db_session, test_tenant, other, test_user)
    link_id = (await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"][0]["clinics"][0]["link_id"]

    mine = {p.status: p.id for p in (await db_session.execute(select(Prescription).where(Prescription.patient_id == test_patient.id))).scalars()}
    theirs = (await db_session.execute(select(Prescription).where(Prescription.patient_id == other.id, Prescription.status == "issued"))).scalar_one()
    ok = await client.get(f"/api/v1/patient/links/{link_id}/prescriptions/{mine['issued']}/pdf", headers=H(token))
    assert ok.status_code == 200 and ok.headers["content-type"] == "application/pdf"
    for rid in (mine["draft"], mine["voided"], theirs.id):
        assert (await client.get(f"/api/v1/patient/links/{link_id}/prescriptions/{rid}/pdf", headers=H(token))).status_code == 404


@pytest.mark.asyncio
async def test_portal_sign_in_has_its_own_ceiling_and_limits(client, sent, monkeypatch):
    monkeypatch.setattr(settings, "OTP_MAX_PORTAL_PER_DAY", 1)
    assert (await client.post("/api/v1/patient/auth/request", json={"phone": PHONE})).status_code == 200
    capped = await client.post("/api/v1/patient/auth/request", json={"phone": "01822222222"})
    assert capped.status_code == 429 and capped.json()["detail"]["code"] == "otp_portal_daily_cap"
    monkeypatch.setattr(settings, "OTP_MAX_PORTAL_PER_DAY", 100)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 60)
    again = await client.post("/api/v1/patient/auth/request", json={"phone": PHONE})
    assert again.status_code == 429 and again.json()["detail"]["code"] == "otp_cooldown"


@pytest.mark.asyncio
async def test_demo_phones_get_a_fixed_code_only_in_development(client, sent, monkeypatch):
    from app.modules.identity.otp import DEMO_OTP_CODE

    for environment, expect_fixed in (("development", True), ("production", False)):
        monkeypatch.setattr(settings, "ENVIRONMENT", environment)
        r = await client.post("/api/v1/patient/auth/request", json={"phone": "01700000001"})
        assert r.status_code == 200, r.text
        assert (sent[-1]["code"] == DEMO_OTP_CODE) is expect_fixed
