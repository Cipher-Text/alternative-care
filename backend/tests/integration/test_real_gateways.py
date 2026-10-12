"""SSLCommerz and bKash checkout, against mocked provider responses (no network).

These prove OUR behaviour: what we send, that nothing is trusted from the browser, and that a payment is
fulfilled only when the provider confirms it for the right invoice and amount. They do not prove the
providers' real APIs behave as mocked; that needs a sandbox account."""

import json
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.modules.billing.gateways import available_gateways, bkash, sslcommerz
from app.modules.plans.service import PlansService
from app.shared.models import BillingOrder

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
GW = "/api/v1/billing/gateways"
PLUS = {"kind": "subscription", "plan_key": "plus", "period": "monthly"}


@pytest.fixture(autouse=True)
async def priced(db_session):
    rows = await PlansService(db_session).plan_rows()
    rows["plus"].price_monthly, rows["plus"].price_yearly = Decimal(1000), Decimal(10000)
    await db_session.commit()


# ---------------------------------------------------------------- SSLCommerz


@pytest.fixture
def ssl(monkeypatch):
    """SSLCommerz sandbox credentials plus a scriptable fake provider."""
    monkeypatch.setattr(settings, "SSLCOMMERZ_STORE_ID", "teststore")
    monkeypatch.setattr(settings, "SSLCOMMERZ_STORE_PASSWORD", "test-password-123")
    monkeypatch.setattr(settings, "SSLCOMMERZ_IS_SANDBOX", True)
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://api.example.test")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.example.test")
    state = {"refuse": False, "down": False, "trans": [], "validation": {}, "calls": [], "session_form": None}

    def handler(request: httpx.Request) -> httpx.Response:
        state["calls"].append(request.url.path)
        if state["down"]:
            raise httpx.ConnectError("provider down")
        path = request.url.path
        if path.endswith("gwprocess/v4/api.php"):
            state["session_form"] = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
            if state["refuse"]:
                return httpx.Response(200, json={"status": "FAILED", "failedreason": "Invalid Store"})
            return httpx.Response(200, json={"status": "SUCCESS", "sessionkey": "SESS1", "GatewayPageURL": "https://sandbox.sslcommerz.com/gw/pay?s=SESS1"})
        if path.endswith("merchantTransIDvalidationAPI.php"):
            return httpx.Response(200, json={"APIConnect": "DONE", "no_of_trans_found": len(state["trans"]), "element": state["trans"]})
        if path.endswith("validationserverAPI.php"):
            return httpx.Response(200, json=state["validation"])
        return httpx.Response(404)

    monkeypatch.setattr(sslcommerz, "_TRANSPORT", httpx.MockTransport(handler))
    return state


def _paid(state, order, amount="1000.00", currency="BDT", tran_id=None):
    state["trans"] = [{"status": "VALID", "tran_id": order["receipt_no"], "val_id": "VAL1", "amount": amount}]
    state["validation"] = {
        "status": "VALID", "tran_id": tran_id or order["receipt_no"], "val_id": "VAL1", "amount": amount,
        "currency_type": currency, "bank_tran_id": "BANK123", "card_type": "BKASH-bKash", "risk_level": "0",
    }


async def _start(client, token, gateway):
    r = await client.post("/api/v1/billing/checkout", json={**PLUS, "gateway": gateway}, headers=H(token))
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_sslcommerz_session_request_and_redirect(client, doctor_token, ssl, test_tenant):
    info = (await client.get("/api/v1/billing/subscription", headers=H(doctor_token))).json()
    assert info["gateways"] == ["sslcommerz"] and info["test_mode"] is True  # a sandbox is flagged

    body = await _start(client, doctor_token, "sslcommerz")
    order = body["order"]
    assert body["redirect_url"].startswith("https://sandbox.sslcommerz.com/") and order["status"] == "pending"
    sent = ssl["session_form"]
    assert sent["tran_id"] == order["receipt_no"] and sent["total_amount"] == "1000.00" and sent["currency"] == "BDT"
    assert sent["success_url"] == "https://api.example.test/api/v1/billing/gateways/sslcommerz/success"
    assert sent["ipn_url"].endswith("/sslcommerz/ipn") and sent["product_profile"] == "non-physical-goods"
    assert sent["store_id"] == "teststore" and sent["cus_name"] and sent["cus_email"] and sent["cus_phone"]
    assert "test-password-123" not in json.dumps(body)  # credentials never reach the browser


@pytest.mark.asyncio
async def test_sslcommerz_refusal_creates_no_order(client, doctor_token, ssl, db_session):
    ssl["refuse"] = True
    r = await client.post("/api/v1/billing/checkout", json={**PLUS, "gateway": "sslcommerz"}, headers=H(doctor_token))
    assert r.status_code == 502 and "Invalid Store" not in r.text
    assert (await db_session.execute(select(BillingOrder))).scalars().all() == []


