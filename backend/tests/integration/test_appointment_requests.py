"""Appointment requests (ADR 009, Phase 3): a signed-in patient asks, the clinic confirms or declines."""

import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.modules.identity import requests as requests_module
from app.modules.identity import sms
from app.shared.models import (
    Appointment,
    AppointmentRequest,
    ConsentEvent,
    Patient,
    PatientLink,
    PersonProfile,
    TenantEntitlementOverride,
)

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PHONE = "01711111111"
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


@pytest.fixture
def sent(monkeypatch):
    log = []

    async def capture(phone, message, code):
        log.append({"phone": phone, "message": message, "code": code})

    monkeypatch.setattr(sms, "dispatch_sms", capture)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "OTP_MAX_PER_PHONE_PER_HOUR", 100)
    return log


@pytest.fixture
def clinic_sms(monkeypatch):
    """The platform SMS provider is configured; the Celery send is captured."""
    monkeypatch.setattr(settings, "SMS_PROVIDER", "bulksmsbd")
    monkeypatch.setattr(settings, "BULKSMSBD_API_KEY", "k")
    monkeypatch.setattr(settings, "BULKSMSBD_SENDER_ID", "AltCare")
    texts = []
    stub = SimpleNamespace(delay=lambda **kw: texts.append(kw) or SimpleNamespace(id="t"))
    monkeypatch.setattr("app.modules.integration.tasks.send_platform_sms_task", stub)
    return texts


