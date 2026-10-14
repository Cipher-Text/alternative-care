"""The platform work queue: what staff need to act on, across every clinic."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.security import create_access_token, get_password_hash
from app.shared.models import BillingOrder, ContactMessage, FacebookFeatureRequest, PractitionerListing, Tenant, User

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
URL = "/api/v1/admin/dashboard/queue"
NOW = datetime.now(timezone.utc)


def _tenant(name, **extra):
    uid = uuid.uuid4().hex[:8]
    return Tenant(
        id=str(uuid.uuid4()), name=name, email=f"{uid}@clinic.test", clinic_name=name, specializations=["homeopathy"],
        is_verified=extra.pop("is_verified", True), is_approved=extra.pop("is_approved", True), is_active=True,
        plan=extra.pop("plan", "free"), **extra,
    )


def _listing(tenant, listed=True):
    return PractitionerListing(
        id=str(uuid.uuid4()), tenant_id=tenant.id, user_id=str(uuid.uuid4()), slug=f"dr-{uuid.uuid4().hex[:8]}", is_listed=listed,
        listed_at=NOW - timedelta(days=2) if listed else None,
    )


def _order(tenant, status, amount=1000, paid_at=None, created_at=None):
    return BillingOrder(
        id=str(uuid.uuid4()), receipt_no=f"AC-T-{uuid.uuid4().hex[:6].upper()}", tenant_id=tenant.id, payer_user_id="u", payer_name="Payer",
        kind="subscription", plan_key="plus", period="monthly", description="Plus plan", amount=Decimal(amount), status=status,
        gateway="manual", paid_at=paid_at, created_at=created_at or NOW,
    )


async def _queue(client, token):
    r = await client.get(URL, headers=H(token))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_an_empty_platform_has_empty_queues(client, admin_access_token):
    q = await _queue(client, admin_access_token)
    assert (q["pending_approvals_total"], q["pending_approvals"], q["verification_waiting_total"], q["plans_expiring_total"]) == (0, [], 0, 0)
    assert q["contact"] == {"new": 0, "by_topic": {}, "latest": []}
    assert q["marketing"] == {"needs_draft": 0, "waiting_for_doctor": 0, "ready_to_post": 0}
    assert float(q["revenue"]["this_month"]) == 0 and q["revenue"]["failed_last_7_days"] == 0


@pytest.mark.asyncio
async def test_pending_approvals_show_the_doctor_oldest_first(client, admin_access_token, db_session):
    older, newer, approved = _tenant("Older Clinic", is_approved=False), _tenant("Newer Clinic", is_approved=False), _tenant("Approved Clinic")
    older.created_at, newer.created_at = NOW - timedelta(days=5), NOW - timedelta(days=1)
    db_session.add_all([older, newer, approved])
    await db_session.flush()
    db_session.add(User(id=str(uuid.uuid4()), tenant_id=older.id, email="dr.old@clinic.test", password_hash=get_password_hash("Test@1234"),
                        full_name="Dr. Older", role="doctor", is_active=True))
    await db_session.commit()
    q = await _queue(client, admin_access_token)
    assert q["pending_approvals_total"] == 2
    assert [(t["clinic_name"], t["doctor_name"]) for t in q["pending_approvals"]] == [("Older Clinic", "Dr. Older"), ("Newer Clinic", None)]


@pytest.mark.asyncio
async def test_verification_queue_is_clinics_that_listed_themselves_but_are_not_verified(client, admin_access_token, db_session):
    waiting = _tenant("Waiting Clinic", is_verified=False)
    verified = _tenant("Verified Clinic")
    unlisted = _tenant("Unlisted Clinic", is_verified=False)
    unapproved = _tenant("Unapproved Clinic", is_verified=False, is_approved=False)
    db_session.add_all([waiting, verified, unlisted, unapproved])
    await db_session.flush()
    db_session.add_all([_listing(waiting), _listing(verified), _listing(unlisted, listed=False), _listing(unapproved)])
    await db_session.commit()
    q = await _queue(client, admin_access_token)
    assert q["verification_waiting_total"] == 1
    assert [t["clinic_name"] for t in q["verification_waiting"]] == ["Waiting Clinic"]


@pytest.mark.asyncio
async def test_contact_and_facebook_queues(client, admin_access_token, db_session):
    for topic, status, name in (("enterprise", "new", "Ent One"), ("enterprise", "new", "Ent Two"), ("billing", "new", "Bill"), ("general", "handled", "Done")):
        db_session.add(ContactMessage(id=str(uuid.uuid4()), topic=topic, name=name, email="x@y.test", message="Hello there, please call.", status=status))
    clinics = [_tenant(f"FB Clinic {i}") for i in range(4)]
    db_session.add_all(clinics)
    await db_session.flush()
    for clinic, status in zip(clinics, ("requested", "drafted", "approved", "posted")):
        db_session.add(FacebookFeatureRequest(id=str(uuid.uuid4()), tenant_id=clinic.id, status=status, requested_by="u"))
    await db_session.commit()
    q = await _queue(client, admin_access_token)
    assert q["contact"]["new"] == 3 and q["contact"]["by_topic"] == {"enterprise": 2, "billing": 1}
    assert {m["name"] for m in q["contact"]["latest"]} == {"Ent One", "Ent Two", "Bill"}  # the handled one is not listed
    assert q["marketing"] == {"needs_draft": 1, "waiting_for_doctor": 1, "ready_to_post": 1}  # a posted one needs nothing


@pytest.mark.asyncio
async def test_revenue_and_checkout_problems(client, admin_access_token, db_session):
    clinic = _tenant("Paying Clinic")
    db_session.add(clinic)
    await db_session.flush()
    month_start = NOW.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = month_start - timedelta(days=3)
    db_session.add_all([
        _order(clinic, "paid", 1000, paid_at=month_start + timedelta(seconds=1)),
        _order(clinic, "paid", 2500, paid_at=month_start + timedelta(seconds=2)),
        _order(clinic, "paid", 700, paid_at=last_month),
        _order(clinic, "failed", 300, created_at=NOW - timedelta(days=1)),
        _order(clinic, "pending", 300, created_at=NOW - timedelta(hours=5)),  # abandoned
        _order(clinic, "pending", 300, created_at=NOW - timedelta(minutes=10)),  # still being paid
    ])
    await db_session.commit()
    r = (await _queue(client, admin_access_token))["revenue"]
    assert (float(r["this_month"]), float(r["last_month"]), r["paid_orders_this_month"]) == (3500.0, 700.0, 2)
    assert (r["failed_last_7_days"], r["abandoned_checkouts"]) == (1, 1)


@pytest.mark.asyncio
async def test_plan_renewals_and_growth(client, admin_access_token, db_session):
    soon = _tenant("Soon Clinic", plan="pro", plan_expires_at=NOW + timedelta(days=5, hours=1))
    sooner = _tenant("Sooner Clinic", plan="plus", plan_expires_at=NOW + timedelta(days=2, hours=1))
    later = _tenant("Later Clinic", plan="pro", plan_expires_at=NOW + timedelta(days=40))
    never = _tenant("Lifetime Clinic", plan="enterprise")
    free = _tenant("Free Clinic", plan="free")
    lapsed = _tenant("Lapsed Clinic", plan="pro", plan_expires_at=NOW - timedelta(days=2))
    long_gone = _tenant("Long Gone Clinic", plan="pro", plan_expires_at=NOW - timedelta(days=30))
    db_session.add_all([soon, sooner, later, never, free, lapsed, long_gone])
    await db_session.commit()
    q = await _queue(client, admin_access_token)
    assert q["plans_expiring_total"] == 2
    assert [(p["clinic_name"], p["days_left"]) for p in q["plans_expiring"]] == [("Sooner Clinic", 2), ("Soon Clinic", 5)]
    assert q["recently_expired"] == 1
    assert q["growth"]["new_tenants_this_month"] == 7 and q["growth"]["new_tenants_last_month"] == 0


@pytest.mark.asyncio
async def test_who_can_see_the_queue(client, admin_access_token, doctor_token, db_session):
    assert (await client.get(URL)).status_code == 401
    assert (await client.get(URL, headers=H(doctor_token))).status_code == 403
    operator = User(id=str(uuid.uuid4()), tenant_id=None, email="op@altcare.test", password_hash=get_password_hash("Test@1234"),
                    full_name="Operator", role="operator", is_active=True, is_email_verified=True)
    db_session.add(operator)
    await db_session.commit()
    token = create_access_token({"sub": operator.id, "tenant_id": None, "role": "operator", "email": operator.email, "plan": None})
    assert (await client.get(URL, headers=H(token))).status_code == 200  # read-only staff can see it
