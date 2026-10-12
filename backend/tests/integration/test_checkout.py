"""Checkout with the fake gateway: orders settle exactly once and only on a verified payment."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from dateutil.relativedelta import relativedelta
from sqlalchemy import select

from app.core.config import settings
from app.core.credits import CreditService
from app.modules.billing.gateways.base import GatewayResult
from app.modules.billing.orders import OrderService
from app.modules.plans.service import PlansService
from app.shared.models import BillingOrder

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
PLUS_MONTHLY = {"kind": "subscription", "gateway": "fake", "plan_key": "plus", "period": "monthly"}


@pytest.fixture
def fake_gateway(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_FAKE_GATEWAY_ENABLED", True)


@pytest.fixture
async def priced_plans(db_session):
    prices = {"plus": (1000, 10000), "pro": (2500, 25000)}
    rows = await PlansService(db_session).plan_rows()
    for key, (monthly, yearly) in prices.items():
        rows[key].price_monthly, rows[key].price_yearly = Decimal(monthly), Decimal(yearly)
    await db_session.commit()


async def _pay(client, token, body, outcome="success"):
    r = await client.post("/api/v1/billing/checkout", json=body, headers=H(token))
    assert r.status_code == 201, r.text
    order = r.json()["order"]
    done = await client.post(
        f"/api/v1/billing/fake-gateway/{order['id']}/complete", json={"outcome": outcome}, headers=H(token)
    )
    assert done.status_code == 200, done.text
    return done.json()


@pytest.mark.asyncio
async def test_subscription_options_come_from_the_server(client, doctor_token, fake_gateway, priced_plans):
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert info["applied_plan"] == "free" and info["gateways"] == ["fake"]
    by_key = {o["plan_key"]: o for o in info["options"]}
    assert set(by_key) == {"plus", "pro"}
    assert by_key["plus"]["action"] == "subscribe" and Decimal(by_key["plus"]["price_monthly"]) == 1000


@pytest.mark.asyncio
async def test_unpriced_plan_is_not_purchasable(client, doctor_token, fake_gateway):
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert {o["action"] for o in info["options"]} == {"unavailable"}
    r = await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_purchasable"


@pytest.mark.asyncio
async def test_no_gateway_means_no_checkout(client, doctor_token, priced_plans):
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert info["gateways"] == []
    assert (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))).status_code == 400


@pytest.mark.asyncio
async def test_paid_order_activates_plan_and_nothing_before(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    r = await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))
    assert r.status_code == 201
    order = r.json()["order"]
    assert order["status"] == "pending" and Decimal(order["amount"]) == 1000
    assert order["receipt_no"].startswith("AC-") and "/billing/fake-gateway?order=" in r.json()["redirect_url"]
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "free"  # starting checkout grants nothing

    paid = await _pay(client, doctor_token, PLUS_MONTHLY)
    assert paid["status"] == "paid" and paid["fulfilment"]["plan"] == "plus"
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "plus"
    expected = datetime.now(timezone.utc) + relativedelta(months=1)
    assert abs((test_tenant.plan_expires_at - expected).total_seconds()) < 60


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["failed", "cancelled"])
async def test_failed_or_cancelled_payment_grants_nothing(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans, outcome
):
    order = await _pay(client, doctor_token, PLUS_MONTHLY, outcome)
    assert order["status"] == outcome and order["fulfilment"] is None
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "free"
    # and the clinic can simply try again
    assert (await _pay(client, doctor_token, PLUS_MONTHLY))["status"] == "paid"


@pytest.mark.asyncio
async def test_settling_twice_never_grants_twice(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    order = await _pay(client, doctor_token, PLUS_MONTHLY)
    await db_session.refresh(test_tenant)
    first_expiry = test_tenant.plan_expires_at

    again = await client.post(
        f"/api/v1/billing/fake-gateway/{order['id']}/complete", json={"outcome": "success"}, headers=H(doctor_token)
    )
    assert again.json()["status"] == "paid"
    # a duplicate gateway notification, straight into the service
    stored = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    await OrderService(db_session).settle(
        stored.id, GatewayResult(status="paid", amount=stored.amount, currency=stored.currency)
    )
    await db_session.refresh(test_tenant)
    assert test_tenant.plan_expires_at == first_expiry


@pytest.mark.asyncio
async def test_renewal_extends_from_current_expiry(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    await _pay(client, doctor_token, PLUS_MONTHLY)
    await db_session.refresh(test_tenant)
    first = test_tenant.plan_expires_at

    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert next(o for o in info["options"] if o["plan_key"] == "plus")["action"] == "renew"
    renewed = await _pay(client, doctor_token, PLUS_MONTHLY)
    assert renewed["fulfilment"]["extended"] is True
    await db_session.refresh(test_tenant)
    assert test_tenant.plan_expires_at == first + relativedelta(months=1)


@pytest.mark.asyncio
async def test_upgrade_allowed_downgrade_blocked_while_active(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    await _pay(client, doctor_token, PLUS_MONTHLY)
    pro = {"kind": "subscription", "gateway": "fake", "plan_key": "pro", "period": "yearly"}
    assert (await _pay(client, doctor_token, pro))["fulfilment"]["plan"] == "pro"
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "pro"

    r = await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_allowed_now"


@pytest.mark.asyncio
async def test_plan_without_expiry_cannot_be_rebought(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    test_tenant.plan, test_tenant.plan_expires_at = "pro", None  # e.g. an admin-granted founding plan
    await db_session.commit()
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert next(o for o in info["options"] if o["plan_key"] == "pro")["action"] == "current"
    pro = {"kind": "subscription", "gateway": "fake", "plan_key": "pro", "period": "monthly"}
    assert (await client.post("/api/v1/billing/checkout", json=pro, headers=H(doctor_token))).status_code == 409


@pytest.mark.asyncio
async def test_expired_plan_can_be_bought_again(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    test_tenant.plan = "plus"
    test_tenant.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=3)
    await db_session.commit()
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert info["expired"] is True and info["applied_plan"] == "free"
    renewed = await _pay(client, doctor_token, PLUS_MONTHLY)
    assert renewed["fulfilment"]["extended"] is False  # starts today, not from the lapsed date
    await db_session.refresh(test_tenant)
    assert test_tenant.plan_expires_at > datetime.now(timezone.utc) + timedelta(days=27)


@pytest.mark.asyncio
async def test_wrong_amount_from_gateway_is_never_fulfilled(
    client, doctor_token, db_session, test_tenant, fake_gateway, priced_plans
):
    order = (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))).json()["order"]
    result = await OrderService(db_session).settle(
        order["id"], GatewayResult(status="paid", amount=Decimal("1"), currency="BDT")
    )
    assert result.status == "failed" and result.fulfilled_at is None
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "free"


@pytest.mark.asyncio
async def test_credit_pack_purchase_adds_credits(
    client, doctor_token, admin_access_token, db_session, test_tenant, fake_gateway
):
    r = await client.post(
        "/api/v1/admin/billing/packs",
        json={"channel": "sms", "quantity": 500, "price": 350, "name_en": "500 SMS"},
        headers=H(admin_access_token),
    )
    assert r.status_code == 201
    pack = r.json()

    packs = (await client.get("/api/v1/billing/packs", headers=H(doctor_token))).json()
    assert [p["id"] for p in packs] == [pack["id"]]

    order = await _pay(client, doctor_token, {"kind": "credit_pack", "gateway": "fake", "pack_id": pack["id"]})
    assert order["status"] == "paid" and order["fulfilment"] == {"channel": "sms", "added": 500, "balance": 500}
    assert (await CreditService(db_session, test_tenant.id).balance("sms")) == 500
    ledger = (await client.get("/api/v1/billing/credits/ledger", headers=H(doctor_token))).json()
    assert ledger[0]["kind"] == "purchase" and ledger[0]["reference"] == order["receipt_no"]

    # repricing the pack later does not rewrite what was already sold
    await client.patch(f"/api/v1/admin/billing/packs/{pack['id']}", json={"price": 999}, headers=H(admin_access_token))
    again = (await client.get(f"/api/v1/billing/orders/{order['id']}", headers=H(doctor_token))).json()
    assert Decimal(again["amount"]) == 350


@pytest.mark.asyncio
async def test_pack_rules(client, doctor_token, admin_access_token, fake_gateway):
    body = {"channel": "email", "quantity": 100, "price": 50, "name_en": "100 emails"}
    assert (await client.post("/api/v1/admin/billing/packs", json=body, headers=H(doctor_token))).status_code == 403
    assert (await client.post("/api/v1/admin/billing/packs", json={**body, "price": 0}, headers=H(admin_access_token))).status_code == 422
    pack = (await client.post("/api/v1/admin/billing/packs", json=body, headers=H(admin_access_token))).json()
    await client.patch(f"/api/v1/admin/billing/packs/{pack['id']}", json={"is_active": False}, headers=H(admin_access_token))
    assert (await client.get("/api/v1/billing/packs", headers=H(doctor_token))).json() == []
    r = await client.post(
        "/api/v1/billing/checkout",
        json={"kind": "credit_pack", "gateway": "fake", "pack_id": pack["id"]},
        headers=H(doctor_token),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_orders_are_private_to_their_clinic_and_doctors_only(
    client, doctor_token, test_access_token_2, db_session, test_tenant, fake_gateway, priced_plans
):
    order = await _pay(client, doctor_token, PLUS_MONTHLY)
    assert (await client.get(f"/api/v1/billing/orders/{order['id']}", headers=H(test_access_token_2))).status_code == 404
    assert (
        await client.post(
            f"/api/v1/billing/fake-gateway/{order['id']}/complete", json={"outcome": "failed"}, headers=H(test_access_token_2)
        )
    ).status_code == 404
    assert (await client.get("/api/v1/billing/orders", headers=H(test_access_token_2))).json() == []

    import uuid

    from app.core.security import create_access_token, get_password_hash
    from app.shared.models import User

    rec = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec3@clinic.com",
        password_hash=get_password_hash("RecPass123"), role="receptionist", full_name="Rec",
        language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db_session.add(rec)
    await db_session.commit()
    token = create_access_token(
        {"sub": rec.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": rec.email, "plan": "free"}
    )
    assert (await client.get("/api/v1/billing/orders", headers=H(token))).status_code == 403
    assert (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(token))).status_code == 403


@pytest.mark.asyncio
async def test_fake_endpoint_is_off_unless_enabled(client, doctor_token, fake_gateway, priced_plans, monkeypatch):
    order = (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))).json()["order"]
    monkeypatch.setattr(settings, "PAYMENT_FAKE_GATEWAY_ENABLED", False)
    r = await client.post(
        f"/api/v1/billing/fake-gateway/{order['id']}/complete", json={"outcome": "success"}, headers=H(doctor_token)
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_sees_all_orders_with_clinic_names(
    client, doctor_token, admin_access_token, test_tenant, fake_gateway, priced_plans
):
    await _pay(client, doctor_token, PLUS_MONTHLY)
    await _pay(client, doctor_token, PLUS_MONTHLY, "failed")
    allo = (await client.get("/api/v1/admin/billing/orders", headers=H(admin_access_token))).json()
    assert len(allo) == 2 and allo[0]["tenant_name"] and allo[0]["tenant_id"] == test_tenant.id
    paid = (await client.get("/api/v1/admin/billing/orders", params={"status": "paid"}, headers=H(admin_access_token))).json()
    assert [o["status"] for o in paid] == ["paid"]
    assert (await client.get("/api/v1/admin/billing/orders", headers=H(doctor_token))).status_code == 403


def test_production_refuses_the_fake_gateway():
    from app.core.config import Settings

    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", PAYMENT_FAKE_GATEWAY_ENABLED=True)


# ===== Housekeeping =====


@pytest.mark.asyncio
async def test_expiry_reminders_go_out_once_per_stage(db_session, test_tenant):
    from app.modules.billing.maintenance import send_expiry_reminders

    sent = []
    send = lambda *a: sent.append(a)  # noqa: E731
    now = datetime.now(timezone.utc)

    test_tenant.plan, test_tenant.plan_expires_at = "plus", now + timedelta(days=20)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, send) == 0  # too early

    test_tenant.plan_expires_at = now + timedelta(days=6)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, send) == 1
    assert await send_expiry_reminders(db_session, send) == 0  # not twice for the same stage
    assert "/billing" in sent[0][2] and "Plus plan ends" in sent[0][1]

    test_tenant.plan_expires_at = now + timedelta(hours=20)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, send) == 1  # the 1-day reminder
    assert len(sent) == 2

    # renewing resets the stage so the next period is reminded again
    test_tenant.plan_reminder_stage = 0
    test_tenant.plan_expires_at = now + timedelta(days=5)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, send) == 1


@pytest.mark.asyncio
async def test_free_and_lapsed_plans_get_no_reminders(db_session, test_tenant):
    from app.modules.billing.maintenance import send_expiry_reminders

    sent = []
    now = datetime.now(timezone.utc)
    test_tenant.plan, test_tenant.plan_expires_at = "free", now + timedelta(days=2)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, lambda *a: sent.append(a)) == 0
    test_tenant.plan, test_tenant.plan_expires_at = "plus", now - timedelta(days=1)
    await db_session.commit()
    assert await send_expiry_reminders(db_session, lambda *a: sent.append(a)) == 0
    assert sent == []


@pytest.mark.asyncio
async def test_abandoned_orders_expire_but_recent_ones_do_not(
    client, doctor_token, db_session, fake_gateway, priced_plans
):
    from app.modules.billing.maintenance import expire_stale_orders

    old = (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))).json()["order"]
    fresh = (await client.post("/api/v1/billing/checkout", json=PLUS_MONTHLY, headers=H(doctor_token))).json()["order"]
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == old["id"]))).scalar_one()
    row.created_at = datetime.now(timezone.utc) - timedelta(hours=30)
    await db_session.commit()

    assert await expire_stale_orders(db_session) == 1
    statuses = {o["id"]: o["status"] for o in (await client.get("/api/v1/billing/orders", headers=H(doctor_token))).json()}
    assert statuses == {old["id"]: "expired", fresh["id"]: "pending"}
