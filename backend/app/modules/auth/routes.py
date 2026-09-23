"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, RequireAdmin, get_current_user
from app.modules.auth.schemas import (
    AdminCreateTenantDoctorRequest,
    AdminClientDetailResponse,
    AdminClientListItem,
    ChangePasswordRequest,
    Disable2FARequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    Setup2FAResponse,
    UserProfileResponse,
    TenantResponse,
    Verify2FARequest,
    Verify2FAResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()


# ============================================================================
# Registration
# ============================================================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new doctor",
    description="Register a new doctor account. Requires admin approval before activation.",
)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register new doctor with tenant creation."""
    service = AuthService(db)
    return await service.register_doctor(data)


@router.post(
    "/admin/provision-client",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: create client account",
    description="Create tenant (clinic) and primary doctor account in one operation.",
)
async def admin_provision_client(
    data: AdminCreateTenantDoctorRequest,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only client provisioning."""
    service = AuthService(db)
    return await service.admin_create_tenant_doctor(data, current_user.user_id)


@router.get(
    "/admin/clients",
    response_model=list[AdminClientListItem],
    summary="Admin: list clients",
    description="List all tenant clients with primary doctor summaries.",
)
async def list_admin_clients(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only client directory."""
    service = AuthService(db)
    return await service.list_admin_clients()


@router.get(
    "/admin/clients/{tenant_id}",
    response_model=AdminClientDetailResponse,
    summary="Admin: get client detail",
    description="Get tenant/clinic details and doctor users for a client.",
)
async def get_admin_client_detail(
    tenant_id: str,
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only client detail."""
    service = AuthService(db)
    return await service.get_admin_client_detail(tenant_id)


@router.get(
    "/admin/tenants/pending",
    response_model=list[TenantResponse],
    summary="Admin: list pending tenants",
    description="List tenants waiting for approval.",
)
async def list_pending_tenants(
    current_user: RequireAdmin,  # noqa: ARG001
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only pending tenant list."""
    service = AuthService(db)
    return await service.list_pending_tenants()


@router.post(
    "/admin/tenants/{tenant_id}/approve",
    response_model=TenantResponse,
    summary="Admin: approve tenant",
    description="Approve a tenant so tenant-scoped users can log in.",
)
async def approve_tenant(
    tenant_id: str,
    current_user: RequireAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only tenant approval."""
    service = AuthService(db)
    return await service.approve_tenant(tenant_id, current_user.user_id)


# ============================================================================
# Login & Logout
# ============================================================================


@router.post(
    "/login",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    summary="Login",
    description="Authenticate user and receive JWT tokens. Requires 2FA code if enabled.",
)
async def login(
    data: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login and create session."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.login(data, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/login-2fa",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    summary="Complete login with 2FA code",
    description=(
        "Second step of login for accounts with 2FA enabled: resubmit "
        "email/password with totp_code to receive JWT tokens."
    ),
)
async def login_2fa(
    data: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Complete a 2FA-gated login and create session."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.login(data, ip_address=ip_address, user_agent=user_agent)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="Logout user by revoking refresh token session.",
)
async def logout(
    data: LogoutRequest | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user and revoke session."""
    service = AuthService(db)
    refresh_token = data.refresh_token if data else None
    await service.logout(current_user.user_id, refresh_token)
    return LogoutResponse(message="Logged out successfully")


# ============================================================================
# Token Refresh
# ============================================================================


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token. Implements token rotation.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token."""
    service = AuthService(db)
    return await service.refresh_tokens(data.refresh_token)


# ============================================================================
# 2FA Setup
# ============================================================================


@router.post(
    "/2fa/setup",
    response_model=Setup2FAResponse,
    summary="Setup 2FA",
    description="Generate TOTP secret and QR code URI for 2FA setup.",
)
async def setup_2fa(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Setup 2FA for current user."""
    service = AuthService(db)
    return await service.setup_2fa(current_user.user_id)


@router.post(
    "/2fa/verify",
    response_model=Verify2FAResponse,
    summary="Verify and enable 2FA",
    description="Verify TOTP code and enable 2FA for user.",
)
async def verify_2fa(
    data: Verify2FARequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code and enable 2FA."""
    service = AuthService(db)
    success = await service.verify_and_enable_2fa(current_user.user_id, data.totp_code)
    return Verify2FAResponse(
        success=success,
        message="2FA enabled successfully" if success else "Failed to enable 2FA",
    )


@router.post(
    "/2fa/disable",
    response_model=Verify2FAResponse,
    summary="Disable 2FA",
    description="Disable 2FA after password and TOTP verification.",
)
async def disable_2fa(
    data: Disable2FARequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA."""
    service = AuthService(db)
    success = await service.disable_2fa(
        current_user.user_id, data.password, data.totp_code
    )
    return Verify2FAResponse(
        success=success,
        message="2FA disabled successfully" if success else "Failed to disable 2FA",
    )


# ============================================================================
# Password Management
# ============================================================================


@router.post(
    "/password/change",
    response_model=Verify2FAResponse,
    summary="Change password",
    description="Change password for authenticated user.",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password."""
    service = AuthService(db)
    success = await service.change_password(
        current_user.user_id, data.current_password, data.new_password
    )
    return Verify2FAResponse(
        success=success,
        message="Password changed successfully" if success else "Failed to change password",
    )


# TODO: Implement password reset flow (requires email service)
# @router.post("/password/forgot", response_model=ForgotPasswordResponse)
# async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
#     """Request password reset email."""
#     pass

# @router.post("/password/reset", response_model=ResetPasswordResponse)
# async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
#     """Reset password using token from email."""
#     pass


# ============================================================================
# User Profile
# ============================================================================


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile with tenant information.",
)
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile."""
    service = AuthService(db)
    return await service.get_user_profile(current_user.user_id)


# TODO: Email verification endpoints
# @router.post("/email/verify", response_model=VerifyEmailResponse)
# async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
#     """Verify email address."""
#     pass

# @router.post("/email/resend", response_model=ForgotPasswordResponse)
# async def resend_verification(data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
#     """Resend verification email."""
#     pass
