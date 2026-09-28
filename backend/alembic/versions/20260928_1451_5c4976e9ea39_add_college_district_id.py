"""add college district_id

Revision ID: 5c4976e9ea39
Revises: 5bb63dbcb9a4
Create Date: 2026-09-28 14:51:06.497269

Structured cross-reference from a college's free-text `location` to the
existing `districts` catalog, so a college can be filtered/joined by
district rather than only string-matched. Does not replace `location` —
the free text carries detail (ward, road, town) a district id can't.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c4976e9ea39'
down_revision: Union[str, None] = '5bb63dbcb9a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("colleges", sa.Column("district_id", sa.Integer(), nullable=True))
    op.create_index("ix_colleges_district_id", "colleges", ["district_id"])
    op.create_foreign_key(
        "fk_colleges_district_id_districts",
        "colleges",
        "districts",
        ["district_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_colleges_district_id_districts", "colleges", type_="foreignkey")
    op.drop_index("ix_colleges_district_id", table_name="colleges")
    op.drop_column("colleges", "district_id")
