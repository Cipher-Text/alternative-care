"""Schemas for checkout: subscriptions, credit packs, orders."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

OrderStatus = Literal["pending", "paid", "failed", "cancelled", "expired"]
Period = Literal["monthly", "yearly"]


class CheckoutRequest(BaseModel):
    kind: Literal["subscription", "credit_pack"]
    gateway: str = Field(..., max_length=20)
    # subscription
    plan_key: str | None = Field(None, max_length=20)
    period: Period | None = None
    # credit pack
    pack_id: int | None = None

    @model_validator(mode="after")
    def _shape(self):
        if self.kind == "subscription" and not (self.plan_key and self.period):
            raise ValueError("plan_key and period are required for a subscription")
        if self.kind == "credit_pack" and self.pack_id is None:
            raise ValueError("pack_id is required for a credit pack")
        return self


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    receipt_no: str
    kind: str
    status: OrderStatus
    description: str
    amount: Decimal
    currency: str
    plan_key: str | None
    period: str | None
    channel: str | None
    quantity: int | None
    gateway: str
    payer_name: str
    created_at: datetime
    paid_at: datetime | None
    fulfilment: dict | None


class CheckoutResponse(BaseModel):
    order: OrderResponse
    redirect_url: str


class FakeGatewayComplete(BaseModel):
    outcome: Literal["success", "failed", "cancelled"]


class PlanOption(BaseModel):
    """What the clinic can do with one plan right now, computed by the server (not the browser)."""

    plan_key: str
    name_en: str
    name_bn: str | None
    price_monthly: Decimal | None
    price_yearly: Decimal | None
    currency: str
    # subscribe | renew | upgrade | current (no expiry) | blocked | unavailable (no online price)
    action: str
    reason: str | None = None


class SubscriptionInfo(BaseModel):
    plan: str  # stored plan
    applied_plan: str  # plan whose entitlements apply right now (Free after expiry)
    expired: bool
    plan_expires_at: datetime | None
    days_left: int | None
    options: list[PlanOption]
    gateways: list[str]  # payment methods that can be used right now
    # True when a usable method moves no real money (the test gateway or a provider sandbox)
    test_mode: bool = False


class CreditPackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    quantity: int
    price: Decimal
    currency: str
    name_en: str
    name_bn: str | None
    is_active: bool
    sort_order: int


class CreditPackCreate(BaseModel):
    channel: Literal["sms", "email"]
    quantity: int = Field(..., gt=0, le=1_000_000)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    name_en: str = Field(..., min_length=2, max_length=100)
    name_bn: str | None = Field(None, max_length=100)
    is_active: bool = True
    sort_order: int = 0


class CreditPackUpdate(BaseModel):
    """A pack's quantity/channel never change once sold from; edit price, names, status, order."""

    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    name_en: str | None = Field(None, min_length=2, max_length=100)
    name_bn: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    sort_order: int | None = None


class ManualPlanGrant(BaseModel):
    """An admin sets a clinic's plan after taking payment outside the gateways (cash, bank, mobile transfer)."""

    plan_key: str = Field(..., min_length=2, max_length=20, pattern="^[a-z][a-z0-9_]*$")
    term: Literal["monthly", "yearly", "until_date", "no_expiry"]
    # Only for term == "until_date": the last day the plan is active
    until_date: date | None = None
    amount: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    payment_method: Literal["cash", "bank_transfer", "bkash", "nagad", "rocket", "cheque", "other"]
    reference: str = Field(..., min_length=3, max_length=200, description="Transaction id, receipt or note")


class AdminOrderItem(OrderResponse):
    tenant_id: str
    tenant_name: str
    payer_phone: str | None
    gateway_txn_id: str | None
