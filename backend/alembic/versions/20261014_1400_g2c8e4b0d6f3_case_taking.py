"""Case-taking answers: patient case profiles and visit assessments

Revision ID: g2c8e4b0d6f3
Revises: f1b7d3a9c5e2
Create Date: 2026-10-14 14:00:00

Step 3 of structured health history (homeopathy first). Answers are JSON under fixed keys validated by the
registry in app/shared/case_taking, so adding a field never needs a migration. Both tables are
tenant-isolated like the other clinical tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g2c8e4b0d6f3"
down_revision: Union[str, None] = "f1b7d3a9c5e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "patient_case_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("system", sa.String(20), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        *_audit(),
        sa.UniqueConstraint("patient_id", "system", name="uq_patient_case_profile"),
    )
    op.create_table(
        "visit_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("visit_id", sa.String(36), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("system", sa.String(20), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        *_audit(),
        sa.UniqueConstraint("visit_id", "system", name="uq_visit_assessment"),
    )
    for table in ("patient_case_profiles", "visit_assessments"):
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(f"CREATE POLICY tenant_isolation ON {table} USING (tenant_id = current_setting('app.tenant_id', true))")
        )


def downgrade() -> None:
    op.drop_table("visit_assessments")
    op.drop_table("patient_case_profiles")
