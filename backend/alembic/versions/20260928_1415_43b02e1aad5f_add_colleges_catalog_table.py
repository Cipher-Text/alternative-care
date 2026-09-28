"""add colleges catalog table

Revision ID: 43b02e1aad5f
Revises: d36407b8b27e
Create Date: 2026-09-28 14:15:11.154426

Track D (docs/planning/future-scope-2026-09.md) — admin-curated directory
of institutions teaching alternative-medicine disciplines. Always global,
never tenant-owned: colleges aren't tenants, so unlike `medicines`/
`symptoms` this is a plain new catalog table, not a hybrid global-or-tenant
one — no `tenant_id` column, no CHECK constraint pairing it with `is_global`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43b02e1aad5f'
down_revision: Union[str, None] = 'd36407b8b27e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "colleges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_en", sa.String(length=500), nullable=False),
        sa.Column("name_bn", sa.String(length=500), nullable=True),
        sa.Column("college_type", sa.String(length=20), nullable=False),
        sa.Column(
            "disciplines",
            sa.ARRAY(sa.String(length=50)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("courses_offered", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_colleges_name_en", "colleges", ["name_en"])


def downgrade() -> None:
    op.drop_index("ix_colleges_name_en", table_name="colleges")
    op.drop_table("colleges")