@pytest.mark.asyncio
async def test_a_verified_payment_activates_the_plan_and_the_browser_is_sent_back(
    client, doctor_token, ssl, db_session, test_tenant
):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, order)
    r = await client.post(f"{GW}/sslcommerz/success", data={"tran_id": order["receipt_no"], "status": "VALID"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"https://app.example.test/billing/return?order={order['id']}"
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "plus"
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    assert row.status == "paid" and row.gateway_txn_id == "BANK123" and row.gateway_data["result"]["card_type"] == "BKASH-bKash"
    assert "test-password-123" not in json.dumps(row.gateway_data)


@pytest.mark.asyncio
async def test_a_forged_success_for_an_unpaid_order_changes_nothing(client, doctor_token, ssl, db_session, test_tenant):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    ssl["trans"] = []  # SSLCommerz has no payment for it
    r = await client.post(f"{GW}/sslcommerz/success", data={"tran_id": order["receipt_no"], "status": "VALID", "amount": "1000.00"}, follow_redirects=False)
    assert r.status_code == 303
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    await db_session.refresh(test_tenant)
    assert row.status == "pending" and test_tenant.plan == "free"


@pytest.mark.asyncio
async def test_wrong_amount_or_wrong_transaction_is_never_fulfilled(client, doctor_token, ssl, db_session, test_tenant):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, order, amount="1.00")  # paid far less than the price
    await client.post(f"{GW}/sslcommerz/success", data={"tran_id": order["receipt_no"]}, follow_redirects=False)
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    assert row.status == "failed" and row.fulfilled_at is None

    other = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, other, tran_id="SOMEONE-ELSES-TRAN")  # validation is for a different transaction
    await client.post(f"{GW}/sslcommerz/success", data={"tran_id": other["receipt_no"]}, follow_redirects=False)
    row2 = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == other["id"]))).scalar_one()
    assert row2.status == "pending" and row2.fulfilled_at is None
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "free"


@pytest.mark.asyncio
async def test_fail_and_cancel_returns(client, doctor_token, ssl, db_session):
    a = (await _start(client, doctor_token, "sslcommerz"))["order"]
    await client.post(f"{GW}/sslcommerz/cancel", data={"tran_id": a["receipt_no"]}, follow_redirects=False)
    b = (await _start(client, doctor_token, "sslcommerz"))["order"]
    await client.post(f"{GW}/sslcommerz/fail", data={"tran_id": b["receipt_no"]}, follow_redirects=False)
    statuses = {o.id: o.status for o in (await db_session.execute(select(BillingOrder))).scalars()}
    assert statuses == {a["id"]: "cancelled", b["id"]: "failed"}

    # a "cancel" for an order SSLCommerz actually has paid does not undo it: the provider's answer wins
    c = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, c)
    await client.post(f"{GW}/sslcommerz/cancel", data={"tran_id": c["receipt_no"]}, follow_redirects=False)
    assert (await db_session.execute(select(BillingOrder.status).where(BillingOrder.id == c["id"]))).scalar_one() == "paid"


@pytest.mark.asyncio
async def test_ipn_settles_even_if_the_browser_never_returns_and_repeats_are_harmless(
    client, doctor_token, ssl, db_session, test_tenant
):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, order)
    r = await client.post(f"{GW}/sslcommerz/ipn", data={"tran_id": order["receipt_no"], "val_id": "VAL1"})
    assert r.status_code == 200 and r.json() == {"ok": True}
    await db_session.refresh(test_tenant)
    expiry = test_tenant.plan_expires_at
    for _ in range(2):
        await client.post(f"{GW}/sslcommerz/ipn", data={"tran_id": order["receipt_no"]})
        await client.post(f"{GW}/sslcommerz/success", data={"tran_id": order["receipt_no"]}, follow_redirects=False)
    await db_session.refresh(test_tenant)
    assert test_tenant.plan_expires_at == expiry  # never granted twice


@pytest.mark.asyncio
async def test_a_lost_callback_is_recovered_when_the_return_page_checks(client, doctor_token, ssl, db_session, test_tenant):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    _paid(ssl, order)  # paid, but no callback ever arrived
    polled = (await client.get(f"/api/v1/billing/orders/{order['id']}", headers=H(doctor_token))).json()
    assert polled["status"] == "paid"
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "plus"


