"""Checkout gateways available to this deployment, chosen from the environment."""

from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.billing.gateways import bkash, sslcommerz
from app.modules.billing.gateways.base import CheckoutGateway, CheckoutSession, Customer, GatewayResult
from app.modules.billing.gateways.bkash import BkashCheckoutGateway
from app.modules.billing.gateways.fake import FakeGateway
from app.modules.billing.gateways.sslcommerz import SslcommerzGateway


def available_gateways() -> list[str]:
    """Names usable right now, best first: real providers, then the test gateway if enabled."""
    names = []
    if sslcommerz.is_configured():
        names.append("sslcommerz")
    if bkash.is_configured():
        names.append("bkash")
    if settings.PAYMENT_FAKE_GATEWAY_ENABLED:
        names.append("fake")
    return names


def get_gateway(name: str) -> CheckoutGateway:
    if name == "sslcommerz" and sslcommerz.is_configured():
        return SslcommerzGateway()
    if name == "bkash" and bkash.is_configured():
        return BkashCheckoutGateway()
    if name == "fake" and settings.PAYMENT_FAKE_GATEWAY_ENABLED:
        return FakeGateway()
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "This payment method is not available")


def is_test_mode() -> bool:
    """True when any usable gateway moves no real money (fake or a provider sandbox): the UI says so."""
    return any(get_gateway(n).sandbox for n in available_gateways())


__all__ = [
    "CheckoutGateway", "CheckoutSession", "Customer", "GatewayResult",
    "available_gateways", "get_gateway", "is_test_mode",
]