async def _portal_login(client, sent, phone=PHONE):
    r = await client.post("/api/v1/patient/auth/request", json={"phone": phone})
    v = await client.post("/api/v1/patient/auth/verify", json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"]})
    assert v.status_code == 200, v.text
    return v.json()["access_token"]


async def _go_public(client, db, tenant, doctor_token, **listing):
    tenant.plan = "plus"
    await db.commit()
    r = await client.put(
        "/api/v1/directory/listing",
        json={"is_listed": True, "bio_en": "Homeopath with ten years of experience.", **listing},
        headers=H(doctor_token),
    )
    assert r.status_code == 200 and r.json()["eligibility"]["public"], r.text
    return r.json()["slug"]


async def _me_profile(client, token, name="Rahim Uddin", relationship="self", **extra):
    body = {"display_name": name, "date_of_birth": "1980-05-15", "gender": "male", "relationship": relationship, **extra}
    r = await client.post("/api/v1/patient/profiles", json=body, headers=H(token))
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _ask(client, token, slug, profile_id, **over):
    body = {"practitioner_slug": slug, "profile_id": profile_id, "preferred_date": TOMORROW,
            "preferred_window": "morning", "reason": "Back pain", "consent": True, **over}
    return await client.post("/api/v1/patient/appointment-requests", json=body, headers=H(token))


def _confirm_body(**over):
    return {"appointment_date": TOMORROW, "appointment_time": "10:00", "duration_minutes": 30, **over}


async def _setup(client, db, tenant, doctor_token, sent):
    slug = await _go_public(client, db, tenant, doctor_token)
    token = await _portal_login(client, sent)
    pid = await _me_profile(client, token)
    return slug, token, pid


# ---------------------------------------------------------------- profiles the holder adds


@pytest.mark.asyncio
async def test_holder_adds_themselves_and_a_child_but_not_another_adult(client, sent):
    token = await _portal_login(client, sent)
    me = await _me_profile(client, token)
    # one account holder per phone
    again = await client.post("/api/v1/patient/profiles", json={"display_name": "Karim Ali", "date_of_birth": "1985-01-01", "relationship": "self"}, headers=H(token))
    assert again.status_code == 409 and again.json()["detail"]["code"] == "self_profile_exists"
    # the same person again is the same profile
    assert (await _me_profile(client, token)) == me

    child = await client.post("/api/v1/patient/profiles", json={"display_name": "Little Rahim", "approx_birth_year": date.today().year - 6, "relationship": "child"}, headers=H(token))
    assert child.status_code == 201 and child.json()["is_dependent"] is True
    grown = await client.post("/api/v1/patient/profiles", json={"display_name": "Grown Child", "date_of_birth": "1990-01-01", "relationship": "child"}, headers=H(token))
    assert grown.status_code == 422 and grown.json()["detail"]["code"] == "child_must_be_under_18"
    for rel in ("spouse", "parent", "other"):
        r = await client.post("/api/v1/patient/profiles", json={"display_name": "Someone Else", "date_of_birth": "1970-01-01", "relationship": rel}, headers=H(token))
        assert r.status_code == 422, rel
    assert (await client.post("/api/v1/patient/profiles", json={"display_name": "No Age", "relationship": "child"}, headers=H(token))).status_code == 422

    shown = (await client.get("/api/v1/patient/me", headers=H(token))).json()["profiles"]
    assert {p["display_name"] for p in shown} == {"Rahim Uddin", "Little Rahim"} and all(p["clinics"] == [] for p in shown)


# ---------------------------------------------------------------- asking


@pytest.mark.asyncio
async def test_a_request_reaches_the_clinic_with_a_snapshot_of_basic_details(
    client, doctor_token, sent, db_session, test_tenant, test_user
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    r = await _ask(client, token, slug, pid)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "requested" and body["clinic_name"] == test_tenant.clinic_name and body["doctor_name"] == test_user.full_name
    assert (body["preferred_date"], body["preferred_window"], body["reason"]) == (TOMORROW, "morning", "Back pain")

    mine = (await client.get("/api/v1/patient/appointment-requests", headers=H(token))).json()
    assert [m["id"] for m in mine] == [body["id"]]

    inbox = (await client.get("/api/v1/appointment-requests", headers=H(doctor_token))).json()
    assert len(inbox) == 1
    req = inbox[0]
    assert req["requester"]["display_name"] == "Rahim Uddin" and req["requester"]["phone"] == "+8801711111111"
    assert req["requester"]["gender"] == "male" and req["requester"]["age_years"] >= 40
    assert req["existing_patient_id"] is None and req["status"] == "requested"
    # the clinic is shown a snapshot, never the live profile or its ids
    assert "profile_id" not in req and "account_id" not in req


@pytest.mark.asyncio
async def test_asking_needs_consent_a_public_practitioner_and_a_sensible_date(
    client, doctor_token, sent, db_session, test_tenant
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    assert (await _ask(client, token, slug, pid, consent=False)).status_code == 422
    assert (await _ask(client, token, "no-such-doctor", pid)).status_code == 404
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    far = (date.today() + timedelta(days=90)).isoformat()
    for bad in (yesterday, far):
        r = await _ask(client, token, slug, pid, preferred_date=bad)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "date_out_of_range"
    # a clinic that stops being public (plan ends) can no longer be asked
    test_tenant.plan = "free"
    await db_session.commit()
    assert (await _ask(client, token, slug, pid)).status_code == 404


@pytest.mark.asyncio
async def test_a_practitioner_can_turn_requests_off(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    await client.put("/api/v1/directory/listing", json={"accepts_requests": False}, headers=H(doctor_token))
    r = await _ask(client, token, slug, pid)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_accepting_requests"


@pytest.mark.asyncio
async def test_one_open_request_per_person_per_clinic_and_a_cap_per_account(
    client, doctor_token, sent, db_session, test_tenant, monkeypatch
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    assert (await _ask(client, token, slug, pid)).status_code == 201
    dup = await _ask(client, token, slug, pid)
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "request_in_progress"

    monkeypatch.setattr(requests_module, "MAX_OPEN_PER_ACCOUNT", 1)
    child = await _me_profile(client, token, "Little Rahim", "child", date_of_birth="2019-03-01")
    capped = await _ask(client, token, slug, child)
    assert capped.status_code == 409 and capped.json()["detail"]["code"] == "too_many_open_requests"


@pytest.mark.asyncio
async def test_you_can_only_ask_for_your_own_profiles(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    other = await _portal_login(client, sent, phone="01822222222")
    assert (await _ask(client, other, slug, pid)).status_code == 404  # someone else's profile
    # an adult family member recorded by a clinic is not requestable from this account
    account = (await db_session.execute(select(PersonProfile.account_id).where(PersonProfile.id == pid))).scalar_one()
    adult = PersonProfile(
        id=str(uuid.uuid4()), account_id=account, display_name="Fatema Begum", name_key="fatema begum",
        relationship="spouse", is_dependent=False,
    )
    db_session.add(adult)
    await db_session.commit()
    assert (await _ask(client, token, slug, adult.id)).status_code == 404


# ---------------------------------------------------------------- the clinic's reply


@pytest.mark.asyncio
async def test_confirming_creates_the_record_links_it_books_the_visit_and_texts_the_patient(
    client, doctor_token, sent, clinic_sms, db_session, test_tenant, test_user
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    req_id = (await _ask(client, token, slug, pid)).json()["id"]

    done = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(), headers=H(doctor_token))
    assert done.status_code == 200, done.text
    item = done.json()
    assert item["status"] == "confirmed" and item["appointment"]["time"] == "10:00" and item["appointment"]["status"] == "confirmed"

    patient = (await db_session.execute(select(Patient).where(Patient.id == item["patient_id"]))).scalar_one()
    assert (patient.full_name, patient.phone, str(patient.date_of_birth), patient.gender) == ("Rahim Uddin", "+8801711111111", "1980-05-15", "male")
    link = (await db_session.execute(select(PatientLink).where(PatientLink.patient_id == patient.id))).scalar_one()
    assert link.method == "appointment" and link.status == "linked" and link.portal_access_at is not None
    event = (await db_session.execute(select(ConsentEvent).where(ConsentEvent.patient_id == patient.id))).scalar_one()
    assert event.method == "appointment" and event.script_version == "request-2026-10-v1"
    appt = (await db_session.execute(select(Appointment).where(Appointment.patient_id == patient.id))).scalar_one()
    assert appt.doctor_id == test_user.id and appt.reason == "Back pain" and appt.status == "confirmed"

    assert len(clinic_sms) == 1 and clinic_sms[0]["recipient"] == "+8801711111111" and "10:00" in clinic_sms[0]["message"]

    # the patient sees the confirmed time, and the visit shows in their records
    mine = (await client.get("/api/v1/patient/appointment-requests", headers=H(token))).json()[0]
    assert mine["status"] == "confirmed" and mine["appointment"]["date"] == TOMORROW
    records = (await client.get(f"/api/v1/patient/profiles/{pid}/records", headers=H(token))).json()
    assert [a["reason"] for a in records["appointments"]] == ["Back pain"]


@pytest.mark.asyncio
async def test_a_person_already_linked_here_reuses_their_record(client, doctor_token, sent, db_session, test_tenant, test_patient):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    # the clinic linked this person earlier (verified at the clinic)
    r = await client.post("/api/v1/identity/verify/request", json={"phone": PHONE}, headers=H(doctor_token))
    vt = (await client.post("/api/v1/identity/verify/confirm", json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"], "script_confirmed": True}, headers=H(doctor_token))).json()["verification_token"]
    await client.post("/api/v1/identity/link", json={"verification_token": vt, "patient_id": test_patient.id, "profile_id": pid}, headers=H(doctor_token))

    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    listed = (await client.get("/api/v1/appointment-requests", headers=H(doctor_token))).json()[0]
    assert listed["existing_patient_id"] == test_patient.id
    before = (await db_session.execute(select(func.count()).select_from(Patient))).scalar_one()
    done = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(), headers=H(doctor_token))
    assert done.json()["patient_id"] == test_patient.id
    assert (await db_session.execute(select(func.count()).select_from(Patient))).scalar_one() == before  # no duplicate


@pytest.mark.asyncio
async def test_an_unlinked_record_is_never_matched_automatically(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    old = Patient(id=str(uuid.uuid4()), tenant_id=test_tenant.id, full_name="Rahim Uddin", phone="+8801711111111")
    db_session.add(old)
    await db_session.commit()
    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    done = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(), headers=H(doctor_token))
    assert done.json()["patient_id"] != old.id  # same name and phone, still a new record
    assert (await db_session.execute(select(func.count()).select_from(Patient).where(Patient.full_name == "Rahim Uddin"))).scalar_one() == 2


@pytest.mark.asyncio
async def test_a_taken_slot_leaves_no_half_made_record(client, doctor_token, sent, db_session, test_tenant, test_user):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    blocker = Patient(id=str(uuid.uuid4()), tenant_id=test_tenant.id, full_name="Blocker")
    db_session.add(blocker)
    await db_session.flush()
    from datetime import time

    db_session.add(Appointment(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, patient_id=blocker.id, doctor_id=test_user.id,
        appointment_date=date.fromisoformat(TOMORROW), appointment_time=time(10, 0), duration_minutes=30, status="scheduled",
    ))
    await db_session.commit()
    patients = (await db_session.execute(select(func.count()).select_from(Patient))).scalar_one()

    r = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(), headers=H(doctor_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "slot_taken"
    assert (await db_session.execute(select(func.count()).select_from(Patient))).scalar_one() == patients
    assert (await db_session.execute(select(AppointmentRequest.status))).scalar_one() == "requested"
    # another time works
    ok = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(appointment_time="11:00"), headers=H(doctor_token))
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_confirm_validation_and_the_plan_patient_cap(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    url = f"/api/v1/appointment-requests/{req_id}/confirm"
    past = (date.today() - timedelta(days=1)).isoformat()
    assert (await client.post(url, json=_confirm_body(appointment_date=past), headers=H(doctor_token))).status_code == 422
    assert (await client.post(url, json=_confirm_body(doctor_id=str(uuid.uuid4())), headers=H(doctor_token))).status_code == 422

    existing = (await db_session.execute(select(func.count()).select_from(Patient).where(Patient.tenant_id == test_tenant.id))).scalar_one()
    db_session.add(TenantEntitlementOverride(tenant_id=test_tenant.id, entitlement_key="max_patients", enabled=True, limit_value=existing))
    await db_session.commit()
    full = await client.post(url, json=_confirm_body(), headers=H(doctor_token))
    assert full.status_code == 403 and full.json()["detail"]["code"] == "plan_limit_reached"
    assert (await db_session.execute(select(AppointmentRequest.status))).scalar_one() == "requested"  # still waiting


@pytest.mark.asyncio
async def test_confirming_twice_and_the_clinic_text_is_best_effort(
    client, doctor_token, sent, clinic_sms, db_session, test_tenant
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    # no SMS allowance left: the confirmation still goes through, just without a text
    db_session.add(TenantEntitlementOverride(tenant_id=test_tenant.id, entitlement_key="monthly_sms", enabled=True, limit_value=0))
    await db_session.commit()
    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    ok = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(), headers=H(doctor_token))
    assert ok.status_code == 200 and clinic_sms == []
    again = await client.post(f"/api/v1/appointment-requests/{req_id}/confirm", json=_confirm_body(appointment_time="12:00"), headers=H(doctor_token))
    assert again.status_code == 409 and again.json()["detail"]["code"] == "not_open"


@pytest.mark.asyncio
async def test_declining_gives_a_reason_and_the_patient_can_ask_again(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    req_id = (await _ask(client, token, slug, pid)).json()["id"]
    assert (await client.post(f"/api/v1/appointment-requests/{req_id}/decline", json={"reason": "x"}, headers=H(doctor_token))).status_code == 422
    r = await client.post(f"/api/v1/appointment-requests/{req_id}/decline", json={"reason": "Fully booked this week"}, headers=H(doctor_token))
    assert r.status_code == 200 and r.json()["status"] == "declined"
    mine = (await client.get("/api/v1/patient/appointment-requests", headers=H(token))).json()[0]
    assert mine["status"] == "declined" and mine["decline_reason"] == "Fully booked this week"
    assert (await _ask(client, token, slug, pid)).status_code == 201  # only an open request blocks a new one


# ---------------------------------------------------------------- patient cancels


@pytest.mark.asyncio
async def test_patient_cancels_a_waiting_request_or_a_future_appointment(client, doctor_token, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    a = (await _ask(client, token, slug, pid)).json()["id"]
    c = await client.post(f"/api/v1/patient/appointment-requests/{a}/cancel", headers=H(token))
    assert c.status_code == 200 and (c.json()["status"], c.json()["cancelled_by"]) == ("cancelled", "patient")
    assert (await client.post(f"/api/v1/patient/appointment-requests/{a}/cancel", headers=H(token))).status_code == 409

    b = (await _ask(client, token, slug, pid)).json()["id"]
    await client.post(f"/api/v1/appointment-requests/{b}/confirm", json=_confirm_body(), headers=H(doctor_token))
    cancelled = await client.post(f"/api/v1/patient/appointment-requests/{b}/cancel", headers=H(token))
    assert cancelled.status_code == 200 and cancelled.json()["appointment"]["status"] == "cancelled"
    appt = (await db_session.execute(select(Appointment))).scalar_one()
    assert appt.status == "cancelled" and appt.cancellation_reason == "Cancelled by the patient"
    # the clinic sees it was the patient
    listed = (await client.get("/api/v1/appointment-requests", params={"status": "cancelled"}, headers=H(doctor_token))).json()
    assert {i["cancelled_by"] for i in listed} == {"patient"}


@pytest.mark.asyncio
async def test_a_past_appointment_cannot_be_cancelled_here_and_others_cannot_cancel_yours(
    client, doctor_token, sent, db_session, test_tenant
):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    rid = (await _ask(client, token, slug, pid)).json()["id"]
    await client.post(f"/api/v1/appointment-requests/{rid}/confirm", json=_confirm_body(), headers=H(doctor_token))
    stranger = await _portal_login(client, sent, phone="01922222222")
    assert (await client.post(f"/api/v1/patient/appointment-requests/{rid}/cancel", headers=H(stranger))).status_code == 404
    assert (await client.get("/api/v1/patient/appointment-requests", headers=H(stranger))).json() == []

    appt = (await db_session.execute(select(Appointment))).scalar_one()
    appt.appointment_date = date.today() - timedelta(days=2)
    await db_session.commit()
    r = await client.post(f"/api/v1/patient/appointment-requests/{rid}/cancel", headers=H(token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_cancellable"


# ---------------------------------------------------------------- access rules


@pytest.mark.asyncio
async def test_clinics_and_tokens_stay_separate(client, doctor_token, test_access_token_2, sent, db_session, test_tenant):
    slug, token, pid = await _setup(client, db_session, test_tenant, doctor_token, sent)
    rid = (await _ask(client, token, slug, pid)).json()["id"]
    # another clinic sees nothing and can do nothing
    assert (await client.get("/api/v1/appointment-requests", headers=H(test_access_token_2))).json() == []
    for action, body in (("confirm", _confirm_body()), ("decline", {"reason": "no"})):
        assert (await client.post(f"/api/v1/appointment-requests/{rid}/{action}", json=body, headers=H(test_access_token_2))).status_code in (404, 422)
    # staff tokens do not open the patient side, and patient tokens do not open the clinic side
    assert (await client.get("/api/v1/patient/appointment-requests", headers=H(doctor_token))).status_code == 401
    assert (await client.get("/api/v1/appointment-requests", headers=H(token))).status_code in (401, 403)
    assert (await client.post("/api/v1/patient/appointment-requests", json={}, headers=H(doctor_token))).status_code in (401, 422)
