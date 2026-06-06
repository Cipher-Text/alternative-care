"""Tenant and User models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseAuditModel

if TYPE_CHECKING:
    from app.shared.models.patient import Patient


class Tenant(BaseAuditModel):
    """
    Tenant (Clinic/Doctor) model.
    Each doctor or clinic is a separate tenant with isolated data.
    """

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Contact information
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Clinic information
    clinic_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinic_address: Mapped[str | None] = mapped_column(Text, nullable=True)  # Legacy field

    # === PHASE 1: Essential Clinic Fields ===

    # Clinic contact details (separate from owner)
    clinic_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    clinic_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinic_whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Structured address
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Geographic location (Bangladesh)
    division_id: Mapped[int | None] = mapped_column(nullable=True)
    district_id: Mapped[int | None] = mapped_column(nullable=True)
    upazila_id: Mapped[int | None] = mapped_column(nullable=True)

    # Geolocation for maps
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Professional credentials (beyond license)
    registration_body: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., BMDC, Bangladesh Homeopathic Board"
    )
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(nullable=True)

    # Fees (stored in paisa: 100 paisa = 1 BDT)
    consultation_fee: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Fee in paisa (100 paisa = 1 BDT)"
    )
    follow_up_fee: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Follow-up fee in paisa"
    )

    # Medical specializations (1-4 systems)
    # Options: homeopathy, ayurveda, unani, herbal
    specializations: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        server_default="{}",
    )

    # License and verification
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Subscription
    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
    )  # free, plus, pro
    plan_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="tenant")


class User(BaseAuditModel):
    """
    User model - can be platform admin/operator or tenant-scoped doctor/receptionist.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Tenant association (NULL for platform admins/operators)
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )

    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role: admin, operator (platform), doctor, receptionist (tenant-scoped)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 2FA
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    totp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Preferences
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
    )  # en, bn

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Token version for JWT invalidation
    # Incremented on password change, email change, or role change to invalidate old tokens
    token_version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        server_default="1",
    )

    # Relationships
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="users")
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user")


class UserSession(BaseAuditModel):
    """User session tracking for security and analytics."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session data
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Status
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
