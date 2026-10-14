"""Admin billing: sell-able credit packs and every clinic's orders (revenue visibility)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.billing.orders import OrderService
from app.shared.models import BillingOrder, CreditPack, Tenant
from app.shared.schemas import (
    AdminOrderItem,
    CreditPackCreate,
    CreditPackResponse,
    CreditPackUpdate,
    ManualPlanGrant,
)

router = APIRouter()

Needs_billing_admin = Annotated[CurrentUser, Depends(require_permission("billing.admin"))]



@router.get("/packs", response_model=list[CreditPackResponse])
async def list_packs(admin: Needs_billing_admin, db: Annotated[AsyncSession, Depends(get_db)]):  # noqa: ARG001
    rows = await db.execute(select(CreditPack).order_by(CreditPack.channel, CreditPack.sort_order))
    return rows.scalars().all()


@router.post("/packs", response_model=CreditPackResponse, status_code=status.HTTP_201_CREATED)
async def create_pack(
    data: CreditPackCreate, admin: Needs_billing_admin, db: Annotated[AsyncSession, Depends(get_db)]
):
    pack = CreditPack(**data.model_dump(), created_by=admin.user_id)
    db.add(pack)
    await db.commit()
    await db.refresh(pack)
    return pack


@router.patch("/packs/{pack_id}", response_model=CreditPackResponse)
async def update_pack(
    pack_id: int,
    data: CreditPackUpdate,
    admin: Needs_billing_admin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Edit price, names, order or active flag. Past orders keep the quantity and price they sold at."""
    pack = (await db.execute(select(CreditPack).where(CreditPack.id == pack_id))).scalar_one_or_none()
    if pack is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pack not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(pack, key, value)
    pack.updated_by = admin.user_id
    await db.commit()
    await db.refresh(pack)
    return pack


@router.post("/tenants/{tenant_id}/plan", response_model=AdminOrderItem, status_code=status.HTTP_201_CREATED)
async def grant_plan(
    tenant_id: str,
    data: ManualPlanGrant,
    admin: Needs_billing_admin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Move a clinic to a plan after a manual payment (cash, bank or mobile transfer). Recorded as a paid
    order with the method and reference, so it shows in the clinic's receipts and in revenue."""
    order = await OrderService(db).grant_manual(tenant_id, admin.user_id, data)
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    return AdminOrderItem(**_order_dict(order), tenant_name=tenant.clinic_name or tenant.name)


@router.get("/orders", response_model=list[AdminOrderItem])
async def list_orders(
    admin: Needs_billing_admin,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status", pattern="^(pending|paid|failed|cancelled|expired)$"),
    tenant_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):  # noqa: ARG001
    q = select(BillingOrder, Tenant.clinic_name, Tenant.name).join(Tenant, Tenant.id == BillingOrder.tenant_id)
    if status_filter:
        q = q.where(BillingOrder.status == status_filter)
    if tenant_id:
        q = q.where(BillingOrder.tenant_id == tenant_id)
    rows = (await db.execute(q.order_by(BillingOrder.created_at.desc()).limit(limit).offset(offset))).all()
    return [
        AdminOrderItem(**_order_dict(order), tenant_name=clinic or name)
        for order, clinic, name in rows
    ]


def _order_dict(order: BillingOrder) -> dict:
    return {
        c: getattr(order, c)
        for c in (
            "id", "receipt_no", "kind", "status", "description", "amount", "currency", "plan_key",
            "period", "channel", "quantity", "gateway", "payer_name", "created_at", "paid_at",
            "fulfilment", "tenant_id", "payer_phone", "gateway_txn_id",
        )
    }
