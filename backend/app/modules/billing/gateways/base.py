"""Checkout gateway interface. One implementation per provider (fake, SSLCommerz, bKash).

The browser's return from a gateway is never trusted: the server asks the gateway for the truth
(`verify`, or `handle_return` for a provider that needs a final capture step) and checks amount and
currency before anything is fulfilled (see `OrderService.settle`)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.shared.models import BillingOrder


@dataclass
class Customer:
    """What a hosted payment page asks for about the payer. Missing values get plain placeholders."""

    name: str
    email: str
    phone: str
    address: str = "N/A"
    city: str = "Dhaka"


@dataclass
class CheckoutSession:
    redirect_url: str  # where to send the browser to pay
    gateway_session_id: str | None = None  # the provider's id for this payment attempt


@dataclass
class GatewayResult:
    status: Literal["paid", "failed", "cancelled", "pending"]
    gateway_txn_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    raw: dict = field(default_factory=dict)  # safe-to-store fields only: never credentials


class CheckoutGateway(ABC):
    name: str
    label: str = ""
    sandbox: bool = False  # true when no real money moves (fake gateway, provider sandbox)

    @abstractmethod
    async def create_checkout(self, order: BillingOrder, customer: Customer) -> CheckoutSession:
        """Start a hosted payment for this order."""

    @abstractmethod
    async def verify(self, order: BillingOrder) -> GatewayResult:
        """Ask the gateway what actually happened to this order."""

    async def handle_return(self, order: BillingOrder, params: dict) -> GatewayResult:
        """The browser came back from the provider with `params`. The default ignores what the
        browser claims and asks the provider; a gateway with a capture step overrides this."""
        return await self.verify(order)
