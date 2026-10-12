"""Checkout orders: create, settle exactly once, and activate what was paid for.

Settling is the only place money turns into entitlement. It runs under a row lock on the order, so
a gateway notification that arrives twice (or races the browser's return) cannot grant twice, and it
refuses to fulfil when the gateway's amount or currency does not match what we asked for.
"""

import secrets
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import structlog
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import CreditService
from app.core.entitlements import FALLBACK_PLAN, effective_plan_key
from app.modules.billing.gateways import available_gateways, get_gateway, is_test_mode
from app.modules.billing.gateways.base import Customer, GatewayResult
from app.modules.plans.service import PlansService
from app.shared.models import BillingOrder, CreditPack, Plan, Tenant, User
from app.shared.schemas import CheckoutRequest, PlanOption, SubscriptionInfo

logger = structlog.get_logger()

PERIOD_DELTA = {"monthly": relativedelta(months=1), "yearly": relativedelta(years=1)}
PERIOD_LABEL = {"monthly": "1 month", "yearly": "1 year"}


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, "message": message})


def _price(plan: Plan, period: str) -> Decimal | None:
    value = plan.price_monthly if period == "monthly" else plan.price_yearly
    return value if value is not None and value > 0 else None


async def _plans(db: AsyncSession) -> dict[str, Plan]:
    """Public plans by key. Rows are created from the code defaults on first use, so a deployment
    where an admin never opened the plan editor still lists its plans (just without prices)."""
    rows = await PlansService(db).plan_rows()
    return {key: p for key, p in rows.items() if p.is_public}


def assess(tenant: Tenant, plan: Plan, plans: dict[str, Plan]) -> tuple[str, str | None]:
    """(action, reason) for buying `plan` now. Pure: shared by the options list and checkout."""
    if plan.price_monthly is None and plan.price_yearly is None:
        return "unavailable", "No online price for this plan yet."
    applied, expired = effective_plan_key(tenant)
    current_rank = plans[applied].sort_order if applied in plans else 0
    if applied == FALLBACK_PLAN or expired:
        return "subscribe", None
    if plan.key == applied:
        if tenant.plan_expires_at is None:
            return "current", "Your plan does not expire."
        return "renew", None
    if plan.sort_order > current_rank:
        return "upgrade", None
    return (
        "blocked",
        "Your current plan is still active. You can switch to a lower plan after it ends.",
    )