@pytest.mark.asyncio
async def test_provider_outage_changes_nothing_and_never_errors_the_browser(client, doctor_token, ssl, db_session):
    order = (await _start(client, doctor_token, "sslcommerz"))["order"]
    ssl["down"] = True
    r = await client.post(f"{GW}/sslcommerz/success", data={"tran_id": order["receipt_no"]}, follow_redirects=False)
    assert r.status_code == 303  # still sent back to the app
    ipn = await client.post(f"{GW}/sslcommerz/ipn", data={"tran_id": order["receipt_no"]})
    assert ipn.status_code == 503
    assert (await db_session.execute(select(BillingOrder.status).where(BillingOrder.id == order["id"]))).scalar_one() == "pending"


@pytest.mark.asyncio
async def test_unknown_orders_and_unconfigured_gateways(client, ssl, monkeypatch):
    r = await client.post(f"{GW}/sslcommerz/success", data={"tran_id": "AC-000000-NOPE00"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "https://app.example.test/billing"
    assert (await client.post(f"{GW}/sslcommerz/bogus", data={})).status_code == 404
    monkeypatch.setattr(settings, "SSLCOMMERZ_STORE_ID", "")
    assert (await client.post(f"{GW}/sslcommerz/success", data={"tran_id": "x"})).status_code == 404


# ---------------------------------------------------------------- bKash


@pytest.fixture
def bk(monkeypatch):
    for name, value in {"BKASH_APP_KEY": "appkey", "BKASH_APP_SECRET": "appsecret-xyz", "BKASH_USERNAME": "u", "BKASH_PASSWORD": "p"}.items():
        monkeypatch.setattr(settings, name, value)
    monkeypatch.setattr(settings, "BKASH_IS_SANDBOX", True)
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://api.example.test")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.example.test")
    monkeypatch.setitem(bkash._token, "value", None)
    monkeypatch.setitem(bkash._token, "expires", None)
    state = {"create_body": None, "execute": None, "status": None, "calls": [], "n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        state["calls"].append(path)
        body = json.loads(request.content or b"{}")
        if path.endswith("/token/grant"):
            return httpx.Response(200, json={"statusCode": "0000", "id_token": "TOKEN1", "expires_in": 3600})
        assert request.headers.get("authorization") == "TOKEN1" and request.headers.get("x-app-key") == "appkey"
        if path.endswith("/create"):
            state["create_body"] = body
            state["n"] += 1  # bKash gives every payment its own id
            pid = f"PID{state['n']}"
            return httpx.Response(200, json={"statusCode": "0000", "paymentID": pid, "bkashURL": f"https://sandbox.pay.bka.sh/?id={pid}"})
        if path.endswith("/execute"):
            return httpx.Response(200, json=state["execute"])
        if path.endswith("/payment/status"):
            return httpx.Response(200, json=state["status"])
        return httpx.Response(404)

    monkeypatch.setattr(bkash, "_TRANSPORT", httpx.MockTransport(handler))
    return state


def _completed(order, amount="1000.00", invoice=None):
    return {
        "statusCode": "0000", "paymentID": "PID1", "trxID": "TRX9", "transactionStatus": "Completed",
        "amount": amount, "currency": "BDT", "merchantInvoiceNumber": invoice or order["receipt_no"],
    }


@pytest.mark.asyncio
async def test_bkash_create_request_and_redirect(client, doctor_token, bk, db_session):
    body = await _start(client, doctor_token, "bkash")
    assert body["redirect_url"] == "https://sandbox.pay.bka.sh/?id=PID1"
    sent = bk["create_body"]
    assert sent["merchantInvoiceNumber"] == body["order"]["receipt_no"] and sent["amount"] == "1000.00"
    assert sent["currency"] == "BDT" and sent["intent"] == "sale"
    assert sent["callbackURL"] == "https://api.example.test/api/v1/billing/gateways/bkash/callback"
    assert "appsecret-xyz" not in json.dumps(body)
    # the token is reused, not granted again for every call
    await _start(client, doctor_token, "bkash")
    assert sum(1 for p in bk["calls"] if p.endswith("/token/grant")) == 1


@pytest.mark.asyncio
async def test_bkash_success_callback_executes_then_activates(client, doctor_token, bk, db_session, test_tenant):
    order = (await _start(client, doctor_token, "bkash"))["order"]
    bk["execute"] = _completed(order)
    r = await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "success"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith(f"/billing/return?order={order['id']}")
    assert any(p.endswith("/execute") for p in bk["calls"])
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    await db_session.refresh(test_tenant)
    assert row.status == "paid" and row.gateway_txn_id == "TRX9" and test_tenant.plan == "plus"


@pytest.mark.asyncio
async def test_bkash_callback_cannot_be_forged(client, doctor_token, bk, db_session, test_tenant):
    order = (await _start(client, doctor_token, "bkash"))["order"]
    # a "success" callback, but bKash refuses to execute and says nothing was paid
    bk["execute"] = {"statusCode": "2023", "statusMessage": "Insufficient Balance"}
    bk["status"] = {"statusCode": "0000", "paymentID": "PID1", "transactionStatus": "Initiated", "merchantInvoiceNumber": order["receipt_no"], "amount": "1000.00"}
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "success"}, follow_redirects=False)
    row = (await db_session.execute(select(BillingOrder).where(BillingOrder.id == order["id"]))).scalar_one()
    await db_session.refresh(test_tenant)
    assert row.status == "pending" and test_tenant.plan == "free"


@pytest.mark.asyncio
async def test_bkash_repeated_callback_after_execution_is_safe(client, doctor_token, bk, db_session, test_tenant):
    order = (await _start(client, doctor_token, "bkash"))["order"]
    bk["execute"] = _completed(order)
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "success"}, follow_redirects=False)
    await db_session.refresh(test_tenant)
    expiry = test_tenant.plan_expires_at
    # the second callback: execute now errors ("already completed"), the status query says Completed
    bk["execute"] = {"statusCode": "2062", "statusMessage": "Payment already completed"}
    bk["status"] = _completed(order)
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "success"}, follow_redirects=False)
    await db_session.refresh(test_tenant)
    assert test_tenant.plan_expires_at == expiry


