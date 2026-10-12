"""add contact_messages (public contact form)

Revision ID: a7c4e1f9d2b8
Revises: f6b3e9a2c4d7
Create Date: 2026-10-13 13:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c4e1f9d2b8"
down_revision: Union[str, None] = "f6b3e9a2c4d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("topic", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("organisation", sa.String(length=150), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="new"),
        sa.Column("handled_by", sa.String(length=36), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "topic IN ('general','enterprise','billing','report_profile','other')",
            name="ck_contact_message_topic",
        ),
        sa.CheckConstraint("status IN ('new','handled')", name="ck_contact_message_status"),
    )
    op.create_index("ix_contact_messages_topic", "contact_messages", ["topic"])
    op.create_index("ix_contact_messages_status", "contact_messages", ["status"])


def downgrade() -> None:
    op.drop_table("contact_messages")
