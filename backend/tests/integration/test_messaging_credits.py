"""Platform-owned SMS/email: plan allowance first, then purchased credits, never negative."""

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.core.credits import CreditService
from app.shared.models import TenantEntitlementOverride

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
SMS = {"recipient": "+8801711111111", "message": "Reminder: your appointment is tomorrow"}
EMAIL = {"recipient": "p@example.com", "subject": "Hello", "body_text": "Hi"}


@pytest.fixture
def platform_sms(monkeypatch):
    """SMS provider configured in the environment; the Celery send is stubbed."""
    monkeypatch.setattr(settings, "SMS_PROVIDER", "bulksmsbd")
    monkeypatch.setattr(settings, "BULKSMSBD_API_KEY", "test-key")
    monkeypatch.setattr(settings, "BULKSMSBD_SENDER_ID", "AltCare")
    sent = []
    stub = SimpleNamespace(delay=lambda **kw: sent.append(kw) or SimpleNamespace(id="task-1"))
    monkeypatch.setattr("app.modules.integration.routes.send_platform_sms_task", stub)
    return sent


@pytest.fixture
def platform_email(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    sent = []
    stub = SimpleNamespace(delay=lambda **kw: sent.append(kw) or SimpleNamespace(id="task-2"))
    monkeypatch.setattr("app.modules.integration.routes.send_platform_email_task", stub)
    return sent


async def _limit(db, tenant, key, value):
    db.add(TenantEntitlementOverride(tenant_id=tenant.id, entitlement_key=key, enabled=True, limit_value=value))
    await db.commit()


@pytest.mark.asyncio
async def test_allowance_is_used_first_then_blocked(client, doctor_token, db_session, test_tenant, platform_sms):
    await _limit(db_session, test_tenant, "monthly_sms", 2)
    for _ in range(2):
        assert (await client.post("/api/v1/integrations/send/sms", json=SMS, headers=H(doctor_token))).status_code == 200
    assert [s["source"] for s in platform_sms] == ["allowance", "allowance"]

    r = await client.post("/api/v1/integrations/send/sms", json=SMS, headers=H(doctor_token))
    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["code"] == "credits_exhausted" and detail["channel"] == "sms"
    assert detail["allowance_limit"] == 2 and detail["allowance_used"] == 2 and detail["purchased"] == 0
    assert len(platform_sms) == 2  # nothing queued for the blocked send


@pytest.mark.asyncio
async def test_purchased_credits_cover_overflow_and_are_ledgered(
    client, doctor_token, admin_access_token, db_session, test_tenant, platform_sms
):
    await _limit(db_session, test_tenant, "monthly_sms", 1)
    r = await client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/credits",
        json={"channel": "sms", "quantity": 2, "note": "Founding clinic gift"},
        headers=H(admin_access_token),
    )
    assert r.status_code == 200 and r.json()["purchased"] == 2

    results = [
        (await client.post("/api/v1/integrations/send/sms", json=SMS, headers=H(doctor_token))).status_code
        for _ in range(4)
    ]
    assert results == [200, 200, 200, 403]  # 1 allowance + 2 purchased, then exhausted
    assert [s["source"] for s in platform_sms] == ["allowance", "purchased", "purchased"]

    summary = (await client.get("/api/v1/billing/credits", headers=H(doctor_token))).json()
    sms = next(c for c in summary["channels"] if c["channel"] == "sms")
    assert (sms["allowance_used"], sms["allowance_remaining"], sms["purchased"]) == (1, 0, 0)
    assert summary["sms_available"] is True

    ledger = (await client.get("/api/v1/billing/credits/ledger", headers=H(doctor_token))).json()
    assert [(e["kind"], e["quantity"], e["balance_after"]) for e in ledger] == [
        ("use", -1, 0), ("use", -1, 1), ("adjustment", 2, 2),
    ]


@pytest.mark.asyncio
async def test_email_has_its_own_allowance(client, doctor_token, db_session, test_tenant, platform_sms, platform_email):
    await _limit(db_session, test_tenant, "monthly_sms", 0)
    await _limit(db_session, test_tenant, "monthly_email", 1)
    # SMS blocked, email still allowed: separate channels
    assert (await client.post("/api/v1/integrations/send/sms", json=SMS, headers=H(doctor_token))).status_code == 403
    assert (await client.post("/api/v1/integrations/send/email", json=EMAIL, headers=H(doctor_token))).status_code == 200
    assert (await client.post("/api/v1/integrations/send/email", json=EMAIL, headers=H(doctor_token))).status_code == 403
    assert platform_email[0]["reply_to"]  # replies go to the clinic, not a platform mailbox


