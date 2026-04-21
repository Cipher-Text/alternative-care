"""FastAPI dependencies for authentication and authorization."""

from contextvars import ContextVar
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

# Security scheme
security = HTTPBearer()

# Context variable for tenant_id (used in multi-tenant queries)
tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)


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
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> CurrentUser:
    """
    Get current user from JWT token.

    Raises:
        HTTPException: If token is invalid or missing required claims
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

        tenant_id: str | None = payload.get("tenant_id")
        role: str | None = payload.get("role")
        email: str | None = payload.get("email")
        plan: str | None = payload.get("plan")

        if not role or not email:
            raise credentials_exception

        # Set tenant context for multi-tenant queries
        if tenant_id:
            tenant_id_ctx.set(tenant_id)

        return CurrentUser(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            email=email,
            plan=plan,
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


def require_plan(*allowed_plans: str):
    """
    Dependency factory to require specific subscription plans.

    Usage:
        @router.post("/ai/query")
        async def ai_query(user: CurrentUser = Depends(require_plan("pro"))):
            ...
    """

    async def _check_plan(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.plan or user.plan not in allowed_plans:
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
