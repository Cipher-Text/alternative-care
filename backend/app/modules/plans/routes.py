"""Plan configuration and entitlement routes.

- `public_router`   GET /plans                         — public pricing (no auth)
- `admin_router`    /admin/plans...                    — platform admin plan editor
- `tenant_admin_router` /admin/tenants/{id}/entitlements... — per-tenant overrides
- `me_router`       GET /entitlements/me               — the caller's own limits and usage
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_permission
from app.core.entitlements import EntitlementService
from app.modules.plans.schemas import (
    AdminPlansResponse,
    OverrideRequest,
    PlanAuditEntry,
    PlanConfig,
    PlanUpdateRequest,
    PublicPlansResponse,
    TenantEntitlementsResponse,
)
from app.modules.plans.service import PlansService


Needs_plans_manage = Annotated[CurrentUser, Depends(require_permission("plans.manage"))]
Needs_plans_read = Annotated[CurrentUser, Depends(require_permission("plans.read"))]

DB = Annotated[AsyncSession, Depends(get_db)]

public_router = APIRouter()
admin_router = APIRouter()
tenant_admin_router = APIRouter()
me_router = APIRouter()


@public_router.get("", response_model=PublicPlansResponse, summary="Public plans and pricing")
async def list_public_plans(db: DB):
    return await PlansService(db).public_plans()


@admin_router.get("", response_model=AdminPlansResponse, summary="All plans with entitlements")
async def admin_list_plans(_: Needs_plans_read, db: DB):
    return await PlansService(db).admin_plans()


@admin_router.get("/audit", response_model=list[PlanAuditEntry], summary="Plan change history")
async def admin_plan_audit(
    _: Needs_plans_read,
    db: DB,
    limit: int = Query(100, ge=1, le=500),
    plan_key: str | None = None,
):
    return await PlansService(db).audit(limit, plan_key)


@admin_router.put("/{plan_key}", response_model=PlanConfig, summary="Update a plan")
async def admin_update_plan(plan_key: str, data: PlanUpdateRequest, user: Needs_plans_manage, db: DB):
    return await PlansService(db).update_plan(plan_key, data, user.user_id)


@tenant_admin_router.get(
    "/{tenant_id}/entitlements", response_model=TenantEntitlementsResponse,
    summary="A tenant's effective entitlements and usage",
)
async def tenant_entitlements(tenant_id: str, _: Needs_plans_read, db: DB):
    return await PlansService(db).tenant_entitlements(tenant_id)


@tenant_admin_router.put(
    "/{tenant_id}/entitlements/{key}", response_model=TenantEntitlementsResponse,
    summary="Override one entitlement for one tenant",
)
async def set_tenant_override(
    tenant_id: str, key: str, data: OverrideRequest, user: Needs_plans_manage, db: DB
):
    return await PlansService(db).set_override(tenant_id, key, data, user.user_id)


@tenant_admin_router.delete(
    "/{tenant_id}/entitlements/{key}", response_model=TenantEntitlementsResponse,
    summary="Remove a tenant override (back to the plan's value)",
)
async def delete_tenant_override(tenant_id: str, key: str, user: Needs_plans_manage, db: DB):
    return await PlansService(db).delete_override(tenant_id, key, user.user_id)


@me_router.get("/me", response_model=TenantEntitlementsResponse, summary="My plan limits and usage")
async def my_entitlements(
    user: Annotated[CurrentUser, Depends(get_current_user)], db: DB
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinic account required")
    return await EntitlementService(db).snapshot(user.tenant_id)
