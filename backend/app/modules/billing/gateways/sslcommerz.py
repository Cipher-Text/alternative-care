"""SSLCommerz hosted checkout (cards, bKash, Nagad, Rocket and other mobile banking in one page).

Flow: create a session (server to server) and send the browser to GatewayPageURL; the customer pays;
SSLCommerz POSTs the browser back to our success/fail/cancel URLs and calls our IPN URL. We trust none
of those posts: we ask SSLCommerz about the transaction (by our receipt number) and, when it reports a
valid payment, confirm it with the validation API before reporting it paid.

Built from SSLCommerz's documented API and tested against mocked responses; it has not been run against a
real sandbox account yet."""

from decimal import Decimal, InvalidOperation

import httpx
import structlog
from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.billing.gateways.base import CheckoutGateway, CheckoutSession, Customer, GatewayResult
from app.shared.models import BillingOrder

logger = structlog.get_logger()

# Tests replace this with an httpx.MockTransport
_TRANSPORT: httpx.AsyncBaseTransport | None = None
_VALID = {"VALID", "VALIDATED"}
_FAILED = {"FAILED", "EXPIRED"}
_CANCELLED = {"CANCELLED"}


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0, transport=_TRANSPORT)


def _unavailable() -> HTTPException:
    return HTTPException(status.HTTP_502_BAD_GATEWAY, "The payment provider is not available right now. Try again.")


def is_configured() -> bool:
    return bool(settings.SSLCOMMERZ_STORE_ID and settings.SSLCOMMERZ_STORE_PASSWORD)


def _dec(value) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


class SslcommerzGateway(CheckoutGateway):
    name = "sslcommerz"
    label = "Card, bKash and mobile banking (SSLCommerz)"

    def __init__(self) -> None:
        self.sandbox = settings.SSLCOMMERZ_IS_SANDBOX
        host = "https://sandbox.sslcommerz.com" if self.sandbox else "https://securepay.sslcommerz.com"
        self.session_url = f"{host}/gwprocess/v4/api.php"
        self.query_url = f"{host}/validator/api/merchantTransIDvalidationAPI.php"
        self.validate_url = f"{host}/validator/api/validationserverAPI.php"
        self._auth = {"store_id": settings.SSLCOMMERZ_STORE_ID, "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD}

    def _callback(self, outcome: str) -> str:
        return f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}{settings.API_V1_PREFIX}/billing/gateways/sslcommerz/{outcome}"

    async def create_checkout(self, order: BillingOrder, customer: Customer) -> CheckoutSession:
        form = {
            **self._auth,
            "total_amount": f"{Decimal(order.amount):.2f}",
            "currency": order.currency,
            "tran_id": order.receipt_no,  # our receipt number is the transaction id (max 30 chars)
            "success_url": self._callback("success"),
            "fail_url": self._callback("fail"),
            "cancel_url": self._callback("cancel"),
            "ipn_url": self._callback("ipn"),
            "cus_name": customer.name[:50],
            "cus_email": customer.email,
            "cus_phone": customer.phone,
            "cus_add1": customer.address[:50],
            "cus_city": customer.city[:50],
            "cus_country": "Bangladesh",
            "shipping_method": "NO",
            "product_name": order.description[:100],
            "product_category": "Software subscription",
            "product_profile": "non-physical-goods",
            "value_a": order.id,  # echoed back; lets a callback find the order
        }
        try:
            async with _client() as client:
                response = await client.post(self.session_url, data=form)
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sslcommerz_session_error", error=type(exc).__name__)
            raise _unavailable() from exc
        url = data.get("GatewayPageURL")
        if data.get("status") != "SUCCESS" or not url:
            logger.warning("sslcommerz_session_refused", reason=str(data.get("failedreason"))[:200])
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The payment provider refused this payment. Try again or use another method.")
        return CheckoutSession(redirect_url=url, gateway_session_id=data.get("sessionkey"))

    async def verify(self, order: BillingOrder) -> GatewayResult:
        try:
            async with _client() as client:
                response = await client.get(
                    self.query_url, params={"tran_id": order.receipt_no, **self._auth, "format": "json"}
                )
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sslcommerz_query_error", error=type(exc).__name__)
            raise _unavailable() from exc

        elements = data.get("element") or ([data] if data.get("status") else [])
        if not elements:
            return GatewayResult(status="pending")  # the customer has not paid (yet)
        # If SSLCommerz reports several attempts for one transaction id, a valid one wins
        valid = next((e for e in elements if str(e.get("status", "")).upper() in _VALID), None)
        if valid is None:
            last = str(elements[-1].get("status", "")).upper()
            if last in _CANCELLED:
                return GatewayResult(status="cancelled", raw={"status": last})
            if last in _FAILED:
                return GatewayResult(status="failed", raw={"status": last})
            return GatewayResult(status="pending", raw={"status": last})
        return await self._validate(order, valid)

    async def _validate(self, order: BillingOrder, candidate: dict) -> GatewayResult:
        """Confirm a reported-valid payment with the validation API before calling it paid."""
        val_id = candidate.get("val_id")
        if not val_id:
            return GatewayResult(status="pending", raw={"status": "VALID_WITHOUT_VAL_ID"})
        try:
            async with _client() as client:
                response = await client.get(self.validate_url, params={"val_id": val_id, **self._auth, "format": "json"})
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sslcommerz_validate_error", error=type(exc).__name__)
            raise _unavailable() from exc
        if str(data.get("status", "")).upper() not in _VALID or data.get("tran_id") != order.receipt_no:
            return GatewayResult(status="pending", raw={"status": str(data.get("status")), "note": "validation did not confirm"})
        return GatewayResult(
            status="paid",
            gateway_txn_id=data.get("bank_tran_id") or val_id,
            amount=_dec(data.get("amount")),  # SSLCommerz reports the BDT amount here
            currency=str(data.get("currency_type") or "BDT"),
            raw={
                k: data.get(k)
                for k in ("status", "tran_id", "val_id", "bank_tran_id", "card_type", "risk_level", "risk_title")
            },
        )
