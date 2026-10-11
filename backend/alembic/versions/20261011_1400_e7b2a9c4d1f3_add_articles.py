"""add articles (editorial content with review workflow)

Revision ID: e7b2a9c4d1f3
Revises: d5a8c3f1e7b2
Create Date: 2026-10-11 14:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7b2a9c4d1f3"
down_revision: Union[str, None] = "d5a8c3f1e7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="article"),
        sa.Column("discipline", sa.String(length=20), nullable=False, server_default="general"),
        sa.Column("evidence_label", sa.String(length=20), nullable=False, server_default="general_info"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("title_en", sa.String(length=300), nullable=True),
        sa.Column("title_bn", sa.String(length=300), nullable=True),
        sa.Column("summary_en", sa.Text(), nullable=True),
        sa.Column("summary_bn", sa.Text(), nullable=True),
        sa.Column("body_en", sa.Text(), nullable=True),
        sa.Column("body_bn", sa.Text(), nullable=True),
        sa.Column("youtube_id", sa.String(length=20), nullable=True),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), nullable=True),
        sa.Column("reviewer_display", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("review_due_at", sa.Date(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.CheckConstraint("status IN ('draft','in_review','published')", name="ck_articles_status"),
        sa.CheckConstraint("kind IN ('article','video')", name="ck_articles_kind"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=True)
    op.create_index("ix_articles_discipline", "articles", ["discipline"])
    op.create_index("ix_articles_status", "articles", ["status"])
    op.create_index("ix_articles_author_id", "articles", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_articles_author_id", table_name="articles")
    op.drop_index("ix_articles_status", table_name="articles")
    op.drop_index("ix_articles_discipline", table_name="articles")
    op.drop_index("ix_articles_slug", table_name="articles")
    op.drop_table("articles")
