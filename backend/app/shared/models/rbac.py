"""Roles and permissions as data (ADR 010).

`permissions` mirrors the catalogue in app/core/permissions.py. `roles` are global (`tenant_id` null: the four system
roles and any platform staff roles) or specific to one clinic. A user holds one or more roles through `user_roles`.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, event, func, inspect, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import BaseAuditModel


class PermissionRow(Base):
    __tablename__ = "permissions"
    __table_args__ = (CheckConstraint("scope IN ('platform','tenant')", name="ck_permission_scope"),)

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    module: Mapped[str] = mapped_column(String(30), nullable=False)
    description_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_bn: Mapped[str] = mapped_column(String(300), nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Role(BaseAuditModel):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("scope IN ('platform','tenant')", name="ck_role_scope"),
        # A platform role is always global
        CheckConstraint("scope = 'tenant' OR tenant_id IS NULL", name="ck_role_platform_is_global"),
        # A key is unique among the global roles, and unique within one clinic's own roles
        Index("uq_role_global_key", "key", unique=True, postgresql_where=text("tenant_id IS NULL")),
        Index("uq_role_tenant_key", "tenant_id", "key", unique=True, postgresql_where=text("tenant_id IS NOT NULL")),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    based_on_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_key: Mapped[str] = mapped_column(ForeignKey("permissions.key", ondelete="CASCADE"), primary_key=True)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    granted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RoleAuditLog(Base):
    """Who changed which role or assignment, with the before and after."""

    __tablename__ = "role_audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    role_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)


# ----- keep user_roles in step with users.role (until users.role is retired in ADR 010, Phase 4) -----------------
# Any code that creates a user or changes users.role through the ORM keeps the assignment right without being edited.

from app.shared.models.tenant import User  # noqa: E402


@event.listens_for(User, "after_insert")
def _user_inserted(mapper, connection, user):  # noqa: ARG001
    from app.core.rbac import assign_system_role

    assign_system_role(connection, user.id, user.role)


@event.listens_for(User, "after_update")
def _user_updated(mapper, connection, user):  # noqa: ARG001
    from app.core.rbac import assign_system_role

    if inspect(user).attrs.role.history.has_changes():
        assign_system_role(connection, user.id, user.role)
