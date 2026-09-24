"""usage_tracking: add sms_sent counter and unique (tenant_id, usage_date)

Revision ID: ed07cf4aebc7
Revises: ba209a25bf7d
Create Date: 2026-09-24 21:00:00.000000

Stage 1 "Billing enforcement" (docs/planning/revision-2026-09.md). SMS send
is one of the three named usage-tracking write points but the table has no
counter for it. The unique constraint on (tenant_id, usage_date) lets the
get-or-create write path in app/core/usage_tracking.py rely on a DB-level
conflict instead of a check-then-insert race between concurrent requests
for the same tenant on the same day.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed07cf4aebc7'
down_revision: Union[str, None] = 'ba209a25bf7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'usage_tracking',
        sa.Column('sms_sent', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_unique_constraint(
        'uq_usage_tracking_tenant_date', 'usage_tracking', ['tenant_id', 'usage_date']
    )


def downgrade() -> None:
    op.drop_constraint('uq_usage_tracking_tenant_date', 'usage_tracking', type_='unique')
    op.drop_column('usage_tracking', 'sms_sent')
