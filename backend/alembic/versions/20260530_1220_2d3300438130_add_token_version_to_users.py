"""add_token_version_to_users

Revision ID: 2d3300438130
Revises: 14e7d549acce
Create Date: 2026-05-30 12:20:45.899610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d3300438130'
down_revision: Union[str, None] = '14e7d549acce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add token_version column to users table for JWT invalidation."""
    # Add token_version column with default value 1
    op.add_column(
        'users',
        sa.Column('token_version', sa.Integer(), nullable=False, server_default='1')
    )

    # Update existing users to have token_version = 1
    # (server_default handles this automatically on PostgreSQL)


def downgrade() -> None:
    """Remove token_version column from users table."""
    op.drop_column('users', 'token_version')
