"""Test-only gateway: a fake hosted page where a tester picks the outcome.

Enabled only with PAYMENT_FAKE_GATEWAY_ENABLED (refused at startup in production). It behaves like
a real gateway from the order service's point of view: it returns a redirect, and `verify` reports
the outcome the "customer" chose, so the same settle/fulfil code path is exercised.
"""

from decimal import Decimal

from app.core.config import settings
from app.modules.billing.gateways.base import CheckoutGateway, CheckoutSession, GatewayResult
from app.shared.models import BillingOrder

OUTCOMES = {"success": "paid", "failed": "failed", "cancelled": "cancelled"}


class FakeGateway(CheckoutGateway):
    name = "fake"

    async def create_checkout(self, order: BillingOrder) -> CheckoutSession:
        return CheckoutSession(
            redirect_url=f"{settings.FRONTEND_URL}/billing/fake-gateway?order={order.id}",
            gateway_session_id=f"FAKE-SESSION-{order.id[:8]}",
        )

    async def verify(self, order: BillingOrder) -> GatewayResult:
        outcome = (order.gateway_data or {}).get("fake_outcome")
        if outcome not in OUTCOMES:
            return GatewayResult(status="pending")
        return GatewayResult(
            status=OUTCOMES[outcome],
            gateway_txn_id=f"FAKE-{order.id[:8]}",
            amount=Decimal(order.amount),
            currency=order.currency,
            raw={"fake_outcome": outcome},
        )
