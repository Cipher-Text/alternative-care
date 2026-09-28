"""rename colleges catalog to institutions

Revision ID: 9f1a3c7d2b6e
Revises: 076ccd9eccdd
Create Date: 2026-09-28 16:00:00.000000

The catalog's generic name is "institution" (it holds every type of
educational institution, not only colleges) — matches the existing
`doctor_degrees.institution_name`/`institution_location` free-text fields
this table cross-references. Forward-only rename (not folded into the
`43b02e1aad5f` migration it corrects) since that migration already ran
against local dev; rewriting applied history would desync it from what's
actually in the database.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9f1a3c7d2b6e'
down_revision: Union[str, None] = '076ccd9eccdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("colleges", "institutions")
    op.alter_column("institutions", "college_type", new_column_name="institution_type")
    op.execute("ALTER INDEX ix_colleges_name_en RENAME TO ix_institutions_name_en")
    op.execute("ALTER INDEX ix_colleges_district_id RENAME TO ix_institutions_district_id")
    op.execute(
        "ALTER TABLE institutions RENAME CONSTRAINT fk_colleges_district_id_districts "
        "TO fk_institutions_district_id_districts"
    )

    op.alter_column("doctor_degrees", "college_id", new_column_name="institution_id")
    op.execute(
        "ALTER INDEX ix_doctor_degrees_college_id RENAME TO ix_doctor_degrees_institution_id"
    )
    op.execute(
        "ALTER TABLE doctor_degrees RENAME CONSTRAINT fk_doctor_degrees_college_id_colleges "
        "TO fk_doctor_degrees_institution_id_institutions"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE doctor_degrees RENAME CONSTRAINT fk_doctor_degrees_institution_id_institutions "
        "TO fk_doctor_degrees_college_id_colleges"
    )
    op.execute(
        "ALTER INDEX ix_doctor_degrees_institution_id RENAME TO ix_doctor_degrees_college_id"
    )
    op.alter_column("doctor_degrees", "institution_id", new_column_name="college_id")

    op.execute(
        "ALTER TABLE institutions RENAME CONSTRAINT fk_institutions_district_id_districts "
        "TO fk_colleges_district_id_districts"
    )
    op.execute("ALTER INDEX ix_institutions_district_id RENAME TO ix_colleges_district_id")
    op.execute("ALTER INDEX ix_institutions_name_en RENAME TO ix_colleges_name_en")
    op.alter_column("institutions", "institution_type", new_column_name="college_type")
    op.rename_table("institutions", "colleges")