async def subscription_info(db: AsyncSession, tenant: Tenant) -> SubscriptionInfo:
    plans = await _plans(db)
    applied, expired = effective_plan_key(tenant)
    expires = tenant.plan_expires_at
    days_left = None
    if expires is not None and not expired:
        days_left = max(0, (expires - datetime.now(timezone.utc)).days)
    options = []
    for plan in sorted(plans.values(), key=lambda p: p.sort_order):
        if plan.key == FALLBACK_PLAN:
            continue
        action, reason = assess(tenant, plan, plans)
        options.append(
            PlanOption(
                plan_key=plan.key,
                name_en=plan.name_en,
                name_bn=plan.name_bn,
                price_monthly=plan.price_monthly,
                price_yearly=plan.price_yearly,
                currency=plan.currency,
                action=action,
                reason=reason,
            )
        )
    return SubscriptionInfo(
        plan=tenant.plan,
        applied_plan=applied,
        expired=expired,
        plan_expires_at=expires,
        days_left=days_left,
        options=options,
        gateways=available_gateways(),
        test_mode=is_test_mode(),
    )


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- create ---------------------------------------------------------------------------

    async def create(self, tenant_id: str, user_id: str, data: CheckoutRequest):
        gateway = get_gateway(data.gateway)  # 400 if not available
        tenant = (await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one()

        fields: dict
        if data.kind == "subscription":
            plans = await _plans(self.db)
            plan = plans.get(data.plan_key or "")
            if plan is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
            amount = _price(plan, data.period)
            action, reason = assess(tenant, plan, plans)
            if amount is None or action == "unavailable":
                raise _conflict("not_purchasable", "This plan cannot be bought online yet.")
            if action in ("current", "blocked"):
                raise _conflict("not_allowed_now", reason or "Not available right now.")
            fields = dict(
                plan_key=plan.key,
                period=data.period,
                description=f"{plan.name_en} plan, {PERIOD_LABEL[data.period]}",
                currency=plan.currency,
            )
        else:
            pack = (
                await self.db.execute(select(CreditPack).where(CreditPack.id == data.pack_id))
            ).scalar_one_or_none()
            if pack is None or not pack.is_active:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit pack not found")
            amount = pack.price
            fields = dict(
                pack_id=pack.id,
                channel=pack.channel,
                quantity=pack.quantity,
                description=pack.name_en,
                currency=pack.currency,
            )

        order = BillingOrder(
            id=str(uuid4()),
            receipt_no=f"AC-{datetime.now(timezone.utc):%Y%m}-{secrets.token_hex(3).upper()}",
            tenant_id=tenant_id,
            payer_user_id=user_id,
            payer_name=user.full_name,
            payer_phone=user.phone,
            kind=data.kind,
            amount=amount,
            status="pending",
            gateway=gateway.name,
            created_by=user_id,
            **fields,
        )
        self.db.add(order)
        await self.db.flush()
        customer = Customer(
            name=user.full_name,
            email=user.email or tenant.clinic_email or tenant.email,
            phone=user.phone or tenant.clinic_phone or tenant.phone or "01700000000",
            address=(tenant.address_line_1 or tenant.clinic_address or "N/A"),
        )
        try:
            session = await gateway.create_checkout(order, customer)
        except HTTPException:
            await self.db.rollback()  # the provider refused or is down: leave no half-made order behind
            raise
        order.gateway_data = {"session_id": session.gateway_session_id}
        await self.db.commit()
        await self.db.refresh(order)
        return order, session.redirect_url

    # ----- read -----------------------------------------------------------------------------

    async def get_for_tenant(self, order_id: str, tenant_id: str) -> BillingOrder:
        order = (
            await self.db.execute(
                select(BillingOrder).where(
                    BillingOrder.id == order_id, BillingOrder.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return order

    async def refresh(self, order: BillingOrder) -> BillingOrder:
        """For a pending order, ask the gateway what happened (covers a lost notification)."""
        if order.status != "pending":
            return order
        try:
            result = await get_gateway(order.gateway).verify(order)
        except HTTPException:
            return order
        except Exception:  # noqa: BLE001 — a gateway outage must not break the page
            logger.warning("billing_verify_failed", order_id=order.id, gateway=order.gateway)
            return order
        return await self.settle(order.id, result)

    async def list_for_tenant(self, tenant_id: str, limit: int, offset: int):
        rows = await self.db.execute(
            select(BillingOrder)
            .where(BillingOrder.tenant_id == tenant_id)
            .order_by(BillingOrder.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return rows.scalars().all()

    # ----- settle ---------------------------------------------------------------------------

    async def settle(self, order_id: str, result: GatewayResult) -> BillingOrder:
        """Apply a gateway outcome. Safe to call any number of times, from any source."""
        order = (
            await self.db.execute(
                select(BillingOrder).where(BillingOrder.id == order_id).with_for_update()
            )
        ).scalar_one()

        if result.status == "pending" or order.fulfilled_at is not None:
            await self.db.commit()  # release the lock; nothing to change
            await self.db.refresh(order)
            return order

        if result.status in ("failed", "cancelled"):
            if order.status == "pending":
                order.status = result.status
                order.gateway_data = {**(order.gateway_data or {}), "result": result.raw}
            await self.db.commit()
            await self.db.refresh(order)
            return order

        # Paid: money must match what we asked for, or we do not grant anything
        if (result.amount is not None and Decimal(result.amount) != Decimal(order.amount)) or (
            result.currency is not None and result.currency != order.currency
        ):
            logger.error(
                "billing_amount_mismatch",
                order_id=order.id,
                expected=str(order.amount),
                got=str(result.amount),
            )
            order.status = "failed"
            order.gateway_data = {
                **(order.gateway_data or {}),
                "mismatch": {"amount": str(result.amount), "currency": result.currency},
            }
            await self.db.commit()
            await self.db.refresh(order)
            return order

        now = datetime.now(timezone.utc)
        order.status = "paid"
        order.paid_at = now
        order.gateway_txn_id = result.gateway_txn_id
        order.gateway_data = {**(order.gateway_data or {}), "result": result.raw}
        order.fulfilment = await self._fulfil(order, now)
        order.fulfilled_at = now
        await self.db.commit()
        await self.db.refresh(order)
        logger.info("billing_order_fulfilled", order_id=order.id, kind=order.kind, tenant_id=order.tenant_id)
        return order

    async def _fulfil(self, order: BillingOrder, now: datetime) -> dict:
        if order.kind == "credit_pack":
            balance = await CreditService(self.db, order.tenant_id).grant(
                order.channel, order.quantity, "purchase",
                reference=order.receipt_no, note=order.description, created_by=order.payer_user_id,
                commit=False,
            )
            return {"channel": order.channel, "added": order.quantity, "balance": balance}

        tenant = (
            await self.db.execute(select(Tenant).where(Tenant.id == order.tenant_id).with_for_update())
        ).scalar_one()
        applied, expired = effective_plan_key(tenant)
        extending = (
            tenant.plan == order.plan_key and not expired and tenant.plan_expires_at is not None
        )
        base = tenant.plan_expires_at if extending else now
        new_expiry = base + PERIOD_DELTA[order.period]
        if tenant.plan != order.plan_key or expired:
            tenant.plan_started_at = now
        tenant.plan = order.plan_key
        tenant.plan_expires_at = new_expiry
        tenant.plan_reminder_stage = 0  # a new period gets its own reminders
        return {"plan": order.plan_key, "plan_expires_at": new_expiry.isoformat(), "extended": extending}
