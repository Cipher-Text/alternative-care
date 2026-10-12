"""Platform Admin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireAdmin, RequireAdminOrOperator
from app.shared.schemas import DirectoryVerification
from app.modules.admin.schemas import (
    AdminAddTenantDoctorRequest,
    AdminAddTenantDoctorResponse,
    AdminDashboardResponse,
    AdminProvisionRequest,
    AdminProvisionResponse,
    AdminTenantDetailResponse,
    AdminTenantItem,
    AdminTenantListItem,
    AdminTenantUsageResponse,
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
    current_user: RequireAdminOrOperator,  # noqa: ARG001
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
    current_user: RequireAdminOrOperator,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None, description="Match tenant, clinic or doctor name, or email"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    service = AdminService(db)
    return await service.list_tenants(search=search, limit=limit, offset=offset)


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
    current_user: RequireAdminOrOperator,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    service = AdminService(db)
    return await service.list_pending_tenants(limit=limit, offset=offset)


@router.get(
    "/tenants/{tenant_id}",
    response_model=AdminTenantDetailResponse,
    summary="Get tenant detail",
    description="Get tenant/clinic details and all users.",
)
async def get_tenant_detail(
    tenant_id: str,
    current_user: RequireAdminOrOperator,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.get_tenant_detail(tenant_id)


@router.get(
    "/tenants/{tenant_id}/usage",
    response_model=AdminTenantUsageResponse,
    summary="Get tenant usage",
    description="Get a tenant's month-to-date usage counters (prescriptions, SMS, AI queries, PDFs).",
)
async def get_tenant_usage(
    tenant_id: str,
    current_user: RequireAdminOrOperator,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.get_tenant_usage(tenant_id)


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


@router.post(
    "/tenants/{tenant_id}/doctors",
    response_model=AdminAddTenantDoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add doctor to tenant",
    description="Create another doctor user under an existing clinic tenant.",
)
async def create_tenant_doctor(
    tenant_id: str,
    data: AdminAddTenantDoctorRequest,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AdminService(db)
    return await service.create_tenant_doctor(tenant_id, data, current_user.user_id)


# ============================================================================
# User / role distribution
# ============================================================================


@router.get(
    "/users",
    response_model=AdminUsersResponse,
    summary="List users (role distribution)",
    description="List users across the platform with a role summary over the whole filtered set. Filter by role, tenant, status or search; paginated.",
)
async def list_users(
    current_user: RequireAdminOrOperator,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
    role: str | None = None,
    tenant_id: str | None = None,
    is_active: bool | None = None,
    search: str | None = Query(None, description="Match name, email or clinic name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    service = AdminService(db)
    return await service.list_users(
        role=role,
        tenant_id=tenant_id,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )


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


# ============================================================================
# Credential verification (public directory trust signal — free)
# ============================================================================


@router.post(
    "/tenants/{tenant_id}/verification",
    summary="Verify or unverify a tenant's credentials",
    description=(
        "Records that an admin checked the tenant's registration and credentials. Free for every "
        "plan; a verified tenant can appear in the public directory if it opts in and its plan allows."
    ),
)
async def set_tenant_verification(
    tenant_id: str,
    data: DirectoryVerification,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.modules.directory.service import set_verification

    tenant = await set_verification(db, tenant_id, current_user.user_id, data.verified, data.note)
    return {
        "tenant_id": tenant.id,
        "is_verified": tenant.is_verified,
        "verified_at": tenant.verified_at,
        "verification_note": tenant.verification_note,
    }