@pytest.mark.asyncio
async def test_bkash_wrong_amount_or_invoice_is_not_fulfilled(client, doctor_token, bk, db_session, test_tenant):
    a = (await _start(client, doctor_token, "bkash"))["order"]
    bk["execute"] = _completed(a, amount="10.00")
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "success"}, follow_redirects=False)
    assert (await db_session.execute(select(BillingOrder.status).where(BillingOrder.id == a["id"]))).scalar_one() == "failed"

    b = (await _start(client, doctor_token, "bkash"))["order"]
    bk["execute"] = _completed(b, invoice="AC-999999-OTHER1")
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID2", "status": "success"}, follow_redirects=False)
    paid = [o for o in (await db_session.execute(select(BillingOrder))).scalars() if o.status == "paid"]
    assert paid == []
    await db_session.refresh(test_tenant)
    assert test_tenant.plan == "free"


@pytest.mark.asyncio
async def test_bkash_failure_cancel_and_unknown_payment(client, doctor_token, bk, db_session):
    a = (await _start(client, doctor_token, "bkash"))["order"]
    await client.get(f"{GW}/bkash/callback", params={"paymentID": "PID1", "status": "cancel"}, follow_redirects=False)
    assert (await db_session.execute(select(BillingOrder.status).where(BillingOrder.id == a["id"]))).scalar_one() == "cancelled"
    r = await client.get(f"{GW}/bkash/callback", params={"paymentID": "NOPE", "status": "success"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/billing")
    assert not any(p.endswith("/execute") for p in bk["calls"])  # an unknown payment is never executed


@pytest.mark.asyncio
async def test_bkash_return_page_check_recovers_a_lost_callback(client, doctor_token, bk, db_session, test_tenant):
    order = (await _start(client, doctor_token, "bkash"))["order"]
    bk["status"] = _completed(order)
    polled = (await client.get(f"/api/v1/billing/orders/{order['id']}", headers=H(doctor_token))).json()
    assert polled["status"] == "paid"


# ---------------------------------------------------------------- registry and safety


def test_available_gateways_follow_the_configuration(monkeypatch):
    assert available_gateways() == []
    monkeypatch.setattr(settings, "SSLCOMMERZ_STORE_ID", "s")
    monkeypatch.setattr(settings, "SSLCOMMERZ_STORE_PASSWORD", "p")
    assert available_gateways() == ["sslcommerz"]
    for name in ("BKASH_APP_KEY", "BKASH_APP_SECRET", "BKASH_USERNAME", "BKASH_PASSWORD"):
        monkeypatch.setattr(settings, name, "x")
    assert available_gateways() == ["sslcommerz", "bkash"]
    monkeypatch.setattr(settings, "BKASH_APP_SECRET", "")  # incomplete credentials are not "configured"
    assert available_gateways() == ["sslcommerz"]


@pytest.mark.asyncio
async def test_an_unconfigured_method_cannot_be_used(client, doctor_token):
    r = await client.post("/api/v1/billing/checkout", json={**PLUS, "gateway": "sslcommerz"}, headers=H(doctor_token))
    assert r.status_code == 400


def test_production_refuses_sandbox_gateways():
    from app.core.config import Settings

    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", SSLCOMMERZ_STORE_ID="live", SSLCOMMERZ_IS_SANDBOX=True)
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", BKASH_APP_KEY="k", BKASH_IS_SANDBOX=False,
                 BKASH_BASE_URL="https://tokenized.sandbox.bka.sh/v1.2.0-beta")
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", SSLCOMMERZ_STORE_ID="live", SSLCOMMERZ_IS_SANDBOX=False,
                 BACKEND_PUBLIC_URL="http://insecure.example")
