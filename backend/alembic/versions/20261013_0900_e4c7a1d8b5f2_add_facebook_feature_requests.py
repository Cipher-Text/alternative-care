"""add facebook_feature_requests (staff-run Facebook profile promotion)

Revision ID: e4c7a1d8b5f2
Revises: d2a8e4b6f1c7
Create Date: 2026-10-13 09:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4c7a1d8b5f2"
down_revision: Union[str, None] = "d2a8e4b6f1c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facebook_feature_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="requested"),
        sa.Column("requested_by", sa.String(length=36), nullable=False),
        sa.Column("doctor_note", sa.Text(), nullable=True),
        sa.Column("draft_text", sa.Text(), nullable=True),
        sa.Column("drafted_by", sa.String(length=36), nullable=True),
        sa.Column("drafted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("doctor_comment", sa.Text(), nullable=True),
        sa.Column("approved_text", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("post_url", sa.String(length=500), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["practitioner_listings.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('requested','drafted','approved','posted','rejected','cancelled')",
            name="ck_fb_request_status",
        ),
    )
    op.create_index("ix_facebook_feature_requests_tenant_id", "facebook_feature_requests", ["tenant_id"])
    op.create_index("ix_facebook_feature_requests_status", "facebook_feature_requests", ["status"])
    op.create_index(
        "ix_fb_requests_tenant_created", "facebook_feature_requests", ["tenant_id", "created_at"]
    )
    # At most one open request per clinic
    op.create_index(
        "uq_fb_request_one_open",
        "facebook_feature_requests",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('requested','drafted','approved')"),
    )


def downgrade() -> None:
    op.drop_table("facebook_feature_requests")
