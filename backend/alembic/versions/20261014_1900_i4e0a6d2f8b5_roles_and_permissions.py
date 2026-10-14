"""Roles and permissions as data (ADR 010, Phase 1)

Revision ID: i4e0a6d2f8b5
Revises: h3d9f5c1e7a4
Create Date: 2026-10-14 19:00:00

Adds `permissions`, `roles`, `role_permissions`, `user_roles` and `role_audit_log`; loads the permission catalogue and
the four system roles from app/core/permissions.py (the same routine runs on every deploy, so a later change to the
catalogue ships as a new migration that calls it again); and gives every existing user the system role named by
`users.role`. Nothing reads these tables for access decisions yet except `GET /auth/me/permissions`: behaviour is
unchanged. `users.role` stays as the source of truth until Phase 4.

`roles` carries the clinic row-level-security policy (clinic roles are visible only to their clinic; global roles to
everyone). `role_permissions` and `user_roles` hold no clinic id and are reachable only through `roles`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i4e0a6d2f8b5"
down_revision: Union[str, None] = "h3d9f5c1e7a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("key", sa.String(60), primary_key=True),
        sa.Column("scope", sa.String(10), nullable=False),
        sa.Column("module", sa.String(30), nullable=False),
        sa.Column("description_en", sa.String(200), nullable=False),
        sa.Column("description_bn", sa.String(300), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("scope IN ('platform','tenant')", name="ck_permission_scope"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("name_bn", sa.String(100), nullable=False),
        sa.Column("scope", sa.String(10), nullable=False),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("based_on_role_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.CheckConstraint("scope IN ('platform','tenant')", name="ck_role_scope"),
        sa.CheckConstraint("scope = 'tenant' OR tenant_id IS NULL", name="ck_role_platform_is_global"),
    )
    op.create_index("uq_role_global_key", "roles", ["key"], unique=True, postgresql_where=sa.text("tenant_id IS NULL"))
    op.create_index("uq_role_tenant_key", "roles", ["tenant_id", "key"], unique=True, postgresql_where=sa.text("tenant_id IS NOT NULL"))
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_key", sa.String(60), sa.ForeignKey("permissions.key", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("granted_by", sa.String(36), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_table(
        "role_audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("actor_user_id", sa.String(36), nullable=True),
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
        sa.Column("role_id", sa.String(36), nullable=True, index=True),
        sa.Column("user_id", sa.String(36), nullable=True, index=True),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
    )

    op.execute(sa.text("ALTER TABLE roles ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE roles FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(
            "CREATE POLICY tenant_isolation ON roles "
            "USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true))"
        )
    )

    # Load the catalogue and the system roles, then give every existing user their role
    from app.core.rbac import sync_catalogue

    sync_catalogue(op.get_bind())
    op.execute(
        sa.text(
            "INSERT INTO user_roles (user_id, role_id, granted_at) "
            "SELECT u.id, r.id, now() FROM users u "
            "JOIN roles r ON r.key = u.role AND r.tenant_id IS NULL AND r.is_system "
            "ON CONFLICT DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_table("role_audit_log")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
