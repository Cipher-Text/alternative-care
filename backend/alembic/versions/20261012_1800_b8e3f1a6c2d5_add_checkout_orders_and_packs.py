"""add checkout: credit packs and billing orders

Revision ID: b8e3f1a6c2d5
Revises: a4d9e2c7b6f1
Create Date: 2026-10-12 18:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8e3f1a6c2d5"
down_revision: Union[str, None] = "a4d9e2c7b6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "credit_packs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("channel", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BDT"),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("name_bn", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("channel IN ('sms','email')", name="ck_credit_pack_channel"),
        sa.CheckConstraint("quantity > 0", name="ck_credit_pack_quantity"),
        sa.CheckConstraint("price > 0", name="ck_credit_pack_price"),
    )
    op.create_table(
        "billing_orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("receipt_no", sa.String(length=30), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("payer_user_id", sa.String(length=36), nullable=False),
        sa.Column("payer_name", sa.String(length=255), nullable=False),
        sa.Column("payer_phone", sa.String(length=20), nullable=True),
        sa.Column("kind", sa.String(length=15), nullable=False),
        sa.Column("plan_key", sa.String(length=20), nullable=True),
        sa.Column("period", sa.String(length=10), nullable=True),
        sa.Column("pack_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=10), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BDT"),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="pending"),
        sa.Column("gateway", sa.String(length=20), nullable=False),
        sa.Column("gateway_txn_id", sa.String(length=100), nullable=True),
        sa.Column("gateway_data", sa.JSON(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilment", sa.JSON(), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pack_id"], ["credit_packs.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("receipt_no", name="uq_billing_orders_receipt_no"),
        sa.CheckConstraint("kind IN ('subscription','credit_pack')", name="ck_billing_order_kind"),
        sa.CheckConstraint(
            "status IN ('pending','paid','failed','cancelled','expired')", name="ck_billing_order_status"
        ),
    )
    op.create_index("ix_billing_orders_tenant_id", "billing_orders", ["tenant_id"])
    op.create_index("ix_billing_orders_status", "billing_orders", ["status"])
    op.create_index("ix_billing_orders_tenant_created", "billing_orders", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("billing_orders")
    op.drop_table("credit_packs")
