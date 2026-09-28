"""add college registration code

Revision ID: 5bb63dbcb9a4
Revises: 43b02e1aad5f
Create Date: 2026-09-28 14:22:34.020189

The issuing board's own registration/code number for a college (e.g. the
Bangladesh Homeopathic Medical Education Council's 3-digit college code,
https://bhmec.gov.bd/home/colleges). Not made unique: that register itself
has been observed reusing one code (029) across two differently named
colleges, so this column is provenance, not a candidate key.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5bb63dbcb9a4'
down_revision: Union[str, None] = '43b02e1aad5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("colleges", sa.Column("registration_code", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("colleges", "registration_code")
