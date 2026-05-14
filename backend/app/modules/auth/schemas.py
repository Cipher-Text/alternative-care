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


class AdminCreateTenantDoctorRequest(RegisterRequest):
    """Admin request to create tenant (clinic) and primary doctor account."""

    tenant_name: str | None = Field(
        None,
        min_length=2,
        max_length=255,
        description="Tenant display name; defaults to doctor's full name if omitted.",
    )
    plan: Literal["free", "plus", "pro"] = "free"
    auto_approve: bool = True


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


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """Login response with user data."""

    tokens: TokenResponse
    user: "UserResponse"
    requires_2fa: bool = False


# ============================================================================
# Token Schemas
# ============================================================================


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""

    access_token: str
    refresh_token: str
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
