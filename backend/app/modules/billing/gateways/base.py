"""Checkout gateway interface. One implementation per provider (fake now; SSLCommerz, bKash next).

The browser's return from a gateway is never trusted: the server asks the gateway for the truth
(`verify`) and checks amount and currency before anything is fulfilled.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.shared.models import BillingOrder


@dataclass
class CheckoutSession:
    redirect_url: str  # where to send the browser to pay
    gateway_session_id: str | None = None


@dataclass
class GatewayResult:
    status: Literal["paid", "failed", "cancelled", "pending"]
    gateway_txn_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    raw: dict = field(default_factory=dict)


class CheckoutGateway(ABC):
    name: str

    @abstractmethod
    async def create_checkout(self, order: BillingOrder) -> CheckoutSession:
        """Start a hosted payment for this order."""

    @abstractmethod
    async def verify(self, order: BillingOrder) -> GatewayResult:
        """Ask the gateway what actually happened to this order."""
