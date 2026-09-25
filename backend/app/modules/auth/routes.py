"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    Disable2FARequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthResponse,
    GoogleLoginRequest,
    GoogleRegisterRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    Setup2FAResponse,
    UserProfileResponse,
    Verify2FARequest,
    Verify2FAResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()

# D8: refresh token lives only in an httpOnly cookie, never in a JS-readable
# place — an XSS that hooks fetch/XHR at page load can read any JSON
# response body, but not a Set-Cookie header processed before JS sees the
# response. Path is "/", not just the auth routes: frontend/src/proxy.ts
# reads this cookie's mere presence to gate dashboard page requests, and a
# cookie is only ever sent to requests whose path matches (or is under) the
# one it was set with — scoping it to /api/v1/auth would make it invisible
# to a plain page navigation to e.g. /dashboard.
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


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
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login and create session."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await service.login(data, ip_address=ip_address, user_agent=user_agent)
    if result.tokens and result.tokens.refresh_token:
        _set_refresh_cookie(response, result.tokens.refresh_token)
        result.tokens.refresh_token = None
    return result


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
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Complete a 2FA-gated login and create session."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await service.login(data, ip_address=ip_address, user_agent=user_agent)
    if result.tokens and result.tokens.refresh_token:
        _set_refresh_cookie(response, result.tokens.refresh_token)
        result.tokens.refresh_token = None
    return result


@router.post(
    "/google",
    response_model=GoogleAuthResponse,
    response_model_exclude_none=True,
    summary="Sign in with Google",
    description=(
        "Authenticate with a Google Identity Services ID token. If no "
        "account exists yet for this Google identity, returns "
        "needs_registration=True — submit clinic details to POST "
        "/auth/google/register to complete signup."
    ),
)
async def google_login(
    data: GoogleLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login (or offer registration) via Google Sign-In."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await service.google_login(data, ip_address=ip_address, user_agent=user_agent)
    if result.tokens and result.tokens.refresh_token:
        _set_refresh_cookie(response, result.tokens.refresh_token)
        result.tokens.refresh_token = None
    return result


@router.post(
    "/google/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete registration via Google",
    description=(
        "Register a new doctor + tenant for a Google-verified identity. "
        "Requires admin approval before activation, same as /register."
    ),
)
async def google_register(
    data: GoogleRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register new doctor + tenant using a verified Google identity."""
    service = AuthService(db)
    return await service.google_register(data)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="Logout user by revoking refresh token session.",
)
async def logout(
    request: Request,
    response: Response,
    data: LogoutRequest | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user and revoke session."""
    service = AuthService(db)
    refresh_token = (
        None
        if data and data.all_sessions
        else (data.refresh_token if data else None) or request.cookies.get(REFRESH_COOKIE_NAME)
    )
    await service.logout(current_user.user_id, refresh_token)
    _clear_refresh_cookie(response)
    return LogoutResponse(message="Logged out successfully")


# ============================================================================
# Token Refresh
# ============================================================================


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    response_model_exclude_none=True,
    summary="Refresh access token",
    description="Get new access token using refresh token. Implements token rotation.",
)
async def refresh_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    data: RefreshTokenRequest | None = None,
):
    """Refresh access token. Browsers rely on the httpOnly cookie; the body
    is only a fallback for non-browser clients — an explicit body value
    takes priority the same way it does on /logout."""
    token = (data.refresh_token if data else None) or request.cookies.get(
        REFRESH_COOKIE_NAME
    )
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    service = AuthService(db)
    result = await service.refresh_tokens(token)
    if result.refresh_token:
        _set_refresh_cookie(response, result.refresh_token)
        result.refresh_token = None
    return result


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


@router.post(
    "/password/forgot",
    response_model=ForgotPasswordResponse,
    summary="Request a password reset",
    description="Send a password reset link by email. Always returns the same "
    "message, whether or not the email is registered.",
)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset email."""
    service = AuthService(db)
    return await service.forgot_password(data.email)


@router.post(
    "/password/reset",
    response_model=ResetPasswordResponse,
    summary="Reset password with a token",
    description="Reset password using the token from the forgot-password email. "
    "Invalidates all existing sessions.",
)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email."""
    service = AuthService(db)
    return await service.reset_password(data.token, data.new_password)


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


@router.post(
    "/email/verify",
    response_model=VerifyEmailResponse,
    summary="Verify email address",
    description="Verify email address using the token from the verification email.",
)
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify email address."""
    service = AuthService(db)
    return await service.verify_email(data.token)


@router.post(
    "/email/resend",
    response_model=ForgotPasswordResponse,
    summary="Resend verification email",
    description="Resend the email verification link. Always returns the same "
    "message, whether or not the email is registered or already verified.",
)
async def resend_verification(data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Resend verification email."""
    service = AuthService(db)
    return await service.resend_verification(data.email)
