"""data shares (ADR 009 phase 4): a patient lets one clinic read another clinic's records about them

Revision ID: e8a2c5d7f1b3
Revises: d6f1b8c3a5e7
Create Date: 2026-10-14 09:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8a2c5d7f1b3"
down_revision: Union[str, None] = "d6f1b8c3a5e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
    ]


def upgrade() -> None:
    op.drop_constraint("ck_identity_consent_kind", "identity_consent_events", type_="check")
    op.create_check_constraint(
        "ck_identity_consent_kind", "identity_consent_events",
        "kind IN ('link','revoke','portal_access','share_grant','share_revoke')",
    )
    op.create_table(
        "data_shares",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("source_link_id", sa.String(length=36), nullable=False),
        sa.Column("recipient_link_id", sa.String(length=36), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_event_id", sa.String(length=36), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["person_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["person_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_link_id"], ["patient_links.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_link_id"], ["patient_links.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('active','revoked')", name="ck_data_share_status"),
        sa.CheckConstraint("source_link_id <> recipient_link_id", name="ck_data_share_distinct_links"),
    )
    for col in ("account_id", "profile_id", "source_link_id", "recipient_link_id"):
        op.create_index(f"ix_data_shares_{col}", "data_shares", [col])
    op.create_index(
        "uq_data_share_one_active_per_pair", "data_shares", ["source_link_id", "recipient_link_id"],
        unique=True, postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "data_share_access",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("share_id", sa.String(length=36), nullable=False),
        sa.Column("recipient_tenant_id", sa.String(length=36), nullable=False),
        sa.Column("staff_user_id", sa.String(length=36), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["share_id"], ["data_shares.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_data_share_access_share_id", "data_share_access", ["share_id"])


def downgrade() -> None:
    op.drop_table("data_share_access")
    op.drop_table("data_shares")
    op.execute("DELETE FROM identity_consent_events WHERE kind IN ('share_grant','share_revoke')")
    op.drop_constraint("ck_identity_consent_kind", "identity_consent_events", type_="check")
    op.create_check_constraint(
        "ck_identity_consent_kind", "identity_consent_events", "kind IN ('link','revoke','portal_access')"
    )
