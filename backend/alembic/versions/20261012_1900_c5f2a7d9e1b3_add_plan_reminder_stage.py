"""add tenants.plan_reminder_stage (expiry reminder dedup)

Revision ID: c5f2a7d9e1b3
Revises: b8e3f1a6c2d5
Create Date: 2026-10-12 19:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5f2a7d9e1b3"
down_revision: Union[str, None] = "b8e3f1a6c2d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("plan_reminder_stage", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tenants", "plan_reminder_stage")
