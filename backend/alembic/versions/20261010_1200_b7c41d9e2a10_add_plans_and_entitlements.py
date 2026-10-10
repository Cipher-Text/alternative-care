"""add plans, plan entitlements, tenant overrides and plan audit log

Revision ID: b7c41d9e2a10
Revises: 9f1a3c7d2b6e
Create Date: 2026-10-10 12:00:00.000000

Rows are not seeded here: defaults live in app/core/entitlements.py and are materialised the
first time an admin opens the Plans page, so there is a single source for default values.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'b7c41d9e2a10'
down_revision: Union[str, None] = '9f1a3c7d2b6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        'plans',
        sa.Column('key', sa.String(20), primary_key=True),
        sa.Column('name_en', sa.String(100), nullable=False),
        sa.Column('name_bn', sa.String(100), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_bn', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_yearly', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='BDT'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        *_audit_columns(),
    )
    op.create_table(
        'plan_entitlements',
        sa.Column('plan_key', sa.String(20), sa.ForeignKey('plans.key', ondelete='CASCADE'), primary_key=True),
        sa.Column('entitlement_key', sa.String(50), primary_key=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('limit_value', sa.Integer(), nullable=True),
        *_audit_columns(),
    )
    op.create_table(
        'tenant_entitlement_overrides',
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('entitlement_key', sa.String(50), primary_key=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('limit_value', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        *_audit_columns(),
    )
    op.create_table(
        'plan_audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('plan_key', sa.String(20), nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('entitlement_key', sa.String(50), nullable=True),
        sa.Column('field', sa.String(50), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(36), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_plan_audit_log_plan_key', 'plan_audit_log', ['plan_key'])
    op.create_index('ix_plan_audit_log_tenant_id', 'plan_audit_log', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_plan_audit_log_tenant_id', table_name='plan_audit_log')
    op.drop_index('ix_plan_audit_log_plan_key', table_name='plan_audit_log')
    op.drop_table('plan_audit_log')
    op.drop_table('tenant_entitlement_overrides')
    op.drop_table('plan_entitlements')
    op.drop_table('plans')
