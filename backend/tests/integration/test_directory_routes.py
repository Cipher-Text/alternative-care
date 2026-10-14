"""Practitioner directory: opt-in listing, the verification and plan gates, and contact requests."""

import pytest


H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PROFILE = {"is_listed": True, "bio_en": "Homeopath with ten years of experience.", "languages": ["Bangla", "English"]}
REQUEST = {
    "patient_name": "Rahim Uddin",
    "patient_phone": "+8801711111111",
    "message": "Back pain for a month",
    "consent": True,
}


async def _go_public(client, db_session, tenant, token, **profile):
    tenant.plan = "plus"
    await db_session.commit()
    r = await client.put("/api/v1/directory/listing", json={**PROFILE, **profile}, headers=H(token))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_new_listing_is_private_and_explains_why(client, doctor_token, db_session, test_tenant):
    test_tenant.is_verified = False
    await db_session.commit()
    r = await client.get("/api/v1/directory/listing", headers=H(doctor_token))
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is False
    assert not body["eligibility"]["public"]
    assert {"not_listed", "not_verified", "not_in_plan", "no_profile_text"} <= set(body["eligibility"]["blockers"])


@pytest.mark.asyncio
async def test_listing_needs_verification_and_plan_and_bio(
    client, doctor_token, db_session, test_tenant
):
    # Free plan: listed + verified + bio is still not enough
    r = await client.put("/api/v1/directory/listing", json=PROFILE, headers=H(doctor_token))
    assert r.json()["eligibility"]["blockers"] == ["not_in_plan"]
    slug = r.json()["slug"]
    assert (await client.get(f"/api/v1/public/practitioners/{slug}")).status_code == 404

    # Plus plan but unverified: still hidden (paying never replaces verification)
    test_tenant.plan, test_tenant.is_verified = "plus", False
    await db_session.commit()
    assert (await client.get(f"/api/v1/public/practitioners/{slug}")).status_code == 404
    assert (await client.get("/api/v1/directory/listing", headers=H(doctor_token))).json()[
        "eligibility"
    ]["blockers"] == ["not_verified"]

    test_tenant.is_verified = True
    await db_session.commit()
    assert (await client.get(f"/api/v1/public/practitioners/{slug}")).status_code == 200

    # Opting out takes it down again
    await client.put("/api/v1/directory/listing", json={"is_listed": False}, headers=H(doctor_token))
    assert (await client.get(f"/api/v1/public/practitioners/{slug}")).status_code == 404


@pytest.mark.asyncio
async def test_expired_plan_removes_listing(client, doctor_token, db_session, test_tenant):
    from datetime import datetime, timedelta, timezone

    listing = await _go_public(client, db_session, test_tenant, doctor_token)
    assert (await client.get(f"/api/v1/public/practitioners/{listing['slug']}")).status_code == 200
    test_tenant.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()
    assert (await client.get(f"/api/v1/public/practitioners/{listing['slug']}")).status_code == 404


@pytest.mark.asyncio
async def test_public_profile_respects_privacy_choices(client, doctor_token, db_session, test_tenant):
    test_tenant.clinic_phone, test_tenant.clinic_whatsapp = "+8801811111111", "+8801822222222"
    test_tenant.consultation_fee = 50000  # paisa
    test_tenant.registration_number = "SECRET-REG-1"
    await db_session.commit()

    listing = await _go_public(client, db_session, test_tenant, doctor_token)
    pub = (await client.get(f"/api/v1/public/practitioners/{listing['slug']}")).json()
    assert pub["fee_bdt"] is None  # hidden by default
    assert pub["phone"] == "+8801811111111" and pub["whatsapp"] == "+8801822222222"
    assert pub["display_name"] == "Dr. Test Doctor"
    assert "SECRET-REG-1" not in str(pub)  # registration number never public

    await client.put(
        "/api/v1/directory/listing",
        json={"show_fee": True, "show_phone": False},
        headers=H(doctor_token),
    )
    pub = (await client.get(f"/api/v1/public/practitioners/{listing['slug']}")).json()
    assert pub["fee_bdt"] == 500
    assert pub["phone"] is None


@pytest.mark.asyncio
async def test_list_shows_every_visible_profile_with_no_minimum(client, doctor_token, db_session, test_tenant):
    # nobody is visible yet: an empty list, not a "not launched" state
    r = (await client.get("/api/v1/public/practitioners")).json()
    assert r == {"total": 0, "items": []}
    assert (await client.get("/api/v1/public/practitioners/slugs")).json() == []

    # one visible profile is shown as one
    await _go_public(client, db_session, test_tenant, doctor_token)
    r = (await client.get("/api/v1/public/practitioners")).json()
    assert r["total"] == 1 and "launched" not in r
    assert r["items"][0]["display_name"] == "Dr. Test Doctor"
    assert "bio_en" not in r["items"][0]
    assert len((await client.get("/api/v1/public/practitioners/slugs")).json()) == 1


