"""Checkout gateways available to this deployment."""

from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.billing.gateways.base import CheckoutGateway, CheckoutSession, GatewayResult
from app.modules.billing.gateways.fake import FakeGateway


def available_gateways() -> list[str]:
    names = []
    if settings.PAYMENT_FAKE_GATEWAY_ENABLED:
        names.append("fake")
    return names


def get_gateway(name: str) -> CheckoutGateway:
    if name == "fake" and settings.PAYMENT_FAKE_GATEWAY_ENABLED:
        return FakeGateway()
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "This payment method is not available")


__all__ = ["CheckoutGateway", "CheckoutSession", "GatewayResult", "available_gateways", "get_gateway"]
