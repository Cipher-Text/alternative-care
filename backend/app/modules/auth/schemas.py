"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_password_strength(v: str) -> str:
    """Enforce minimum complexity for authentication passwords."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one number")
    return v


# ============================================================================
# Registration Schemas
# ============================================================================


class RegisterRequest(BaseModel):
    """Doctor registration request."""

    # User info
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    language: Literal["en", "bn"] = "en"

    # Clinic info
    clinic_name: str | None = Field(None, max_length=255)
    clinic_address: str | None = None

    # Location (Bangladesh)
    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    # Medical specializations (1-4 systems)
    specializations: list[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Medical systems: homeopathy, ayurveda, unani, herbal",
    )

    # License
    license_number: str | None = Field(None, max_length=100)

    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, v: list[str]) -> list[str]:
        """Validate specializations are from allowed list."""
        allowed = {"homeopathy", "ayurveda", "unani", "herbal"}
        for spec in v:
            if spec not in allowed:
                raise ValueError(
                    f"Invalid specialization '{spec}'. Allowed: {allowed}"
                )
        # Remove duplicates
        return list(set(v))

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        return _validate_password_strength(v)


class RegisterResponse(BaseModel):
    """Registration response."""

    message: str
    user_id: str
    tenant_id: str
    email: str
    requires_approval: bool = True

    model_config = {"from_attributes": True}


class GoogleRegisterRequest(BaseModel):
    """
    Complete registration for a Google-verified identity.

    Same clinic/specialization fields as RegisterRequest, minus email/
    password/full_name — those come from re-verifying `id_token`
    server-side (see AuthService.google_register) rather than trusting
    whatever the client submits.
    """

    id_token: str
    phone: str | None = Field(None, max_length=20)
    language: Literal["en", "bn"] = "en"

    clinic_name: str | None = Field(None, max_length=255)
    clinic_address: str | None = None

    division_id: int | None = None
    district_id: int | None = None
    upazila_id: int | None = None

    specializations: list[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Medical systems: homeopathy, ayurveda, unani, herbal",
    )

    license_number: str | None = Field(None, max_length=100)

    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, v: list[str]) -> list[str]:
        """Validate specializations are from allowed list."""
        allowed = {"homeopathy", "ayurveda", "unani", "herbal"}
        for spec in v:
            if spec not in allowed:
                raise ValueError(
                    f"Invalid specialization '{spec}'. Allowed: {allowed}"
                )
        return list(set(v))


class TenantApprovalResponse(BaseModel):
    """Tenant approval response."""

    message: str
    tenant_id: str
    is_approved: bool


# ============================================================================
# Login Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str
    totp_code: str | None = Field(None, description="6-digit 2FA code if enabled")


class GoogleLoginRequest(BaseModel):
    """Google Sign-In request — the ID token from Google Identity Services."""

    id_token: str
    totp_code: str | None = Field(
        None, description="6-digit 2FA code, if the matched account has it enabled"
    )


class TokenResponse(BaseModel):
    """JWT token response.

    `refresh_token` is only populated when there's no httpOnly cookie to
    carry it (e.g. a non-browser client) — the routes null it out and rely
    on `response_model_exclude_none=True` to omit it whenever the cookie
    was set instead, so a browser's JS never sees the raw refresh token.
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """Login response with user data.

    When the account has 2FA enabled and no `totp_code` was submitted,
    `requires_2fa` is True and `tokens`/`user` are omitted — the client
    re-submits email/password/totp_code (e.g. to POST /auth/login-2fa) to
    complete login.
    """

    tokens: TokenResponse | None = None
    user: "UserResponse | None" = None
    requires_2fa: bool = False


class GoogleAuthResponse(BaseModel):
    """
    Response to POST /auth/google.

    Exactly one outcome holds per response:
    - matched an existing account, no 2FA: `tokens` + `user` set
    - matched an existing account with 2FA enabled: `requires_2fa=True` —
      the client resubmits the same `id_token` plus `totp_code`
    - no account with this Google identity or email yet:
      `needs_registration=True`, with the Google-verified `email`/
      `full_name` to prefill POST /auth/google/register (the client still
      collects clinic/specialization info, which Google doesn't have)
    """

    tokens: TokenResponse | None = None
    user: "UserResponse | None" = None
    requires_2fa: bool = False
    needs_registration: bool = False
    email: str | None = None
    full_name: str | None = None


# ============================================================================
# Token Schemas
# ============================================================================


class RefreshTokenRequest(BaseModel):
    """Refresh token request.

    Optional — browsers rely on the httpOnly `refresh_token` cookie instead;
    this body is only a fallback for non-browser clients that can't hold
    cookies across requests.
    """

    refresh_token: str | None = None


class RefreshTokenResponse(BaseModel):
    """Refresh token response. See `TokenResponse` re: `refresh_token`."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


# ============================================================================
# 2FA Schemas
# ============================================================================


class Setup2FAResponse(BaseModel):
    """2FA setup response."""

    secret: str
    qr_code_uri: str
    backup_codes: list[str] | None = None


class Verify2FARequest(BaseModel):
    """2FA verification request."""

    totp_code: str = Field(..., min_length=6, max_length=6)


class Verify2FAResponse(BaseModel):
    """2FA verification response."""

    success: bool
    message: str


class Disable2FARequest(BaseModel):
    """Disable 2FA request."""

    password: str
    totp_code: str = Field(..., min_length=6, max_length=6)


# ============================================================================
# Password Reset Schemas
# ============================================================================


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Forgot password response."""

    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password request."""

    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        return _validate_password_strength(v)


class ResetPasswordResponse(BaseModel):
    """Reset password response."""

    message: str


class ChangePasswordRequest(BaseModel):
    """Change password request (authenticated)."""

    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        return _validate_password_strength(v)


# ============================================================================
# User Response Schemas
# ============================================================================


class UserResponse(BaseModel):
    """User response model."""

    id: str
    tenant_id: str | None
    email: str
    full_name: str
    phone: str | None
    role: str
    language: str
    is_active: bool
    is_email_verified: bool
    is_2fa_enabled: bool
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    """Tenant response model."""

    id: str
    name: str
    email: str
    clinic_name: str | None
    specializations: list[str]
    plan: str
    is_verified: bool
    is_approved: bool
    is_active: bool

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    """Detailed user profile with tenant info."""

    user: UserResponse
    tenant: TenantResponse | None

    model_config = {"from_attributes": True}


# ============================================================================
# Logout Schema
# ============================================================================


class LogoutRequest(BaseModel):
    """Logout request.

    By default (omit the body entirely), only the current session — the
    one identified by the httpOnly refresh_token cookie, or by an
    explicitly supplied `refresh_token` — is revoked. Set `all_sessions`
    to revoke every session for the user regardless of which one is
    current; a browser can never read the raw cookie to target a specific
    *other* session, so this is the only way to express "log out
    everywhere."
    """

    refresh_token: str | None = None
    all_sessions: bool = False


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str


# ============================================================================
# Email Verification
# ============================================================================


class VerifyEmailRequest(BaseModel):
    """Email verification request."""

    token: str


class VerifyEmailResponse(BaseModel):
    """Email verification response."""

    message: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""

    email: EmailStr
