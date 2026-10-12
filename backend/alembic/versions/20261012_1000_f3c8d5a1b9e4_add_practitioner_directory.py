"""add practitioner directory (listings, contact requests, listing events, tenant verification audit)

Revision ID: f3c8d5a1b9e4
Revises: e7b2a9c4d1f3
Create Date: 2026-10-12 10:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3c8d5a1b9e4"
down_revision: Union[str, None] = "e7b2a9c4d1f3"
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
    op.add_column("tenants", sa.Column("verified_by", sa.String(length=36), nullable=True))
    op.add_column("tenants", sa.Column("verification_note", sa.Text(), nullable=True))

    op.create_table(
        "practitioner_listings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("is_listed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("listed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("headline_en", sa.String(length=200), nullable=True),
        sa.Column("headline_bn", sa.String(length=200), nullable=True),
        sa.Column("bio_en", sa.Text(), nullable=True),
        sa.Column("bio_bn", sa.Text(), nullable=True),
        sa.Column("languages", postgresql.ARRAY(sa.String(length=30)), server_default="{}", nullable=False),
        sa.Column("consultation_hours", sa.String(length=500), nullable=True),
        sa.Column("availability", sa.String(length=10), nullable=False, server_default="in_person"),
        sa.Column("show_fee", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_phone", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_whatsapp", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("accepts_requests", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", name="uq_practitioner_listings_tenant"),
        sa.CheckConstraint("availability IN ('in_person','online','both')", name="ck_listing_availability"),
    )
    op.create_index("ix_practitioner_listings_slug", "practitioner_listings", ["slug"], unique=True)

    op.create_table(
        "contact_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=False),
        sa.Column("patient_name", sa.String(length=120), nullable=False),
        sa.Column("patient_phone", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("preferred_time", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="new"),
        sa.Column("consented_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["practitioner_listings.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('new','contacted','closed')", name="ck_contact_request_status"),
    )
    op.create_index("ix_contact_requests_tenant_id", "contact_requests", ["tenant_id"])
    op.create_index("ix_contact_requests_listing_id", "contact_requests", ["listing_id"])
    op.create_index("ix_contact_requests_status", "contact_requests", ["status"])
    op.create_index("ix_contact_requests_tenant_created", "contact_requests", ["tenant_id", "created_at"])

    op.create_table(
        "listing_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=10), nullable=False),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["listing_id"], ["practitioner_listings.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_listing_events_listing_created", "listing_events", ["listing_id", "created_at"])


def downgrade() -> None:
    op.drop_table("listing_events")
    op.drop_table("contact_requests")
    op.drop_table("practitioner_listings")
    op.drop_column("tenants", "verification_note")
    op.drop_column("tenants", "verified_by")
