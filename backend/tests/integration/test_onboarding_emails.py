"""Onboarding lifecycle emails: signup received, admin heads-up, account approved."""

from types import SimpleNamespace

import pytest
from httpx import AsyncClient


@pytest.fixture
def sent_emails(monkeypatch):
    """Capture every system email queued, regardless of which module queued it."""
    sent: list[dict] = []

    def _fake_delay(**kwargs):
        sent.append(kwargs)
        return SimpleNamespace(id="task-1")

    # Same Celery task object is shared by all modules, so patching it once covers them all.
    monkeypatch.setattr("app.core.system_email.send_system_email_task.delay", _fake_delay)
    return sent


def _register_payload(**overrides):
    payload = {
        "email": "onboard@test.com",
        "password": "SecurePass123",
        "full_name": "Dr. Onboard",
        "specializations": ["homeopathy"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_signup_sends_received_email_and_notifies_admins(
    client: AsyncClient, platform_admin, sent_emails
):
    response = await client.post(
        "/api/v1/auth/register", json=_register_payload(requested_plan="plus")
    )
    assert response.status_code == 201

    to_doctor = [e for e in sent_emails if e["recipient"] == "onboard@test.com"]
    assert {e["subject"] for e in to_doctor} == {
        "Verify your AltCare email address",
        "We received your AltCare registration",
    }

    to_admin = [e for e in sent_emails if e["recipient"] == platform_admin.email]
    assert len(to_admin) == 1
    assert "Dr. Onboard" in to_admin[0]["subject"]
    assert "Interested in plan: plus" in to_admin[0]["body_text"]


@pytest.mark.asyncio
async def test_signup_succeeds_even_if_email_queue_fails(client: AsyncClient, monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("broker down")

    monkeypatch.setattr("app.core.system_email.send_system_email_task.delay", _boom)

    # The pre-existing verification email is not best-effort, so only the new lifecycle
    # emails are exercised here: patch just the onboarding module's queue path.
    monkeypatch.setattr(
        "app.modules.auth.service.AuthService._send_verification_email",
        lambda self, user: _noop(),
    )
    response = await client.post("/api/v1/auth/register", json=_register_payload())
    assert response.status_code == 201


async def _noop():
    return None


@pytest.mark.asyncio
async def test_approval_emails_doctor_once(
    admin_client: AsyncClient, unapproved_tenant, unapproved_user, sent_emails
):
    first = await admin_client.post(f"/api/v1/admin/tenants/{unapproved_tenant.id}/approve")
    assert first.status_code == 200

    approved = [e for e in sent_emails if e["subject"] == "Your AltCare account is approved"]
    assert [e["recipient"] for e in approved] == [unapproved_user.email]

    # Approving an already-approved tenant must not email again.
    again = await admin_client.post(f"/api/v1/admin/tenants/{unapproved_tenant.id}/approve")
    assert again.status_code == 200
    approved = [e for e in sent_emails if e["subject"] == "Your AltCare account is approved"]
    assert len(approved) == 1


@pytest.mark.asyncio
async def test_bengali_user_gets_bengali_emails(
    client: AsyncClient, sent_emails
):
    response = await client.post(
        "/api/v1/auth/register", json=_register_payload(email="bn@test.com", language="bn")
    )
    assert response.status_code == 201
    subjects = {e["subject"] for e in sent_emails if e["recipient"] == "bn@test.com"}
    assert "আপনার AltCare নিবন্ধন পেয়েছি" in subjects
