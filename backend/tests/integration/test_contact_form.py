"""Public contact form and the staff inbox."""

import pytest
from sqlalchemy import select

from app.shared.models import ContactMessage

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
OK = {
    "topic": "enterprise",
    "name": "Rahim Chowdhury",
    "email": "rahim@hospital.example",
    "organisation": "City Homeo Hospital",
    "message": "We run three branches and need a quote for 12 doctors.",
    "consent": True,
}


@pytest.mark.asyncio
async def test_anyone_can_send_a_message_and_staff_see_it(client, admin_access_token, db_session):
    r = await client.post("/api/v1/public/contact", json=OK)  # no login
    assert r.status_code == 201

    inbox = (await client.get("/api/v1/admin/contact", headers=H(admin_access_token))).json()
    assert len(inbox) == 1
    m = inbox[0]
    assert (m["topic"], m["name"], m["status"]) == ("enterprise", "Rahim Chowdhury", "new")
    assert m["organisation"] == "City Homeo Hospital" and m["email"] == "rahim@hospital.example"

    done = await client.patch(f"/api/v1/admin/contact/{m['id']}", json={"status": "handled"}, headers=H(admin_access_token))
    assert done.json()["status"] == "handled" and done.json()["handled_at"]
    new_only = (await client.get("/api/v1/admin/contact", params={"status": "new"}, headers=H(admin_access_token))).json()
    assert new_only == []
    reopened = await client.patch(f"/api/v1/admin/contact/{m['id']}", json={"status": "new"}, headers=H(admin_access_token))
    assert reopened.json()["handled_at"] is None


@pytest.mark.asyncio
async def test_phone_alone_is_enough_but_something_is_required(client):
    phone_only = {k: v for k, v in OK.items() if k != "email"} | {"phone": "01711 111 111"}
    assert (await client.post("/api/v1/public/contact", json=phone_only)).status_code == 201
    neither = {k: v for k, v in OK.items() if k != "email"}
    assert (await client.post("/api/v1/public/contact", json=neither)).status_code == 422


@pytest.mark.asyncio
async def test_validation(client):
    url = "/api/v1/public/contact"
    assert (await client.post(url, json={**OK, "consent": False})).status_code == 422
    assert (await client.post(url, json={**OK, "email": "not-an-email"})).status_code == 422
    assert (await client.post(url, json={**OK, "phone": "abc"})).status_code == 422
    assert (await client.post(url, json={**OK, "message": "short"})).status_code == 422
    assert (await client.post(url, json={**OK, "name": "x"})).status_code == 422
    assert (await client.post(url, json={**OK, "topic": "spam"})).status_code == 422


@pytest.mark.asyncio
async def test_honeypot_looks_successful_but_stores_nothing(client, db_session):
    assert (await client.post("/api/v1/public/contact", json={**OK, "website": "http://spam.example"})).status_code == 201
    assert (await db_session.execute(select(ContactMessage))).scalars().all() == []


@pytest.mark.asyncio
async def test_inbox_is_admin_only(client, doctor_token, admin_access_token):
    await client.post("/api/v1/public/contact", json=OK)
    assert (await client.get("/api/v1/admin/contact", headers=H(doctor_token))).status_code == 403
    assert (await client.get("/api/v1/admin/contact")).status_code in (401, 403)
    inbox = (await client.get("/api/v1/admin/contact", headers=H(admin_access_token))).json()
    assert (await client.patch(f"/api/v1/admin/contact/{inbox[0]['id']}", json={"status": "handled"}, headers=H(doctor_token))).status_code == 403
    assert (await client.patch("/api/v1/admin/contact/nope", json={"status": "handled"}, headers=H(admin_access_token))).status_code == 404
