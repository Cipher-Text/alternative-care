"""Platform Admin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireAdmin
from app.modules.admin.schemas import (
    AdminDashboardResponse,
    AdminProvisionRequest,
    AdminProvisionResponse,
    AdminTenantDetailResponse,
    AdminTenantItem,
    AdminTenantListItem,
    AdminUpdateTenantRequest,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    AdminUsersResponse,
)
from app.modules.admin.service import AdminService

router = APIRouter()


# ============================================================================
# Dashboard
# ============================================================================


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    summary="Platform KPI dashboard",
    description="Get platform-level KPIs: tenant counts, user counts, plan breakdown.",
)
async def get_dashboard(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.get_dashboard()


# ============================================================================
# Tenant management
# ============================================================================


@router.get(
    "/tenants",
    response_model=list[AdminTenantListItem],
    summary="List all tenants",
    description="List all tenant clients with primary doctor summaries.",
)
async def list_tenants(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.list_tenants()


@router.post(
    "/tenants",
    response_model=AdminProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision tenant + doctor",
    description="Create a tenant (clinic) and primary doctor account in one operation.",
)
async def provision_tenant(
    data: AdminProvisionRequest,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.provision_tenant(data, current_user.user_id)


@router.get(
    "/tenants/pending",
    response_model=list[AdminTenantItem],
    summary="List pending tenants",
    description="List tenants waiting for admin approval.",
)
async def list_pending_tenants(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.list_pending_tenants()


@router.get(
    "/tenants/{tenant_id}",
    response_model=AdminTenantDetailResponse,
    summary="Get tenant detail",
    description="Get tenant/clinic details and all users.",
)
async def get_tenant_detail(
    tenant_id: str,
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.get_tenant_detail(tenant_id)


@router.post(
    "/tenants/{tenant_id}/approve",
    response_model=AdminTenantItem,
    summary="Approve tenant",
    description="Approve a pending tenant so tenant-scoped users can log in.",
)
async def approve_tenant(
    tenant_id: str,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.approve_tenant(tenant_id, current_user.user_id)


@router.patch(
    "/tenants/{tenant_id}",
    response_model=AdminTenantItem,
    summary="Update tenant",
    description="Change plan, suspend (is_active=false), or reactivate (is_active=true) a tenant.",
)
async def update_tenant(
    tenant_id: str,
    data: AdminUpdateTenantRequest,
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.update_tenant(tenant_id, data)


# ============================================================================
# User / role distribution
# ============================================================================


@router.get(
    "/users",
    response_model=AdminUsersResponse,
    summary="List users (role distribution)",
    description="List all users across the platform with role summary. Filter by role, tenant, or status.",
)
async def list_users(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
    role: str | None = None,
    tenant_id: str | None = None,
    is_active: bool | None = None,
):
    service = AdminService(db)
    return await service.list_users(role=role, tenant_id=tenant_id, is_active=is_active)


@router.patch(
    "/users/{user_id}",
    response_model=AdminUpdateUserResponse,
    summary="Update user role or status",
    description="Change a user's role or activate/deactivate them. Role change invalidates existing JWT tokens.",
)
async def update_user(
    user_id: str,
    data: AdminUpdateUserRequest,
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.update_user(user_id, data)
