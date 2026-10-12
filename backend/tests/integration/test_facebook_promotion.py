"""Facebook profile promotion: a staff-run benefit where the doctor approves the exact post."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.modules.marketing.service import quarter_bounds
from app.shared.models import FacebookFeatureRequest

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
DRAFT = "Dr. Test Doctor treats families in Dhanmondi with classical homeopathy. Visit the AltCare profile."
POST_URL = "https://www.facebook.com/altcare/posts/12345"


async def _ready(client, db, tenant, token, plan="pro"):
    """A clinic with the benefit in its plan and a live public profile."""
    tenant.plan = plan
    await db.commit()
    r = await client.put(
        "/api/v1/directory/listing",
        json={"is_listed": True, "bio_en": "Homeopath with ten years of experience."},
        headers=H(token),
    )
    assert r.status_code == 200 and r.json()["eligibility"]["public"], r.text


async def _request(client, token, note="Please mention child health"):
    r = await client.post("/api/v1/marketing/facebook/requests", json={"doctor_note": note}, headers=H(token))
    return r


async def _to_approved(client, doctor_token, admin_token, req_id):
    d = await client.post(f"/api/v1/admin/marketing/facebook/{req_id}/draft", json={"draft_text": DRAFT}, headers=H(admin_token))
    assert d.status_code == 200 and d.json()["status"] == "drafted"
    a = await client.post(f"/api/v1/marketing/facebook/requests/{req_id}/approve", json={}, headers=H(doctor_token))
    assert a.status_code == 200 and a.json()["status"] == "approved"
    return a.json()


@pytest.mark.asyncio
async def test_free_plan_cannot_request(client, doctor_token, db_session, test_tenant):
    s = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()
    assert s["in_plan"] is False and "not_in_plan" in s["blockers"] and s["can_request"] is False
    r = await _request(client, doctor_token)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "feature_not_in_plan"


@pytest.mark.asyncio
async def test_profile_must_be_public_first(client, doctor_token, db_session, test_tenant):
    test_tenant.plan = "pro"
    await db_session.commit()
    s = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()
    assert s["in_plan"] is True and s["blockers"] == ["no_public_profile"]
    r = await _request(client, doctor_token)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "no_public_profile"


@pytest.mark.asyncio
async def test_full_workflow_to_posted(client, doctor_token, admin_access_token, db_session, test_tenant):
    await _ready(client, db_session, test_tenant, doctor_token)
    s = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()
    assert s["can_request"] is True and (s["limit"], s["used"], s["remaining"]) == (1, 0, 1)
    assert s["profile_path"].startswith("/practitioners/")

    req = (await _request(client, doctor_token)).json()
    assert req["status"] == "requested" and req["doctor_note"] == "Please mention child health"

    # staff queue shows it with the clinic and the live profile link
    queue = (await client.get("/api/v1/admin/marketing/facebook", params={"status": "requested"}, headers=H(admin_access_token))).json()
    assert queue[0]["id"] == req["id"] and queue[0]["tenant_name"] and queue[0]["profile_path"]

    approved = await _to_approved(client, doctor_token, admin_access_token, req["id"])
    assert approved["approved_text"] == DRAFT

    posted = await client.post(
        f"/api/v1/admin/marketing/facebook/{req['id']}/posted", json={"post_url": POST_URL}, headers=H(admin_access_token)
    )
    assert posted.status_code == 200 and posted.json()["status"] == "posted" and posted.json()["post_url"] == POST_URL

    after = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()
    assert (after["used"], after["remaining"]) == (1, 0)
    assert "quota_used" in after["blockers"] and after["open_request"] is None


@pytest.mark.asyncio
async def test_nothing_is_posted_without_the_doctors_approval(
    client, doctor_token, admin_access_token, db_session, test_tenant
):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    url = f"/api/v1/admin/marketing/facebook/{req['id']}/posted"

    r = await client.post(url, json={"post_url": POST_URL}, headers=H(admin_access_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_approved"  # not even drafted

    await client.post(f"/api/v1/admin/marketing/facebook/{req['id']}/draft", json={"draft_text": DRAFT}, headers=H(admin_access_token))
    r = await client.post(url, json={"post_url": POST_URL}, headers=H(admin_access_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_approved"  # drafted, not approved


@pytest.mark.asyncio
async def test_approved_text_cannot_be_changed_by_staff(
    client, doctor_token, admin_access_token, db_session, test_tenant
):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    await _to_approved(client, doctor_token, admin_access_token, req["id"])

    r = await client.post(
        f"/api/v1/admin/marketing/facebook/{req['id']}/draft",
        json={"draft_text": "A completely different promotional text that the doctor never saw."},
        headers=H(admin_access_token),
    )
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_draftable"
    row = (await db_session.execute(select(FacebookFeatureRequest).where(FacebookFeatureRequest.id == req["id"]))).scalar_one()
    assert row.approved_text == DRAFT


@pytest.mark.asyncio
async def test_doctor_can_send_a_draft_back(client, doctor_token, admin_access_token, db_session, test_tenant):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    await client.post(f"/api/v1/admin/marketing/facebook/{req['id']}/draft", json={"draft_text": DRAFT}, headers=H(admin_access_token))

    r = await client.post(
        f"/api/v1/marketing/facebook/requests/{req['id']}/changes", json={"comment": "Please remove the address"}, headers=H(doctor_token)
    )
    assert r.json()["status"] == "requested" and r.json()["doctor_comment"] == "Please remove the address"
    assert (await client.post(f"/api/v1/marketing/facebook/requests/{req['id']}/changes", json={"comment": "x"}, headers=H(doctor_token))).status_code == 422
    # approving something that is not a waiting draft is refused
    r = await client.post(f"/api/v1/marketing/facebook/requests/{req['id']}/approve", json={}, headers=H(doctor_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "nothing_to_approve"

    await _to_approved(client, doctor_token, admin_access_token, req["id"])  # staff redraft, then approve


@pytest.mark.asyncio
async def test_cancel_and_reject_give_the_quota_back(
    client, doctor_token, admin_access_token, db_session, test_tenant
):
    await _ready(client, db_session, test_tenant, doctor_token)  # Pro: 1 per quarter
    first = (await _request(client, doctor_token)).json()
    assert (await client.post(f"/api/v1/marketing/facebook/requests/{first['id']}/cancel", headers=H(doctor_token))).json()["status"] == "cancelled"

    second = (await _request(client, doctor_token)).json()
    r = await client.post(
        f"/api/v1/admin/marketing/facebook/{second['id']}/reject", json={"reason": "Profile needs more detail"}, headers=H(admin_access_token)
    )
    assert r.json()["status"] == "rejected" and r.json()["reject_reason"]

    third = await _request(client, doctor_token)
    assert third.status_code == 201  # both earlier ones gave the quota back
    # and now it is genuinely used up
    await client.post(f"/api/v1/marketing/facebook/requests/{third.json()['id']}/cancel", headers=H(doctor_token))


@pytest.mark.asyncio
async def test_one_open_request_at_a_time_and_quota_per_plan(
    client, doctor_token, admin_access_token, db_session, test_tenant
):
    await _ready(client, db_session, test_tenant, doctor_token, plan="enterprise")  # 3 per quarter
    first = await _request(client, doctor_token)
    assert first.status_code == 201
    second = await _request(client, doctor_token)
    assert second.status_code == 409 and second.json()["detail"]["code"] == "request_in_progress"

    # finish three in a row; the fourth hits the quarterly limit
    for _ in range(2):
        rid = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()["open_request"]["id"]
        await _to_approved(client, doctor_token, admin_access_token, rid)
        await client.post(f"/api/v1/admin/marketing/facebook/{rid}/posted", json={"post_url": POST_URL}, headers=H(admin_access_token))
        assert (await _request(client, doctor_token)).status_code == 201
    rid = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()["open_request"]["id"]
    await _to_approved(client, doctor_token, admin_access_token, rid)
    await client.post(f"/api/v1/admin/marketing/facebook/{rid}/posted", json={"post_url": POST_URL}, headers=H(admin_access_token))
    fourth = await _request(client, doctor_token)
    assert fourth.status_code == 403 and fourth.json()["detail"]["code"] == "plan_limit_reached"


@pytest.mark.asyncio
async def test_last_quarters_features_do_not_count(client, doctor_token, admin_access_token, db_session, test_tenant):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    await _to_approved(client, doctor_token, admin_access_token, req["id"])
    await client.post(f"/api/v1/admin/marketing/facebook/{req['id']}/posted", json={"post_url": POST_URL}, headers=H(admin_access_token))

    row = (await db_session.execute(select(FacebookFeatureRequest).where(FacebookFeatureRequest.id == req["id"]))).scalar_one()
    start, _ = quarter_bounds()
    row.created_at = start.replace(year=start.year - 1)  # a year ago
    await db_session.commit()
    s = (await client.get("/api/v1/marketing/facebook", headers=H(doctor_token))).json()
    assert s["used"] == 0 and s["can_request"] is True


def test_quarter_bounds():
    start, end = quarter_bounds(datetime(2026, 11, 15, tzinfo=timezone.utc))
    assert (start.month, start.day, end.year, end.month) == (10, 1, 2027, 1)
    start, end = quarter_bounds(datetime(2026, 3, 31, tzinfo=timezone.utc))
    assert (start.month, end.month) == (1, 4)


@pytest.mark.asyncio
async def test_post_link_must_be_a_facebook_https_url(client, doctor_token, admin_access_token, db_session, test_tenant):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    await _to_approved(client, doctor_token, admin_access_token, req["id"])
    url = f"/api/v1/admin/marketing/facebook/{req['id']}/posted"
    for bad in ("http://facebook.com/x", "https://evil.example.com/facebook.com", "javascript:alert(1)", "not a url"):
        assert (await client.post(url, json={"post_url": bad}, headers=H(admin_access_token))).status_code == 422, bad
    assert (await client.post(url, json={"post_url": "https://fb.watch/abc"}, headers=H(admin_access_token))).status_code == 200


@pytest.mark.asyncio
async def test_access_rules_and_clinic_isolation(
    client, doctor_token, test_access_token_2, admin_access_token, db_session, test_tenant
):
    await _ready(client, db_session, test_tenant, doctor_token)
    req = (await _request(client, doctor_token)).json()
    await client.post(f"/api/v1/admin/marketing/facebook/{req['id']}/draft", json={"draft_text": DRAFT}, headers=H(admin_access_token))

    # another clinic's doctor cannot approve, cancel or see it
    for path in ("approve", "cancel"):
        assert (await client.post(f"/api/v1/marketing/facebook/requests/{req['id']}/{path}", json={}, headers=H(test_access_token_2))).status_code == 404
    assert (await client.get("/api/v1/marketing/facebook", headers=H(test_access_token_2))).json()["history"] == []

    # doctors cannot use the staff queue
    assert (await client.get("/api/v1/admin/marketing/facebook", headers=H(doctor_token))).status_code == 403
    assert (await client.post(f"/api/v1/admin/marketing/facebook/{req['id']}/posted", json={"post_url": POST_URL}, headers=H(doctor_token))).status_code == 403

    import uuid

    from app.core.security import create_access_token, get_password_hash
    from app.shared.models import User

    rec = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec4@clinic.com",
        password_hash=get_password_hash("RecPass123"), role="receptionist", full_name="Rec",
        language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db_session.add(rec)
    await db_session.commit()
    token = create_access_token({"sub": rec.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": rec.email, "plan": "pro"})
    assert (await client.get("/api/v1/marketing/facebook", headers=H(token))).status_code == 403
