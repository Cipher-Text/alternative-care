"""add messaging credits (balances, ledger), emails_sent usage, platform-sent integration logs

Revision ID: a4d9e2c7b6f1
Revises: f3c8d5a1b9e4
Create Date: 2026-10-12 16:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4d9e2c7b6f1"
down_revision: Union[str, None] = "f3c8d5a1b9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_tracking",
        sa.Column("emails_sent", sa.Integer(), nullable=False, server_default="0"),
    )
    # Sends through the platform's own providers have no per-clinic integration row
    op.alter_column("integration_logs", "tenant_integration_id", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "credit_balances",
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("channel", sa.String(length=10), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "channel"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint("balance >= 0", name="ck_credit_balance_nonneg"),
        sa.CheckConstraint("channel IN ('sms','email')", name="ck_credit_balance_channel"),
    )
    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("channel", sa.String(length=10), nullable=False),
        sa.Column("kind", sa.String(length=12), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "kind IN ('purchase','use','refund','adjustment')", name="ck_credit_ledger_kind"
        ),
    )
    op.create_index("ix_credit_ledger_tenant_id", "credit_ledger", ["tenant_id"])
    op.create_index("ix_credit_ledger_created_at", "credit_ledger", ["created_at"])


def downgrade() -> None:
    op.drop_table("credit_ledger")
    op.drop_table("credit_balances")
    op.execute("DELETE FROM integration_logs WHERE tenant_integration_id IS NULL")
    op.alter_column("integration_logs", "tenant_integration_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("usage_tracking", "emails_sent")
