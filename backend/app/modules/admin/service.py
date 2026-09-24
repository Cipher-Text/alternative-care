"""Platform Admin service — business logic for platform-level operations."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.core.usage_tracking import UsageService
from app.modules.admin.schemas import (
    AdminAddTenantDoctorRequest,
    AdminAddTenantDoctorResponse,
    AdminDashboardResponse,
    AdminProvisionRequest,
    AdminProvisionResponse,
    AdminTenantDetailResponse,
    AdminTenantDoctorItem,
    AdminTenantItem,
    AdminTenantListItem,
    AdminTenantUsageResponse,
    AdminUpdateTenantRequest,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    AdminUserItem,
    AdminUsersResponse,
)
from app.shared.models.tenant import Tenant, User

VALID_ROLES = {"admin", "operator", "doctor", "receptionist"}
PLATFORM_ROLES = {"admin", "operator"}
TENANT_ROLES = {"doctor", "receptionist"}


class AdminService:
    """Platform Admin service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Dashboard
    # ========================================================================

    async def get_dashboard(self) -> AdminDashboardResponse:
        """Get platform KPI metrics."""
        # Tenant counts
        total_result = await self.db.execute(select(func.count()).select_from(Tenant))
        total_tenants = total_result.scalar() or 0

        active_result = await self.db.execute(
            select(func.count()).select_from(Tenant).where(
                Tenant.is_active == True,  # noqa: E712
                Tenant.is_approved == True,  # noqa: E712
            )
        )
        active_tenants = active_result.scalar() or 0

        pending_result = await self.db.execute(
            select(func.count()).select_from(Tenant).where(
                Tenant.is_approved == False  # noqa: E712
            )
        )
        pending_approvals = pending_result.scalar() or 0

        # User counts
        doctor_result = await self.db.execute(
            select(func.count()).select_from(User).where(User.role == "doctor")
        )
        total_doctors = doctor_result.scalar() or 0

        total_users_result = await self.db.execute(select(func.count()).select_from(User))
        total_users = total_users_result.scalar() or 0

        # Plan breakdown
        plans: dict[str, int] = {"free": 0, "plus": 0, "pro": 0}
        plan_result = await self.db.execute(
            select(Tenant.plan, func.count().label("count"))
            .group_by(Tenant.plan)
        )
        for plan_name, count in plan_result.all():
            if plan_name in plans:
                plans[plan_name] = count

        return AdminDashboardResponse(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            pending_approvals=pending_approvals,
            total_doctors=total_doctors,
            total_users=total_users,
            plans=plans,
        )

    # ========================================================================
    # Tenant management
    # ========================================================================

    async def list_tenants(self) -> list[AdminTenantListItem]:
        """List all tenants with primary doctor summaries."""
        tenant_result = await self.db.execute(
            select(Tenant).order_by(Tenant.created_at.desc())
        )
        tenants = tenant_result.scalars().all()

        if not tenants:
            return []

        tenant_ids = [t.id for t in tenants]
        user_result = await self.db.execute(
            select(User)
            .where(User.tenant_id.in_(tenant_ids), User.role == "doctor")
            .order_by(User.created_at.asc())
        )
        doctors = user_result.scalars().all()

        doctors_by_tenant: dict[str, list[User]] = {}
        for doctor in doctors:
            if doctor.tenant_id:
                doctors_by_tenant.setdefault(doctor.tenant_id, []).append(doctor)

        return [
            AdminTenantListItem(
                tenant=AdminTenantItem.model_validate(tenant),
                primary_doctor=(
                    AdminTenantDoctorItem.model_validate(doctors_by_tenant[tenant.id][0])
                    if doctors_by_tenant.get(tenant.id)
                    else None
                ),
                doctor_count=len(doctors_by_tenant.get(tenant.id, [])),
                created_at=tenant.created_at,
            )
            for tenant in tenants
        ]

    async def get_tenant_detail(self, tenant_id: str) -> AdminTenantDetailResponse:
        """Get tenant details with all users."""
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        user_result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant.id)
            .order_by(User.created_at.asc())
        )
        users = user_result.scalars().all()

        return AdminTenantDetailResponse(
            tenant=AdminTenantItem.model_validate(tenant),
            doctors=[AdminTenantDoctorItem.model_validate(u) for u in users],
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            approved_at=tenant.approved_at,
            approved_by=tenant.approved_by,
        )

    async def get_tenant_usage(self, tenant_id: str) -> AdminTenantUsageResponse:
        """Get a tenant's month-to-date usage counters."""
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        usage = await UsageService(self.db, tenant_id).get_month_to_date()

        return AdminTenantUsageResponse(
            tenant_id=tenant_id,
            plan=tenant.plan,
            plan_expires_at=tenant.plan_expires_at,
            month=datetime.now(timezone.utc).strftime("%Y-%m"),
            **usage,
        )

    async def list_pending_tenants(self) -> list[AdminTenantItem]:
        """List tenants waiting for approval."""
        result = await self.db.execute(
            select(Tenant)
            .where(Tenant.is_approved == False)  # noqa: E712
            .order_by(Tenant.created_at.desc())
        )
        return [AdminTenantItem.model_validate(t) for t in result.scalars().all()]

    async def provision_tenant(
        self, data: AdminProvisionRequest, admin_user_id: str
    ) -> AdminProvisionResponse:
        """Create tenant (clinic) and primary doctor in one operation."""
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=data.tenant_name or data.full_name,
            email=data.email,
            phone=data.phone,
            clinic_name=data.clinic_name,
            clinic_address=data.clinic_address,
            division_id=data.division_id,
            district_id=data.district_id,
            upazila_id=data.upazila_id,
            specializations=data.specializations,
            license_number=data.license_number,
            is_verified=False,
            is_approved=data.auto_approve,
            approved_at=datetime.now(timezone.utc) if data.auto_approve else None,
            approved_by=admin_user_id if data.auto_approve else None,
            is_active=True,
            plan=data.plan,
        )
        self.db.add(tenant)

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            role="doctor",
            full_name=data.full_name,
            phone=data.phone,
            language=data.language,
            is_active=True,
            is_email_verified=False,
        )
        self.db.add(user)
        await self.db.commit()

        return AdminProvisionResponse(
            message=(
                "Client account created successfully."
                if data.auto_approve
                else "Client account created. Tenant is pending approval."
            ),
            user_id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            requires_approval=not data.auto_approve,
        )

    async def approve_tenant(
        self, tenant_id: str, admin_user_id: str
    ) -> AdminTenantItem:
        """Approve a pending tenant."""
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        tenant.is_approved = True
        tenant.approved_at = datetime.now(timezone.utc)
        tenant.approved_by = admin_user_id

        await self.db.commit()
        await self.db.refresh(tenant)
        return AdminTenantItem.model_validate(tenant)

    async def update_tenant(
        self, tenant_id: str, data: AdminUpdateTenantRequest
    ) -> AdminTenantItem:
        """Update tenant plan, active status, or approval status."""
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        if data.plan is not None:
            tenant.plan = data.plan
        if data.is_active is not None:
            tenant.is_active = data.is_active
        if data.is_approved is not None:
            tenant.is_approved = data.is_approved

        await self.db.commit()
        await self.db.refresh(tenant)
        return AdminTenantItem.model_validate(tenant)

    async def create_tenant_doctor(
        self,
        tenant_id: str,
        data: AdminAddTenantDoctorRequest,
        admin_user_id: str,
    ) -> AdminAddTenantDoctorResponse:
        """Add another doctor user under an existing clinic tenant."""
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        email_result = await self.db.execute(select(User).where(User.email == data.email))
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            role="doctor",
            full_name=data.full_name,
            phone=data.phone,
            language=data.language,
            is_active=True,
            is_email_verified=False,
            created_by=admin_user_id,
            updated_by=admin_user_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return AdminAddTenantDoctorResponse(
            message="Doctor added to clinic successfully.",
            tenant_id=tenant.id,
            doctor=AdminTenantDoctorItem.model_validate(user),
        )

    # ========================================================================
    # User / role distribution
    # ========================================================================

    async def list_users(
        self,
        role: str | None = None,
        tenant_id: str | None = None,
        is_active: bool | None = None,
    ) -> AdminUsersResponse:
        """List all users across the platform, grouped by role."""
        query = select(User)

        if role is not None:
            query = query.where(User.role == role)
        if tenant_id is not None:
            query = query.where(User.tenant_id == tenant_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.order_by(User.role, User.created_at.asc())
        result = await self.db.execute(query)
        users = result.scalars().all()

        # Fetch tenant names for tenant users
        tenant_ids = {u.tenant_id for u in users if u.tenant_id}
        tenant_names: dict[str, str] = {}
        if tenant_ids:
            t_result = await self.db.execute(
                select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
            )
            for t_id, t_name in t_result.all():
                tenant_names[t_id] = t_name

        user_items = [
            AdminUserItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                is_email_verified=u.is_email_verified,
                last_login_at=u.last_login_at,
                tenant_id=u.tenant_id,
                tenant_name=tenant_names.get(u.tenant_id) if u.tenant_id else None,
                created_at=u.created_at,
            )
            for u in users
        ]

        # Build role summary
        by_role: dict[str, int] = {
            "admin": 0,
            "operator": 0,
            "doctor": 0,
            "receptionist": 0,
        }
        for item in user_items:
            if item.role in by_role:
                by_role[item.role] += 1
            else:
                by_role[item.role] = 1

        return AdminUsersResponse(
            summary={"total": len(user_items), "by_role": by_role},
            users=user_items,
        )

    async def update_user(
        self, user_id: str, data: AdminUpdateUserRequest
    ) -> AdminUpdateUserResponse:
        """Update a user's role or activation status."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if data.role is not None:
            if data.role not in VALID_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role '{data.role}'. Must be one of: {sorted(VALID_ROLES)}",
                )

            # Prevent mixing platform and tenant roles
            new_is_platform = data.role in PLATFORM_ROLES
            current_is_platform = user.tenant_id is None
            if new_is_platform != current_is_platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Cannot assign a platform role to a tenant user, or a tenant role to a platform user."
                    ),
                )

            # Prevent removing the last admin
            if user.role == "admin" and data.role != "admin":
                admin_count_result = await self.db.execute(
                    select(func.count()).select_from(User).where(
                        User.role == "admin",
                        User.is_active == True,  # noqa: E712
                    )
                )
                admin_count = admin_count_result.scalar() or 0
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot change role of the last active admin.",
                    )

            user.role = data.role
            # Increment token_version to invalidate all existing JWTs
            user.token_version += 1

        if data.is_active is not None:
            user.is_active = data.is_active

        await self.db.commit()
        await self.db.refresh(user)

        # Fetch tenant name if applicable
        tenant_name = None
        if user.tenant_id:
            t_result = await self.db.execute(
                select(Tenant.name).where(Tenant.id == user.tenant_id)
            )
            tenant_name = t_result.scalar_one_or_none()

        user_item = AdminUserItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            last_login_at=user.last_login_at,
            tenant_id=user.tenant_id,
            tenant_name=tenant_name,
            created_at=user.created_at,
        )
        return AdminUpdateUserResponse(
            message="User updated successfully.",
            user=user_item,
        )
