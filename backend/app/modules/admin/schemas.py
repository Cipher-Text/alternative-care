"""Pydantic schemas for Platform Admin endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Dashboard
# ============================================================================


class AdminDashboardResponse(BaseModel):
    """Platform KPI dashboard response."""

    total_tenants: int
    active_tenants: int
    pending_approvals: int
    total_doctors: int
    total_users: int
    plans: dict[str, int]  # { "free": 6, "plus": 3, "pro": 3 }


# ============================================================================
# Tenant schemas
# ============================================================================


class AdminTenantItem(BaseModel):
    """Tenant summary for the platform admin client directory."""

    id: str
    name: str
    email: str
    clinic_name: str | None
    specializations: list[str]
    plan: str
    is_verified: bool
    is_approved: bool
    is_active: bool
    approved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminTenantDoctorItem(BaseModel):
    """Doctor/user summary within a tenant for platform admin views."""

    id: str
    email: str
    full_name: str
    phone: str | None
    role: str
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminTenantListItem(BaseModel):
    """Tenant + primary doctor summary for platform admin client directory."""

    tenant: AdminTenantItem
    primary_doctor: AdminTenantDoctorItem | None
    doctor_count: int
    created_at: datetime


class AdminTenantDetailResponse(BaseModel):
    """Tenant and all users for platform admin detail view."""

    tenant: AdminTenantItem
    doctors: list[AdminTenantDoctorItem]
    created_at: datetime
    updated_at: datetime | None
    approved_at: datetime | None
    approved_by: str | None


class AdminUpdateTenantRequest(BaseModel):
    """Payload for PATCH /admin/tenants/{id}."""

    plan: Literal["free", "plus", "pro"] | None = None
    is_active: bool | None = None
    is_approved: bool | None = None


# ============================================================================
# Tenant provisioning (moved from auth)
# ============================================================================


class AdminProvisionRequest(BaseModel):
    """Admin request to create tenant (clinic) and primary doctor in one operation."""

    # Doctor / user info
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    language: Literal["en", "bn"] = "en"

    # Clinic info
    tenant_name: str | None = Field(
        None,
        min_length=2,
        max_length=255,
        description="Tenant display name; defaults to doctor's full name if omitted.",
    )
    clinic_name: str | None = Field(None, max_length=255)
    clinic_address: str | None = None

    # Location (Bangladesh)
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    # Medical specializations
    specializations: list[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Medical systems: homeopathy, ayurveda, unani, herbal",
    )

    # Professional
    license_number: str | None = Field(None, max_length=100)
    plan: Literal["free", "plus", "pro"] = "free"
    auto_approve: bool = True


class AdminProvisionResponse(BaseModel):
    """Response after provisioning a tenant."""

    message: str
    user_id: str
    tenant_id: str
    email: str
    requires_approval: bool


# ============================================================================
# User (role distribution) schemas
# ============================================================================


class AdminUserItem(BaseModel):
    """User record for platform admin role distribution view."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime | None
    tenant_id: str | None
    tenant_name: str | None  # populated from join
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUsersResponse(BaseModel):
    """All users with role summary for platform admin."""

    summary: dict  # { "total": N, "by_role": { "admin": 1, "doctor": 18, ... } }
    users: list[AdminUserItem]


class AdminUpdateUserRequest(BaseModel):
    """Payload for PATCH /admin/users/{user_id}."""

    role: str | None = None
    is_active: bool | None = None


class AdminUpdateUserResponse(BaseModel):
    """Response after updating a user."""

    message: str
    user: AdminUserItem
