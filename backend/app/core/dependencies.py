"""FastAPI dependencies for authentication and authorization."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.shared.models.tenant import Tenant, User

# Security scheme
security = HTTPBearer()


class CurrentUser:
    """Current authenticated user data from JWT."""

    def __init__(
        self,
        user_id: str,
        tenant_id: str | None,
        role: str,
        email: str,
        plan: str | None = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email
        self.plan = plan

    @property
    def is_platform_user(self) -> bool:
        """Check if user is platform admin/operator."""
        return self.tenant_id is None

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "admin"

    @property
    def is_doctor(self) -> bool:
        """Check if user is doctor."""
        return self.role == "doctor"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Get current user from JWT token with token version validation.

    SECURITY: Validates token_version to ensure tokens are invalidated on:
    - Password change
    - Email change
    - Role change

    Raises:
        HTTPException: If token is invalid, expired, or version mismatch
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise credentials_exception

        # Extract claims
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_version: int | None = payload.get("token_version")
        tenant_id: str | None = payload.get("tenant_id")
        role: str | None = payload.get("role")
        email: str | None = payload.get("email")
        plan: str | None = payload.get("plan")

        if not role or not email:
            raise credentials_exception

        # SECURITY: Validate token version against database
        # This invalidates old tokens on password/email/role changes
        if token_version is not None:  # Skip check for old tokens without version
            result = await db.execute(
                select(User.token_version, User.is_active).where(User.id == user_id)
            )
            user_data = result.first()

            if not user_data:
                raise credentials_exception

            db_token_version, is_active = user_data

            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is deactivated",
                )

            if token_version != db_token_version:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been invalidated. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Row-level security keys off this per-request GUC (see the RLS
        # migration, 273747e56a3f). set_config(..., true) is transaction-
        # scoped like SET LOCAL — it can't leak across pooled-connection
        # reuse between requests, since get_db() wraps exactly one
        # transaction per request and commits/rolls back at the end. A
        # platform user (tenant_id=None) simply never sets it, which RLS
        # treats as "no tenant" — zero rows from the clinical tables, a
        # safe default since no current admin code path reads them.
        if tenant_id:
            await db.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            )

        return CurrentUser(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            email=email,
            plan=plan,
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles.

    Usage:
        @router.post("/medicines")
        async def create_medicine(
            user: CurrentUser = Depends(require_role("doctor", "admin"))
        ):
            ...
    """

    async def _check_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' not authorized. Required: {allowed_roles}",
            )
        return user

    return _check_role


async def require_tenant_user(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Require tenant context before entering tenant-owned application paths.

    This is an application authorization boundary, not PostgreSQL RLS.
    """
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A tenant account is required for this operation.",
        )
    return user


def require_plan(*allowed_plans: str):
    """
    Dependency factory to require specific subscription plans.

    Checks the tenant's plan and plan_expires_at in the database, not the
    JWT's `plan` claim — a downgraded or expired tenant must lose access
    immediately, without waiting for its holders' access tokens to expire.

    Usage:
        @router.post("/ai/query")
        async def ai_query(user: CurrentUser = Depends(require_plan("pro"))):
            ...
    """

    async def _check_plan(
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires one of these plans: {allowed_plans}",
            )

        result = await db.execute(
            select(Tenant.plan, Tenant.plan_expires_at).where(Tenant.id == user.tenant_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires one of these plans: {allowed_plans}",
            )

        plan, plan_expires_at = row
        if plan_expires_at is not None and plan_expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your plan has expired.",
            )

        if plan not in allowed_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires one of these plans: {allowed_plans}",
            )
        return user

    return _check_plan


# Common dependency combinations
RequireDoctor = Annotated[CurrentUser, Depends(require_role("doctor"))]
RequireAdmin = Annotated[CurrentUser, Depends(require_role("admin"))]
RequireAdminOrOperator = Annotated[CurrentUser, Depends(require_role("admin", "operator"))]
RequireProPlan = Annotated[CurrentUser, Depends(require_plan("pro"))]
