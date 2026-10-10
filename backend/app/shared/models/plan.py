"""Subscription plan configuration: plans, per-plan entitlements, per-tenant overrides, audit log.

Platform-level configuration (not tenant-scoped), edited by platform admins. The *set of
entitlement keys* is fixed in code (`app/core/entitlements.py`) because only code can enforce a
key; these tables hold the values (limits, on/off, prices).
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import BaseAuditModel


class Plan(BaseAuditModel):
    """A subscription plan (free / plus / pro). Keys match `tenants.plan`."""

    __tablename__ = "plans"

    key: Mapped[str] = mapped_column(String(20), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    # NULL price = "contact us" (no price approved yet)
    price_monthly: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_yearly: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BDT")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PlanEntitlement(BaseAuditModel):
    """One entitlement value for a plan. `limit_value` NULL means unlimited (limit kinds only)."""

    __tablename__ = "plan_entitlements"

    plan_key: Mapped[str] = mapped_column(
        ForeignKey("plans.key", ondelete="CASCADE"), primary_key=True
    )
    entitlement_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    limit_value: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TenantEntitlementOverride(BaseAuditModel):
    """Replaces one entitlement for one tenant (founding member, trial extension, ...)."""

    __tablename__ = "tenant_entitlement_overrides"

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    entitlement_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    limit_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlanAuditLog(Base):
    """Append-only history of plan and override changes."""

    __tablename__ = "plan_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_key: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    entitlement_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
