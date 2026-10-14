"""Remove per-clinic integrations; the integration log becomes the message log

Revision ID: h3d9f5c1e7a4
Revises: g2c8e4b0d6f3
Create Date: 2026-10-14 17:00:00

Clinics no longer connect their own SMS, email or payment providers: they collect cash, and the platform sends
SMS and email for them (charged as messaging credits). So:

- `tenant_integrations` (a clinic's encrypted provider credentials) and `integration_providers` (the provider
  catalogue) are dropped.
- `integration_logs` is kept as the log of messages the platform sent for a clinic, renamed `message_logs`; its
  per-clinic integration id and the payment-only amount and currency columns are dropped.

Downgrade recreates the two dropped tables EMPTY: their rows (and every stored credential) are not restored.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h3d9f5c1e7a4"
down_revision: Union[str, None] = "g2c8e4b0d6f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RENAMES = (
    ("INDEX", "ix_integration_logs_status", "ix_message_logs_status"),
    ("INDEX", "ix_integration_logs_tenant_id", "ix_message_logs_tenant_id"),
    ("INDEX", "ix_integration_logs_transaction_type", "ix_message_logs_transaction_type"),
    ("INDEX", "integration_logs_pkey", "message_logs_pkey"),
    ("SEQUENCE", "integration_logs_id_seq", "message_logs_id_seq"),
)


def upgrade() -> None:
    op.drop_table("tenant_integrations")
    op.drop_table("integration_providers")

    op.drop_index("ix_integration_logs_tenant_integration_id", table_name="integration_logs")
    op.drop_column("integration_logs", "tenant_integration_id")
    op.drop_column("integration_logs", "amount")
    op.drop_column("integration_logs", "currency")

    op.rename_table("integration_logs", "message_logs")
    for kind, old, new in _RENAMES:
        op.execute(sa.text(f"ALTER {kind} {old} RENAME TO {new}"))
    op.execute(sa.text("ALTER TABLE message_logs RENAME CONSTRAINT fk_integration_logs_tenant_id TO fk_message_logs_tenant_id"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE message_logs RENAME CONSTRAINT fk_message_logs_tenant_id TO fk_integration_logs_tenant_id"))
    for kind, old, new in reversed(_RENAMES):
        op.execute(sa.text(f"ALTER {kind} {new} RENAME TO {old}"))
    op.rename_table("message_logs", "integration_logs")

    op.add_column("integration_logs", sa.Column("currency", sa.String(3), nullable=True))
    op.add_column("integration_logs", sa.Column("amount", sa.Integer(), nullable=True))
    op.add_column("integration_logs", sa.Column("tenant_integration_id", sa.Integer(), nullable=True))
    op.create_index("ix_integration_logs_tenant_integration_id", "integration_logs", ["tenant_integration_id"])

    op.create_table(
        "integration_providers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("config_schema", sa.JSON(), nullable=True),
        sa.Column("supported_countries", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "tenant_integrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_id", sa.Integer(), nullable=False, index=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("test_status", sa.String(20), nullable=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE", name="fk_tenant_integrations_tenant_id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
    )
