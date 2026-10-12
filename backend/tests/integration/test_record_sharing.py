"""Patient-controlled sharing between clinics (ADR 009, Phase 4)."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.database import TENANT_INFO_KEY, bind_tenant, tenant_context
from app.core.security import create_access_token, get_password_hash
from app.modules.identity import sms
from app.shared.models import (
    ConsentEvent,
    DataShare,
    DataShareAccess,
    Patient,
    PatientDiagnosis,
    PersonAccount,
    Prescription,
    PrescriptionItem,
    Tenant,
    User,
)

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PHONE = "01711111111"


@pytest.fixture
def sent(monkeypatch):
    log = []

    async def capture(phone, message, code):
        log.append({"phone": phone, "message": message, "code": code})

    monkeypatch.setattr(sms, "dispatch_sms", capture)
    monkeypatch.setattr(settings, "OTP_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "OTP_MAX_PER_PHONE_PER_HOUR", 100)
    return log


async def _portal_login(client, sent, phone=PHONE):
    r = await client.post("/api/v1/patient/auth/request", json={"phone": phone})
    v = await client.post("/api/v1/patient/auth/verify", json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"]})
    assert v.status_code == 200, v.text
    return v.json()["access_token"]


async def _staff_link(client, staff_token, sent, patient, name="Rahim Uddin", relationship="self", phone=PHONE):
    r = await client.post("/api/v1/identity/verify/request", json={"phone": phone}, headers=H(staff_token))
    c = await client.post(
        "/api/v1/identity/verify/confirm",
        json={"challenge_id": r.json()["challenge_id"], "code": sent[-1]["code"], "script_confirmed": True},
        headers=H(staff_token),
    )
    link = await client.post(
        "/api/v1/identity/link",
        json={"verification_token": c.json()["verification_token"], "patient_id": patient.id,
              "new_profile": {"display_name": name, "date_of_birth": "1980-05-15", "relationship": relationship}},
        headers=H(staff_token),
    )
    assert link.status_code == 201, link.text


async def _records(db, tenant, patient, doctor, tag):
    for status in ("issued", "draft", "voided"):
        rx = Prescription(
            id=str(uuid.uuid4()), tenant_id=tenant.id, patient_id=patient.id, prescribed_by=doctor.id,
            diagnosis=f"{tag} dx {status}", doctors_notes=f"PRIVATE note {tag}", advice="Rest", status=status,
        )
        db.add(rx)
        await db.flush()
        db.add(PrescriptionItem(
            tenant_id=tenant.id, prescription_id=rx.id, medicine_name=f"{tag} medicine {status}", dosage="1 tab",
            frequency="twice daily", duration="5 days", display_order=0,
        ))
    db.add(PatientDiagnosis(tenant_id=tenant.id, patient_id=patient.id, description=f"{tag} chronic gastritis", icd_code="K29", diagnosed_at=date(2026, 3, 1), is_active=True))
    await db.commit()


@pytest.fixture
async def world(client, doctor_token, test_access_token_2, sent, db_session, test_tenant, test_tenant_2, test_user, test_user_2, test_patient, test_patient_2):
    """One person with a record at clinic A (tenant 1) and clinic B (tenant 2); the patient is signed in."""
    patient_token = await _portal_login(client, sent)
    await _staff_link(client, doctor_token, sent, test_patient)
    await _staff_link(client, test_access_token_2, sent, test_patient_2)
    await _records(db_session, test_tenant, test_patient, test_user, "ClinicA")
    await _records(db_session, test_tenant_2, test_patient_2, test_user_2, "ClinicB")
    me = (await client.get("/api/v1/patient/me", headers=H(patient_token))).json()["profiles"][0]
    links = {c["clinic_name"]: c["link_id"] for c in me["clinics"]}
    return SimpleNS(
        token=patient_token, a=links[test_tenant.clinic_name], b=links[test_tenant_2.clinic_name], profile_id=me["id"],
        doctor_a=doctor_token, doctor_b=test_access_token_2, patient_a=test_patient, patient_b=test_patient_2,
        pid_a=test_patient.id, pid_b=test_patient_2.id,  # ids captured now: a rolled-back test session expires objects
    )


class SimpleNS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


async def _share(client, w, categories=("prescriptions", "diagnoses"), days=30, source=None, recipient=None, token=None, consent=True):
    return await client.post(
        "/api/v1/patient/shares",
        json={"source_link_id": source or w.a, "recipient_link_id": recipient or w.b, "categories": list(categories), "days": days, "consent": consent},
        headers=H(token or w.token),
    )


@pytest.mark.asyncio
async def test_a_share_lets_the_other_clinics_doctor_read_only_what_was_chosen(client, world, db_session, test_tenant, test_tenant_2):
    r = await _share(client, world)
    assert r.status_code == 201, r.text
    share = r.json()
    assert (share["status"], share["categories"], share["source_clinic"], share["recipient_clinic"]) == (
        "active", ["diagnoses", "prescriptions"], test_tenant.clinic_name, test_tenant_2.clinic_name,
    )

    out = await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))
    assert out.status_code == 200, out.text
    body = out.json()
    assert [p["diagnosis"] for p in body["prescriptions"]] == ["ClinicA dx issued"]  # issued only, and A's, not B's own
    assert body["prescriptions"][0]["items"][0]["medicine"] == "ClinicA medicine issued"
    assert [d["description"] for d in body["diagnoses"]] == ["ClinicA chronic gastritis"]
    assert {p["source_clinic"] for p in body["prescriptions"]} == {test_tenant.clinic_name}
    raw = out.text
    for secret in ("PRIVATE note", "dx draft", "dx voided", "ClinicB"):
        assert secret not in raw, secret

    # both sides can see that it happened, and the patient sees who read it
    mine = (await client.get("/api/v1/patient/shares", headers=H(world.token))).json()[0]
    assert mine["access_count"] == 1 and mine["last_accessed_at"] is not None
    out_a = (await client.get(f"/api/v1/identity/patients/{world.pid_a}/sharing", headers=H(world.doctor_a))).json()
    assert [(s["clinic_name"], s["access_count"]) for s in out_a["outgoing"]] == [(test_tenant_2.clinic_name, 1)] and out_a["incoming"] == []
    in_b = (await client.get(f"/api/v1/identity/patients/{world.pid_b}/sharing", headers=H(world.doctor_b))).json()
    assert [s["clinic_name"] for s in in_b["incoming"]] == [test_tenant.clinic_name] and in_b["outgoing"] == []

    event = (await db_session.execute(select(ConsentEvent).where(ConsentEvent.kind == "share_grant"))).scalar_one()
    assert event.method == "portal" and event.script_version == "share-2026-10-v1" and event.tenant_id == test_tenant.id
    access = (await db_session.execute(select(DataShareAccess))).scalar_one()
    assert access.recipient_tenant_id == test_tenant_2.id and access.record_count == 2


@pytest.mark.asyncio
async def test_only_the_named_categories_are_readable(client, world):
    await _share(client, world, categories=("diagnoses",))
    body = (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()
    assert body["prescriptions"] == [] and len(body["diagnoses"]) == 1


@pytest.mark.asyncio
async def test_sharing_needs_a_recent_sign_in(client, world, db_session):
    account = (await db_session.execute(select(PersonAccount))).scalar_one()

    def token(**claims):
        base = {"sub": account.id, "type": "patient", "exp": datetime.now(timezone.utc) + timedelta(hours=10)}
        return jwt.encode({**base, **claims}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    stale = token(iat=datetime.now(timezone.utc) - timedelta(hours=2))
    legacy = token()  # no iat at all
    for t in (stale, legacy):
        r = await _share(client, world, token=t)
        assert r.status_code == 403 and r.json()["detail"]["code"] == "recent_sign_in_required"
    # these old sessions can still read and stop shares
    assert (await client.get("/api/v1/patient/shares", headers=H(stale))).status_code == 200
    assert (await _share(client, world)).status_code == 201  # the fresh sign-in works


@pytest.mark.asyncio
async def test_share_validation(client, world, sent, doctor_token, test_access_token_2, db_session, test_patient_2):
    assert (await _share(client, world, consent=False)).status_code == 422
    assert (await _share(client, world, categories=())).status_code == 422
    assert (await _share(client, world, categories=("payments",))).status_code == 422  # not a shareable category
    assert (await _share(client, world, days=365)).status_code == 422
    same = await _share(client, world, source=world.a, recipient=world.a)
    assert same.status_code in (409, 422)
    assert (await _share(client, world, source=str(uuid.uuid4()))).status_code == 404

    # someone else's links cannot be used
    stranger = await _portal_login(client, sent, phone="01822222222")
    assert (await _share(client, world, token=stranger)).status_code == 404

    # two different people (the person and their child) cannot be bridged
    child = Patient(id=str(uuid.uuid4()), tenant_id=test_patient_2.tenant_id, full_name="Little Rahim", phone=PHONE)
    db_session.add(child)
    await db_session.commit()
    await _staff_link(client, test_access_token_2, sent, child, name="Little Rahim", relationship="child")
    me = (await client.get("/api/v1/patient/me", headers=H(world.token))).json()["profiles"]
    kid = next(p for p in me if p["display_name"] == "Little Rahim")
    r = await _share(client, world, source=world.a, recipient=kid["clinics"][0]["link_id"])
    assert r.status_code == 422 and r.json()["detail"]["code"] == "different_people"


@pytest.mark.asyncio
async def test_one_active_share_per_pair_and_revoking_cuts_access_at_once(client, world, db_session):
    first = (await _share(client, world)).json()
    dup = await _share(client, world)
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "share_exists"

    assert len((await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()["prescriptions"]) == 1
    assert (await client.post(f"/api/v1/patient/shares/{first['id']}/revoke", headers=H(world.token))).status_code == 204
    after = (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()
    assert after["prescriptions"] == [] and after["diagnoses"] == []  # immediate: nothing was ever copied
    assert (await client.get("/api/v1/patient/shares", headers=H(world.token))).json()[0]["status"] == "revoked"
    assert (await client.post(f"/api/v1/patient/shares/{first['id']}/revoke", headers=H(world.token))).status_code == 409
    kinds = [e.kind for e in (await db_session.execute(select(ConsentEvent).where(ConsentEvent.kind.like("share_%")).order_by(ConsentEvent.created_at))).scalars()]
    assert kinds == ["share_grant", "share_revoke"]
    assert (await _share(client, world)).status_code == 201  # and it can be granted again


@pytest.mark.asyncio
async def test_expired_shares_stop_working(client, world, db_session):
    await _share(client, world)
    share = (await db_session.execute(select(DataShare))).scalar_one()
    share.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    body = (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()
    assert body["prescriptions"] == []
    assert (await client.get("/api/v1/patient/shares", headers=H(world.token))).json()[0]["status"] == "expired"


@pytest.mark.asyncio
async def test_removing_either_clinic_from_the_account_ends_the_share(client, world):
    await _share(client, world)
    assert (await client.post(f"/api/v1/patient/links/{world.a}/revoke", headers=H(world.token))).status_code == 204
    shares = (await client.get("/api/v1/patient/shares", headers=H(world.token))).json()
    assert shares[0]["status"] == "ended"
    body = (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()
    assert body["prescriptions"] == [] and body["diagnoses"] == []


@pytest.mark.asyncio
async def test_only_doctors_at_the_recipient_clinic_can_read(client, world, db_session, test_tenant_2):
    await _share(client, world)
    rec = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant_2.id, email="rec5@clinic.com", password_hash=get_password_hash("RecPass123"),
        role="receptionist", full_name="Rec", language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db_session.add(rec)
    await db_session.commit()
    rtoken = create_access_token({"sub": rec.id, "tenant_id": test_tenant_2.id, "role": "receptionist", "email": rec.email, "plan": "free"})
    assert (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(rtoken))).status_code == 403
    # a receptionist may see that a share exists (names and dates), never the records
    summary = await client.get(f"/api/v1/identity/patients/{world.pid_b}/sharing", headers=H(rtoken))
    assert summary.status_code == 200 and "ClinicA" not in summary.text and "medicine" not in summary.text
    # the SOURCE clinic gets nothing from an incoming-share call: shares flow one way, A -> B
    from_a = (await client.get(f"/api/v1/identity/patients/{world.pid_a}/shared-records", headers=H(world.doctor_a))).json()
    assert from_a["prescriptions"] == [] and from_a["diagnoses"] == []


@pytest.mark.asyncio
async def test_a_share_is_between_one_pair_of_clinics_only(client, world, sent, db_session, test_patient_2):
    # a third clinic that the patient also uses
    t3 = Tenant(id=str(uuid.uuid4()), name="Dr Three", email="three@test.com", clinic_name="Third Clinic", is_verified=True, is_approved=True, is_active=True, plan="free")
    db_session.add(t3)
    await db_session.flush()
    doc3 = User(id=str(uuid.uuid4()), tenant_id=t3.id, email="doc3@test.com", password_hash=get_password_hash("TestPass123"), role="doctor", full_name="Dr Three", language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False)
    p3 = Patient(id=str(uuid.uuid4()), tenant_id=t3.id, full_name="Rahim Uddin", phone=PHONE)
    db_session.add_all([doc3, p3])
    await db_session.commit()
    token3 = create_access_token({"sub": doc3.id, "tenant_id": t3.id, "role": "doctor", "email": doc3.email, "plan": "free"})
    await _staff_link(client, token3, sent, p3)

    await _share(client, world)  # A -> B only
    # clinic three cannot read A's or B's records
    body = (await client.get(f"/api/v1/identity/patients/{p3.id}/shared-records", headers=H(token3))).json()
    assert body["prescriptions"] == [] and body["diagnoses"] == [] and body["shares"] == []
    # and B cannot read clinic three's records, which were never shared
    assert all(p["source_clinic"] != "Third Clinic" for p in (await client.get(f"/api/v1/identity/patients/{world.pid_b}/shared-records", headers=H(world.doctor_b))).json()["prescriptions"])


@pytest.mark.asyncio
async def test_unlinked_patients_and_token_types(client, world, doctor_token, test_tenant):
    stranger = Patient(id=str(uuid.uuid4()), tenant_id=test_tenant.id, full_name="Never Linked")
    assert (await client.get(f"/api/v1/identity/patients/{stranger.id}/shared-records", headers=H(world.doctor_b))).status_code == 404
    # staff tokens never open patient endpoints and the reverse
    assert (await client.get("/api/v1/patient/shares", headers=H(doctor_token))).status_code == 401
    assert (await client.get(f"/api/v1/identity/patients/{world.pid_b}/sharing", headers=H(world.token))).status_code in (401, 403)


@pytest.mark.asyncio
async def test_reading_another_clinics_rows_never_leaves_the_binding_behind(db_session):
    await bind_tenant(db_session, "tenant-a")
    async with tenant_context(db_session, "tenant-b"):
        assert db_session.info[TENANT_INFO_KEY] == "tenant-b"
    assert db_session.info[TENANT_INFO_KEY] == "tenant-a"

    await bind_tenant(db_session, None)
    async with tenant_context(db_session, "tenant-b"):
        assert db_session.info[TENANT_INFO_KEY] == "tenant-b"
    assert TENANT_INFO_KEY not in db_session.info  # nothing was bound before, nothing is left
