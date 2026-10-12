"""The practitioner's "today" view: schedule, waiting requests, follow-ups due, warning signs, plan."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.shared.models import Appointment, Patient, Visit

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
TODAY = date.today()


def _patient(tenant_id, name, active=True):
    return Patient(id=str(uuid.uuid4()), tenant_id=tenant_id, full_name=name, is_active=active)


def _appointment(tenant_id, patient, doctor_id, when=TODAY, at=time(10, 0), status="scheduled"):
    return Appointment(
        id=str(uuid.uuid4()), tenant_id=tenant_id, patient_id=patient.id, doctor_id=doctor_id, appointment_date=when,
        appointment_time=at, duration_minutes=30, status=status, reason="Checkup",
    )


def _visit(tenant_id, patient, doctor_id, days_ago=0, **extra):
    return Visit(
        id=str(uuid.uuid4()), tenant_id=tenant_id, patient_id=patient.id, doctor_id=doctor_id,
        visit_date=TODAY - timedelta(days=days_ago), visit_type="consultation", status="completed", **extra,
    )


async def _today(client, token):
    r = await client.get("/api/v1/dashboard/today", headers=H(token))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_an_empty_clinic_gets_empty_lists(client, doctor_token):
    body = await _today(client, doctor_token)
    assert body["today"] == str(TODAY)
    assert (body["appointments"], body["follow_ups_due"], body["alerts"], body["requests_waiting"]) == ([], [], [], 0)
    assert body["plan"]["expired"] is False


@pytest.mark.asyncio
async def test_todays_appointments_are_ordered_and_scoped(client, doctor_token, db_session, test_tenant, test_tenant_2, test_user, test_user_2):
    a, b, c = _patient(test_tenant.id, "Late Patient"), _patient(test_tenant.id, "Early Patient"), _patient(test_tenant.id, "Cancelled Patient")
    other = _patient(test_tenant_2.id, "Other Clinic Patient")
    db_session.add_all([a, b, c, other])
    await db_session.flush()
    db_session.add_all([
        _appointment(test_tenant.id, a, test_user.id, at=time(15, 0)),
        _appointment(test_tenant.id, b, test_user.id, at=time(9, 0), status="confirmed"),
        _appointment(test_tenant.id, c, test_user.id, at=time(11, 0), status="cancelled"),
        _appointment(test_tenant.id, a, test_user.id, when=TODAY + timedelta(days=1)),  # tomorrow
        _appointment(test_tenant_2.id, other, test_user_2.id),
    ])
    await db_session.commit()
    body = await _today(client, doctor_token)
    assert [(x["patient_name"], x["status"]) for x in body["appointments"]] == [("Early Patient", "confirmed"), ("Late Patient", "scheduled")]
    assert body["appointments"][0]["appointment_time"] == "09:00:00" and body["appointments"][0]["reason"] == "Checkup"


@pytest.mark.asyncio
async def test_follow_ups_due_skip_patients_already_seen_or_booked(client, doctor_token, db_session, test_tenant, test_user):
    overdue, soon, seen_since, booked, too_old, inactive = (
        _patient(test_tenant.id, n) for n in ("Overdue", "Soon", "SeenSince", "Booked", "TooOld", "Inactive")
    )
    inactive.is_active = False
    db_session.add_all([overdue, soon, seen_since, booked, too_old, inactive])
    await db_session.flush()
    t = test_tenant.id
    db_session.add_all([
        _visit(t, overdue, test_user.id, days_ago=10, follow_up_date=TODAY - timedelta(days=3), follow_up_notes="Review the rash"),
        _visit(t, soon, test_user.id, days_ago=5, follow_up_date=TODAY + timedelta(days=2)),
        _visit(t, seen_since, test_user.id, days_ago=10, follow_up_date=TODAY - timedelta(days=3)),
        _visit(t, seen_since, test_user.id, days_ago=1),  # came back after the follow-up was asked for
        _visit(t, booked, test_user.id, days_ago=10, follow_up_date=TODAY - timedelta(days=2)),
        _appointment(t, booked, test_user.id, when=TODAY + timedelta(days=4)),
        _visit(t, too_old, test_user.id, days_ago=90, follow_up_date=TODAY - timedelta(days=60)),
        _visit(t, inactive, test_user.id, days_ago=10, follow_up_date=TODAY - timedelta(days=3)),
    ])
    await db_session.commit()
    body = await _today(client, doctor_token)
    assert [(f["patient_name"], f["days_overdue"]) for f in body["follow_ups_due"]] == [("Overdue", 3), ("Soon", -2)]
    assert body["follow_ups_due"][0]["follow_up_notes"] == "Review the rash"


@pytest.mark.asyncio
async def test_alerts_use_only_the_latest_recent_visit_and_sort_by_urgency(client, doctor_token, db_session, test_tenant, test_user):
    t = test_tenant.id
    flagged, urgent, emergency, resolved, old, calm = (
        _patient(t, n) for n in ("Flagged", "Urgent", "Emergency", "Resolved", "Old", "Calm")
    )
    db_session.add_all([flagged, urgent, emergency, resolved, old, calm])
    await db_session.flush()
    db_session.add_all([
        _visit(t, flagged, test_user.id, days_ago=2, red_flags=["chest_pain", "breathlessness"]),
        _visit(t, urgent, test_user.id, days_ago=1, referral_urgency="urgent"),
        _visit(t, emergency, test_user.id, days_ago=5, referral_urgency="emergency", red_flags=["loss_of_consciousness"]),
        _visit(t, resolved, test_user.id, days_ago=6, red_flags=["persistent_vomiting"]),
        _visit(t, resolved, test_user.id, days_ago=1),  # the latest visit shows no warning, so none is raised
        _visit(t, old, test_user.id, days_ago=30, red_flags=["chest_pain"]),
        _visit(t, calm, test_user.id, days_ago=1, referral_urgency="routine"),
    ])
    await db_session.commit()
    alerts = (await _today(client, doctor_token))["alerts"]
    assert [a["patient_name"] for a in alerts] == ["Emergency", "Urgent", "Flagged"]
    assert alerts[2]["red_flags"] == ["chest_pain", "breathlessness"] and alerts[0]["referral_urgency"] == "emergency"


@pytest.mark.asyncio
async def test_plan_status_and_access(client, doctor_token, admin_access_token, db_session, test_tenant):
    test_tenant.plan, test_tenant.plan_expires_at = "pro", datetime.now(timezone.utc) + timedelta(days=10, hours=1)
    await db_session.commit()
    plan = (await _today(client, doctor_token))["plan"]
    assert (plan["plan"], plan["days_left"], plan["expired"]) == ("pro", 10, False)

    test_tenant.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()
    plan = (await _today(client, doctor_token))["plan"]
    assert plan["expired"] is True and plan["days_left"] is None

    assert (await client.get("/api/v1/dashboard/today")).status_code == 401
    assert (await client.get("/api/v1/dashboard/today", headers=H(admin_access_token))).status_code == 403  # platform users have no clinic