@pytest.mark.asyncio
async def test_list_filters(client, doctor_token, db_session, test_tenant):
    await _go_public(client, db_session, test_tenant, doctor_token)
    ok = (await client.get("/api/v1/public/practitioners", params={"discipline": "homeopathy"})).json()
    assert ok["total"] == 1
    none = (await client.get("/api/v1/public/practitioners", params={"discipline": "unani"})).json()
    assert none["total"] == 0
    byname = (await client.get("/api/v1/public/practitioners", params={"q": "Test Doctor"})).json()
    assert byname["total"] == 1


@pytest.mark.asyncio
async def test_contact_request_flow_and_counting(client, doctor_token, db_session, test_tenant):
    listing = await _go_public(client, db_session, test_tenant, doctor_token)
    slug = listing["slug"]

    r = await client.post(f"/api/v1/public/practitioners/{slug}/requests", json=REQUEST)
    assert r.status_code == 201
    await client.post(f"/api/v1/public/practitioners/{slug}/events", json={"event_type": "whatsapp"})
    await client.post(f"/api/v1/public/practitioners/{slug}/events", json={"event_type": "call"})

    stats = (await client.get("/api/v1/directory/stats", headers=H(doctor_token))).json()
    assert (stats["requests"], stats["calls"], stats["whatsapp"], stats["open_requests"]) == (1, 1, 1, 1)

    reqs = (await client.get("/api/v1/directory/requests", headers=H(doctor_token))).json()
    assert reqs[0]["patient_name"] == "Rahim Uddin" and reqs[0]["status"] == "new"
    r = await client.patch(
        f"/api/v1/directory/requests/{reqs[0]['id']}", json={"status": "contacted"}, headers=H(doctor_token)
    )
    assert r.json()["status"] == "contacted"
    assert (await client.get("/api/v1/directory/stats", headers=H(doctor_token))).json()["open_requests"] == 0


@pytest.mark.asyncio
async def test_contact_request_validation(client, doctor_token, db_session, test_tenant):
    slug = (await _go_public(client, db_session, test_tenant, doctor_token))["slug"]
    url = f"/api/v1/public/practitioners/{slug}/requests"
    assert (await client.post(url, json={**REQUEST, "consent": False})).status_code == 422
    assert (await client.post(url, json={**REQUEST, "patient_phone": "abc"})).status_code == 422
    assert (await client.post(url, json={**REQUEST, "patient_name": "x"})).status_code == 422

    # Honeypot: looks successful to a bot, stores nothing
    assert (await client.post(url, json={**REQUEST, "website": "http://spam"})).status_code == 201
    assert (await client.get("/api/v1/directory/requests", headers=H(doctor_token))).json() == []

    # Doctor can turn requests off
    await client.put("/api/v1/directory/listing", json={"accepts_requests": False}, headers=H(doctor_token))
    assert (await client.post(url, json=REQUEST)).status_code == 409


@pytest.mark.asyncio
async def test_request_to_unlisted_practitioner_is_404(client, doctor_token, db_session, test_tenant):
    # Saved but free plan -> not public
    r = await client.put("/api/v1/directory/listing", json=PROFILE, headers=H(doctor_token))
    slug = r.json()["slug"]
    assert (await client.post(f"/api/v1/public/practitioners/{slug}/requests", json=REQUEST)).status_code == 404
    assert (
        await client.post(f"/api/v1/public/practitioners/{slug}/events", json={"event_type": "call"})
    ).status_code == 404


@pytest.mark.asyncio
async def test_requests_are_tenant_isolated(
    client, doctor_token, test_access_token_2, db_session, test_tenant
):
    slug = (await _go_public(client, db_session, test_tenant, doctor_token))["slug"]
    await client.post(f"/api/v1/public/practitioners/{slug}/requests", json=REQUEST)
    req_id = (await client.get("/api/v1/directory/requests", headers=H(doctor_token))).json()[0]["id"]

    other = await client.get("/api/v1/directory/requests", headers=H(test_access_token_2))
    assert other.json() == []
    r = await client.patch(
        f"/api/v1/directory/requests/{req_id}", json={"status": "closed"}, headers=H(test_access_token_2)
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_receptionist_and_anonymous_cannot_manage_listing(client, db_session, test_tenant):
    import uuid

    from app.core.security import create_access_token, get_password_hash
    from app.shared.models import User

    user = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec2@clinic.com",
        password_hash=get_password_hash("RecPass123"), role="receptionist", full_name="Rec",
        language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(
        {"sub": user.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": user.email, "plan": "free"}
    )
    assert (await client.get("/api/v1/directory/listing", headers=H(token))).status_code == 403
    assert (await client.get("/api/v1/directory/listing")).status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_verification_is_recorded(client, admin_access_token, doctor_token, db_session, test_tenant):
    test_tenant.is_verified = False
    await db_session.commit()

    r = await client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/verification",
        json={"verified": True, "note": "BHMS certificate and BHMEC registration checked"},
        headers=H(admin_access_token),
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True and r.json()["verified_at"]
    await db_session.refresh(test_tenant)
    assert test_tenant.verified_by and test_tenant.verification_note.startswith("BHMS")

    # A doctor cannot verify themselves
    r = await client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/verification", json={"verified": True}, headers=H(doctor_token)
    )
    assert r.status_code == 403

    r = await client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/verification", json={"verified": False}, headers=H(admin_access_token)
    )
    assert r.json()["is_verified"] is False and r.json()["verified_at"] is None
