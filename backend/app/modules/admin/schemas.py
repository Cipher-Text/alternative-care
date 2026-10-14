"""Pydantic schemas for Platform Admin endpoints."""

from datetime import datetime
from decimal import Decimal
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
    plans: dict[str, int]  # { "free": 6, "plus": 3, "pro": 3, "enterprise": 1 }


class QueueTenant(BaseModel):
    tenant_id: str
    clinic_name: str
    doctor_name: str | None = None
    email: str | None = None
    since: datetime = Field(..., description="When the clinic registered (approvals) or listed itself (verification)")


class QueueContactMessage(BaseModel):
    id: str
    topic: str
    name: str
    created_at: datetime


class ContactQueue(BaseModel):
    new: int
    by_topic: dict[str, int]
    latest: list[QueueContactMessage]


class MarketingQueue(BaseModel):
    needs_draft: int = Field(..., description="Doctor asked; nobody has written the post")
    waiting_for_doctor: int = Field(..., description="A draft is with the doctor for approval")
    ready_to_post: int = Field(..., description="Approved; waiting to be posted on Facebook")


class RevenueSummary(BaseModel):
    this_month: Decimal
    last_month: Decimal
    paid_orders_this_month: int
    abandoned_checkouts: int = Field(..., description="Pending for over an hour, last 7 days")
    failed_last_7_days: int


class ExpiringPlan(BaseModel):
    tenant_id: str
    clinic_name: str
    plan: str
    expires_at: datetime
    days_left: int


class GrowthSummary(BaseModel):
    new_tenants_this_month: int
    new_tenants_last_month: int


class AdminQueueResponse(BaseModel):
    """What platform staff need to act on, across every clinic."""

    pending_approvals_total: int
    pending_approvals: list[QueueTenant]
    verification_waiting_total: int
    verification_waiting: list[QueueTenant]
    contact: ContactQueue
    marketing: MarketingQueue
    revenue: RevenueSummary
    plans_expiring_total: int
    plans_expiring: list[ExpiringPlan]
    recently_expired: int = Field(..., description="Paid plans that ended in the last 7 days")
    growth: GrowthSummary


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
    plan_expires_at: datetime | None = None
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

    plan: Literal["free", "plus", "pro", "enterprise"] | None = None
    is_active: bool | None = None
    is_approved: bool | None = None


class AdminTenantUsageResponse(BaseModel):
    """Month-to-date usage for one tenant, for platform admin billing views."""

    tenant_id: str
    plan: str
    plan_expires_at: datetime | None
    month: str  # "2026-09"
    prescriptions_created: int
    ai_queries_made: int
    sms_sent: int
    pdfs_generated: int


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
    plan: Literal["free", "plus", "pro", "enterprise"] = "free"
    auto_approve: bool = True


class AdminProvisionResponse(BaseModel):
    """Response after provisioning a tenant."""

    message: str
    user_id: str
    tenant_id: str
    email: str
    requires_approval: bool


class AdminAddTenantDoctorRequest(BaseModel):
    """Admin request to add another doctor user to an existing clinic tenant."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    language: Literal["en", "bn"] = "en"


class AdminAddTenantDoctorResponse(BaseModel):
    """Response after adding a doctor to an existing tenant."""

    message: str
    tenant_id: str
    doctor: AdminTenantDoctorItem


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
