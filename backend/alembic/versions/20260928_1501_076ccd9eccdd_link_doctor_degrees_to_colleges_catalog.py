"""link doctor degrees to colleges catalog

Revision ID: 076ccd9eccdd
Revises: 5c4976e9ea39
Create Date: 2026-09-28 15:01:58.507011

Adds `doctor_degrees.college_id`, an optional structured cross-reference
into the colleges catalog (Track D). `institution_name`/`institution_location`
stay the source of truth and required — a degree's institution may not be
in the curated catalog yet (foreign-trained doctors, MBBS holders, etc.) —
this is additive, not a replacement.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '076ccd9eccdd'
down_revision: Union[str, None] = '5c4976e9ea39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("doctor_degrees", sa.Column("college_id", sa.Integer(), nullable=True))
    op.create_index("ix_doctor_degrees_college_id", "doctor_degrees", ["college_id"])
    op.create_foreign_key(
        "fk_doctor_degrees_college_id_colleges",
        "doctor_degrees",
        "colleges",
        ["college_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_doctor_degrees_college_id_colleges", "doctor_degrees", type_="foreignkey")
    op.drop_index("ix_doctor_degrees_college_id", table_name="doctor_degrees")
    op.drop_column("doctor_degrees", "college_id")
