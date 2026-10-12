"""Clinic-facing billing: messaging credit balances and history."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import CreditService
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.core.messaging import email_configured, sms_configured
from app.modules.billing.gateways import get_gateway
from app.modules.billing.gateways.fake import FakeGateway
from app.modules.billing.orders import OrderService, subscription_info
from app.shared.models import CreditPack, Tenant
from app.shared.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    CreditPackResponse,
    FakeGatewayComplete,
    OrderResponse,
    SubscriptionInfo,
)
from app.shared.schemas.credits import ChannelBalance, CreditSummary, LedgerEntry

router = APIRouter()

# Doctors and receptionists can see the balance (receptionists send reminders); history is the
# clinic's own. Platform users have no tenant and no balance.
TenantStaff = Annotated[CurrentUser, Depends(require_role("doctor", "receptionist"))]
# Only doctors buy, renew and see receipts: the clinic's money is the doctor's decision
Buyer = Annotated[CurrentUser, Depends(require_role("doctor"))]


@router.get("/credits", response_model=CreditSummary)
async def get_credits(db: Annotated[AsyncSession, Depends(get_db)], user: TenantStaff):
    summary = await CreditService(db, user.tenant_id).summary()
    return CreditSummary(
        channels=[ChannelBalance(**s.__dict__) for s in summary],
        sms_available=sms_configured(),
        email_available=email_configured(),
    )


@router.get("/credits/ledger", response_model=list[LedgerEntry])
async def get_credit_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: TenantStaff,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await CreditService(db, user.tenant_id).ledger(limit, offset)


# ===== Subscription and checkout =====


@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription(db: Annotated[AsyncSession, Depends(get_db)], user: Buyer):
    """Current plan, expiry, what can be bought now, and which payment methods are usable."""
    tenant = (await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one()
    return await subscription_info(db, tenant)


@router.get("/packs", response_model=list[CreditPackResponse])
async def list_packs(db: Annotated[AsyncSession, Depends(get_db)], user: Buyer):  # noqa: ARG001
    rows = await db.execute(
        select(CreditPack)
        .where(CreditPack.is_active.is_(True))
        .order_by(CreditPack.channel, CreditPack.sort_order, CreditPack.price)
    )
    return rows.scalars().all()


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def start_checkout(
    data: CheckoutRequest, db: Annotated[AsyncSession, Depends(get_db)], user: Buyer
):
    """Create an order and return where to send the browser to pay. Nothing is granted yet."""
    order, redirect_url = await OrderService(db).create(user.tenant_id, user.user_id, data)
    return CheckoutResponse(order=OrderResponse.model_validate(order), redirect_url=redirect_url)


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Buyer,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await OrderService(db).list_for_tenant(user.tenant_id, limit, offset)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: Annotated[AsyncSession, Depends(get_db)], user: Buyer):
    """One of the clinic's orders. A pending order is re-checked with the gateway, so the return
    page shows the truth even if the gateway's own notification was lost."""
    service = OrderService(db)
    order = await service.get_for_tenant(order_id, user.tenant_id)
    return await service.refresh(order)


@router.post("/fake-gateway/{order_id}/complete", response_model=OrderResponse)
async def complete_fake_payment(
    order_id: str,
    data: FakeGatewayComplete,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Buyer,
):
    """TEST ONLY: the fake hosted page reports the outcome the tester chose. Not registered as a
    usable method (404) unless PAYMENT_FAKE_GATEWAY_ENABLED is on, which production refuses."""
    try:
        get_gateway("fake")
    except HTTPException as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found") from exc
    service = OrderService(db)
    order = await service.get_for_tenant(order_id, user.tenant_id)
    if order.gateway != "fake":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a test-gateway order")
    if order.status == "pending":
        order.gateway_data = {**(order.gateway_data or {}), "fake_outcome": data.outcome}
        await db.commit()
        await db.refresh(order)
    return await service.refresh(order)
