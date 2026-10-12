"""appointment requests (ADR 009 phase 3): patients request appointments, clinics confirm

Revision ID: d6f1b8c3a5e7
Revises: c3e7a9f4b1d2
Create Date: 2026-10-13 19:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d6f1b8c3a5e7"
down_revision: Union[str, None] = "c3e7a9f4b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("person_profiles", sa.Column("source", sa.String(length=10), nullable=False, server_default="clinic"))
    op.drop_constraint("ck_patient_link_method", "patient_links", type_="check")
    op.create_check_constraint(
        "ck_patient_link_method", "patient_links", "method IN ('clinic_otp','claim_code','appointment')"
    )
    op.create_table(
        "appointment_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=True),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="requested"),
        sa.Column("preferred_date", sa.Date(), nullable=False),
        sa.Column("preferred_window", sa.String(length=10), nullable=False, server_default="any"),
        sa.Column("reason", sa.String(length=300), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=True),
        sa.Column("appointment_id", sa.String(length=36), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_by", sa.String(length=36), nullable=True),
        sa.Column("decline_reason", sa.String(length=500), nullable=True),
        sa.Column("cancelled_by", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["practitioner_listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["account_id"], ["person_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["person_profiles.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('requested','confirmed','declined','cancelled')", name="ck_appointment_request_status"
        ),
        sa.CheckConstraint(
            "preferred_window IN ('morning','afternoon','evening','any')", name="ck_appointment_request_window"
        ),
    )
    op.create_index("ix_appointment_requests_tenant_id", "appointment_requests", ["tenant_id"])
    op.create_index("ix_appointment_requests_account_id", "appointment_requests", ["account_id"])
    op.create_index("ix_appointment_requests_profile_id", "appointment_requests", ["profile_id"])
    op.create_index("ix_appointment_requests_status", "appointment_requests", ["status"])
    op.create_index("ix_appointment_requests_tenant_created", "appointment_requests", ["tenant_id", "created_at"])
    op.create_index(
        "uq_appointment_request_one_open", "appointment_requests", ["tenant_id", "profile_id"],
        unique=True, postgresql_where=sa.text("status = 'requested'"),
    )


def downgrade() -> None:
    op.drop_table("appointment_requests")
    op.execute("DELETE FROM patient_links WHERE method = 'appointment'")
    op.drop_constraint("ck_patient_link_method", "patient_links", type_="check")
    op.create_check_constraint("ck_patient_link_method", "patient_links", "method IN ('clinic_otp','claim_code')")
    op.drop_column("person_profiles", "source")
