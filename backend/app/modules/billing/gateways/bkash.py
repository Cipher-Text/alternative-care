"""bKash tokenized checkout for AltCare's own subscriptions and credit packs.

Flow: get a token, create a payment, send the browser to bkashURL; the customer pays in bKash; bKash
redirects the browser to our callback with `paymentID` and a `status`. Only on `success` do we call
Execute (which captures the money); we then rely on bKash's own response, never on the callback's
claim. `verify` (used when the return page polls) queries the payment's status.

This is a separate client from `app/modules/payment/bkash_service.py` (a clinic collecting from its
patients) so platform billing cannot be affected by that feature.

Built from bKash's documented tokenized-checkout API and tested against mocked responses; it has not
been run against a real sandbox account yet."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import httpx
import structlog
from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.billing.gateways.base import CheckoutGateway, CheckoutSession, Customer, GatewayResult
from app.shared.models import BillingOrder

logger = structlog.get_logger()

_TRANSPORT: httpx.AsyncBaseTransport | None = None  # tests replace this with an httpx.MockTransport
_token: dict = {"value": None, "expires": None}  # shared across requests so we do not grant a token each time


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=20.0, transport=_TRANSPORT)


def _unavailable() -> HTTPException:
    return HTTPException(status.HTTP_502_BAD_GATEWAY, "The payment provider is not available right now. Try again.")


def is_configured() -> bool:
    return all([settings.BKASH_APP_KEY, settings.BKASH_APP_SECRET, settings.BKASH_USERNAME, settings.BKASH_PASSWORD])


def _dec(value) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


class BkashCheckoutGateway(CheckoutGateway):
    name = "bkash"
    label = "bKash"

    def __init__(self) -> None:
        self.sandbox = settings.BKASH_IS_SANDBOX
        self.base = settings.BKASH_BASE_URL.rstrip("/")

    async def _token(self) -> str:
        now = datetime.now(timezone.utc)
        if _token["value"] and _token["expires"] and now < _token["expires"]:
            return _token["value"]
        try:
            async with _client() as client:
                response = await client.post(
                    f"{self.base}/tokenized/checkout/token/grant",
                    json={"app_key": settings.BKASH_APP_KEY, "app_secret": settings.BKASH_APP_SECRET},
                    headers={"username": settings.BKASH_USERNAME, "password": settings.BKASH_PASSWORD},
                )
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("bkash_token_error", error=type(exc).__name__)
            raise _unavailable() from exc
        token = data.get("id_token")
        if not token:
            logger.warning("bkash_token_refused", message=str(data.get("statusMessage"))[:200])
            raise _unavailable()
        _token["value"] = token
        _token["expires"] = now + timedelta(seconds=max(60, int(data.get("expires_in", 3600)) - 300))
        return token

    async def _post(self, path: str, body: dict) -> dict:
        headers = {"Authorization": await self._token(), "X-APP-Key": settings.BKASH_APP_KEY}
        try:
            async with _client() as client:
                response = await client.post(f"{self.base}/tokenized/checkout/{path}", json=body, headers=headers)
            return response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("bkash_request_error", path=path, error=type(exc).__name__)
            raise _unavailable() from exc

    async def create_checkout(self, order: BillingOrder, customer: Customer) -> CheckoutSession:
        data = await self._post(
            "create",
            {
                "mode": "0011",
                "payerReference": customer.phone or "AltCare",
                "callbackURL": f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}{settings.API_V1_PREFIX}/billing/gateways/bkash/callback",
                "amount": f"{Decimal(order.amount):.2f}",
                "currency": order.currency,
                "intent": "sale",
                "merchantInvoiceNumber": order.receipt_no,
            },
        )
        if data.get("statusCode") != "0000" or not data.get("bkashURL") or not data.get("paymentID"):
            logger.warning("bkash_create_refused", message=str(data.get("statusMessage"))[:200])
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The payment provider refused this payment. Try again or use another method.")
        return CheckoutSession(redirect_url=data["bkashURL"], gateway_session_id=data["paymentID"])

    def _result(self, order: BillingOrder, data: dict) -> GatewayResult:
        """Turn an Execute/Query response into a result. Only 'Completed' for OUR invoice is paid."""
        state = str(data.get("transactionStatus") or "")
        if state == "Completed":
            if data.get("merchantInvoiceNumber") != order.receipt_no:
                logger.error("bkash_invoice_mismatch", order_id=order.id)
                return GatewayResult(status="failed", raw={"note": "invoice number did not match"})
            return GatewayResult(
                status="paid",
                gateway_txn_id=data.get("trxID"),
                amount=_dec(data.get("amount")),
                currency=str(data.get("currency") or "BDT"),
                raw={k: data.get(k) for k in ("paymentID", "trxID", "transactionStatus", "merchantInvoiceNumber")},
            )
        if state in ("Failed", "Cancelled", "Expired"):
            return GatewayResult(status="cancelled" if state == "Cancelled" else "failed", raw={"transactionStatus": state})
        return GatewayResult(status="pending", raw={"transactionStatus": state})

    def _payment_id(self, order: BillingOrder) -> str | None:
        return (order.gateway_data or {}).get("session_id")

    async def verify(self, order: BillingOrder) -> GatewayResult:
        payment_id = self._payment_id(order)
        if not payment_id:
            return GatewayResult(status="pending")
        data = await self._post("payment/status", {"paymentID": payment_id})
        if data.get("statusCode") not in (None, "0000"):
            return GatewayResult(status="pending", raw={"statusCode": data.get("statusCode")})
        return self._result(order, data)

    async def handle_return(self, order: BillingOrder, params: dict) -> GatewayResult:
        outcome = str(params.get("status") or "").lower()
        if outcome == "cancel":
            return GatewayResult(status="cancelled", raw={"callback_status": "cancel"})
        if outcome == "failure":
            return GatewayResult(status="failed", raw={"callback_status": "failure"})
        payment_id = self._payment_id(order)
        if outcome != "success" or not payment_id:
            return await self.verify(order)  # an unknown status: ask bKash, trust nothing
        # The customer authorised the payment in bKash: capture it, then rely on bKash's answer
        executed = await self._post("execute", {"paymentID": payment_id})
        if executed.get("statusCode") == "0000":
            return self._result(order, executed)
        # Already executed (a repeated callback), or the capture failed: the status query tells which
        return await self.verify(order)
