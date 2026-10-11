"""add botanical name to medicines

Revision ID: 4c91a7d2e6b0
Revises: c8d52e0f3b21
Create Date: 2026-10-11 09:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "4c91a7d2e6b0"
down_revision: Union[str, None] = "c8d52e0f3b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("medicines", sa.Column("botanical_name", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("medicines", "botanical_name")
