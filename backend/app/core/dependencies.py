"""FastAPI dependencies for authentication and authorization."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import bind_tenant, get_db
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
        # Set by require_permission / require_any_permission once the user's permissions have been read
        self.permissions: frozenset[str] | None = None
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email
        self.plan = plan

    @property
    def is_platform_user(self) -> bool:
        """Check if user is platform admin/operator."""
        return self.tenant_id is None



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

        # Row-level security keys off the `app.tenant_id` GUC. bind_tenant() sets it for this
        # transaction AND re-applies it to every later transaction on this session, because
        # services commit mid-request and a transaction-local setting would otherwise vanish
        # (see app/core/database.py). A platform user (tenant_id=None) clears the binding, which
        # RLS treats as "no tenant": zero rows from the clinical tables, a safe default.
        await bind_tenant(db, tenant_id)

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


def _permission_denied(missing: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "permission_denied", "message": "You do not have permission to do this.", "permission": missing},
    )


async def get_permissions(user: CurrentUser, db: AsyncSession) -> frozenset[str]:
    """The user's effective permissions (cached briefly). See app/core/rbac.py."""
    from app.core.rbac import effective_permissions

    if user.permissions is None:
        user.permissions = await effective_permissions(db, user.user_id, user.role, user.tenant_id is None)
    return user.permissions


async def ensure_permission(user: CurrentUser, db: AsyncSession, key: str) -> None:
    """For a check that depends on what the request asks for (issuing a prescription is a different permission from
    saving a draft), where a plain route guard cannot know yet."""
    if key not in await get_permissions(user, db):
        raise _permission_denied(key)


def require_permission(*keys: str):
    """Require EVERY listed permission. The permission-based replacement for `require_role` (ADR 010).

    Usage:
        @router.post("/prescriptions/{id}/issue")
        async def issue(user: CurrentUser = Depends(require_permission("prescriptions.issue"))):
            ...
    """

    async def _check(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CurrentUser:
        held = await get_permissions(user, db)
        for key in keys:
            if key not in held:
                raise _permission_denied(key)
        return user

    _check.permission_all = keys  # read by tests/access_matrix.py
    return _check


def require_any_permission(*keys: str):
    """Require AT LEAST ONE of the listed permissions."""

    async def _check(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CurrentUser:
        held = await get_permissions(user, db)
        if not any(key in held for key in keys):
            raise _permission_denied(keys[0])
        return user

    _check.permission_any = keys
    return _check


_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def module_guard(read: tuple[str, ...], write: tuple[str, ...]):
    """Router-level guard: reading needs ANY of the `read` permissions, changing anything needs ANY of the `write` ones.

    The replacement for `deny_receptionist_writes` (ADR 010). It sits on the router, so a write route added later is
    protected automatically: it cannot be reached without at least one of the module's write permissions. Routes that
    need something finer add `require_permission(...)` on themselves, which is checked in addition."""

    async def _check(request: Request, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
        wanted = read if request.method in _SAFE_METHODS else write
        held = await get_permissions(user, db)
        if not any(key in held for key in wanted):
            raise _permission_denied(wanted[0])

    _check.module_read = read
    _check.module_write = write
    return _check


def access_guard(*keys: str):
    """Router-level guard for an area that needs the same permission for every method (reading and changing alike)."""
    return module_guard(read=keys, write=keys)

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


def require_feature(entitlement_key: str):
    """
    Dependency factory: require a plan feature (see `app/core/entitlements.py`).

    Reads the tenant's effective entitlements from the database on every request, so a plan
    change, expiry or per-tenant override takes effect immediately, not at token expiry.
    """

    async def _check_feature(
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        from app.core.entitlements import EntitlementService

        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "no_tenant", "message": "This feature requires a clinic account."},
            )
        await EntitlementService(db).check_feature(user.tenant_id, entitlement_key)
        return user

    return _check_feature


# Enterprise includes everything Pro does
RequireProPlan = Annotated[CurrentUser, Depends(require_plan("pro", "enterprise"))]
RequireAiAssistant = Annotated[CurrentUser, Depends(require_feature("feature_ai_assistant"))]