@pytest.mark.asyncio
async def test_failed_send_is_refunded(db_session, test_tenant):
    await _limit(db_session, test_tenant, "monthly_sms", 1)
    svc = CreditService(db_session, test_tenant.id)
    await svc.grant("sms", 1, "purchase", reference="order-1")

    assert await svc.spend("sms") == "allowance"
    assert await svc.spend("sms") == "purchased"
    await svc.refund("sms", "purchased")
    await svc.refund("sms", "allowance")

    s = next(c for c in await svc.summary() if c.channel == "sms")
    assert (s.allowance_used, s.purchased) == (0, 1)


@pytest.mark.asyncio
async def test_unlimited_plan_never_touches_credits(client, doctor_token, platform_sms):
    for _ in range(3):
        assert (await client.post("/api/v1/integrations/send/sms", json=SMS, headers=H(doctor_token))).status_code == 200
    assert {s["source"] for s in platform_sms} == {"allowance"}


@pytest.mark.asyncio
async def test_admin_adjustment_rules(client, doctor_token, admin_access_token, test_tenant):
    url = f"/api/v1/admin/tenants/{test_tenant.id}/credits"
    ok = {"channel": "email", "quantity": 5, "note": "manual bank transfer"}
    assert (await client.post(url, json=ok, headers=H(admin_access_token))).status_code == 200
    # cannot remove more than the balance, needs a reason, cannot be zero
    assert (await client.post(url, json={**ok, "quantity": -6}, headers=H(admin_access_token))).status_code == 422
    assert (await client.post(url, json={**ok, "note": ""}, headers=H(admin_access_token))).status_code == 422
    assert (await client.post(url, json={**ok, "quantity": 0}, headers=H(admin_access_token))).status_code == 422
    # a clinic cannot give itself credits
    assert (await client.post(url, json=ok, headers=H(doctor_token))).status_code == 403
    assert (await client.post("/api/v1/admin/tenants/nope/credits", json=ok, headers=H(admin_access_token))).status_code == 404


@pytest.mark.asyncio
async def test_balances_are_per_clinic(client, doctor_token, test_access_token_2, admin_access_token, test_tenant):
    await client.post(
        f"/api/v1/admin/tenants/{test_tenant.id}/credits",
        json={"channel": "sms", "quantity": 10, "note": "gift"},
        headers=H(admin_access_token),
    )
    mine = (await client.get("/api/v1/billing/credits", headers=H(doctor_token))).json()
    other = (await client.get("/api/v1/billing/credits", headers=H(test_access_token_2))).json()
    assert next(c for c in mine["channels"] if c["channel"] == "sms")["purchased"] == 10
    assert next(c for c in other["channels"] if c["channel"] == "sms")["purchased"] == 0
    assert (await client.get("/api/v1/billing/credits/ledger", headers=H(test_access_token_2))).json() == []


@pytest.mark.asyncio
async def test_status_endpoint_never_leaks_secrets(client, admin_access_token, doctor_token, monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "bulksmsbd")
    monkeypatch.setattr(settings, "BULKSMSBD_API_KEY", "SUPER-SECRET-KEY")
    monkeypatch.setattr(settings, "BULKSMSBD_SENDER_ID", "AltCare")
    r = await client.get("/api/v1/admin/messaging/status", headers=H(admin_access_token))
    assert r.status_code == 200
    assert r.json()["sms"] == {"provider": "bulksmsbd", "configured": True}
    assert "SUPER-SECRET-KEY" not in r.text
    assert (await client.get("/api/v1/admin/messaging/status", headers=H(doctor_token))).status_code == 403


@pytest.mark.asyncio
async def test_unconfigured_platform_provider_reports_unavailable(client, doctor_token, monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "")
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "")
    s = (await client.get("/api/v1/billing/credits", headers=H(doctor_token))).json()
    assert s["sms_available"] is False and s["email_available"] is False
