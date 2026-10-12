"""add patient identity (ADR 009 phase 1): accounts, profiles, OTP challenges, links, consent log, claim codes

Revision ID: b9d5f2a8c1e6
Revises: a7c4e1f9d2b8
Create Date: 2026-10-13 15:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b9d5f2a8c1e6"
down_revision: Union[str, None] = "a7c4e1f9d2b8"
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
    op.create_table(
        "person_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="active"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_accounts_phone", "person_accounts", ["phone"], unique=True)

    op.create_table(
        "person_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("approx_birth_year", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("division_id", sa.Integer(), nullable=True),
        sa.Column("district_id", sa.Integer(), nullable=True),
        sa.Column("upazila_id", sa.Integer(), nullable=True),
        sa.Column("relationship", sa.String(length=10), nullable=False, server_default="self"),
        sa.Column("is_dependent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="active"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["person_accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "relationship IN ('self','child','spouse','parent','other')", name="ck_person_profile_relationship"
        ),
    )
    op.create_index("ix_person_profiles_account_id", "person_profiles", ["account_id"])
    op.create_index("ix_person_profiles_name_key", "person_profiles", ["name_key"])

    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("purpose", sa.String(length=15), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.Column("requested_by", sa.String(length=36), nullable=True),
        sa.Column("claim_code_id", sa.String(length=36), nullable=True),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="sent"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("search_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("link_count", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint("purpose IN ('clinic_verify','claim')", name="ck_otp_challenge_purpose"),
    )
    op.create_index("ix_otp_challenges_phone_created", "otp_challenges", ["phone", "created_at"])
    op.create_index("ix_otp_challenges_tenant_created", "otp_challenges", ["tenant_id", "created_at"])
    op.create_index("ix_otp_challenges_token_hash", "otp_challenges", ["token_hash"])

    op.create_table(
        "identity_consent_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("method", sa.String(length=15), nullable=False),
        sa.Column("staff_user_id", sa.String(length=36), nullable=True),
        sa.Column("script_version", sa.String(length=20), nullable=False),
        sa.Column("staff_confirmed_told", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("otp_challenge_id", sa.String(length=36), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint("kind IN ('link','revoke')", name="ck_identity_consent_kind"),
    )
    op.create_index("ix_identity_consent_events_tenant_id", "identity_consent_events", ["tenant_id"])
    op.create_index("ix_identity_consent_events_profile_id", "identity_consent_events", ["profile_id"])

    op.create_table(
        "patient_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("method", sa.String(length=15), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="linked"),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("linked_by", sa.String(length=36), nullable=True),
        sa.Column("consent_event_id", sa.String(length=36), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(length=36), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["person_profiles.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('linked','revoked')", name="ck_patient_link_status"),
        sa.CheckConstraint("method IN ('clinic_otp','claim_code')", name="ck_patient_link_method"),
    )
    op.create_index("ix_patient_links_tenant_id", "patient_links", ["tenant_id"])
    op.create_index("ix_patient_links_patient_id", "patient_links", ["patient_id"])
    op.create_index("ix_patient_links_profile_id", "patient_links", ["profile_id"])
    op.create_index(
        "uq_patient_link_one_active_per_patient", "patient_links", ["tenant_id", "patient_id"],
        unique=True, postgresql_where=sa.text("status = 'linked'"),
    )
    op.create_index(
        "uq_patient_link_one_active_per_profile", "patient_links", ["tenant_id", "profile_id"],
        unique=True, postgresql_where=sa.text("status = 'linked'"),
    )

    op.create_table(
        "identity_claim_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_identity_claim_codes_tenant_id", "identity_claim_codes", ["tenant_id"])
    op.create_index("ix_identity_claim_codes_patient_id", "identity_claim_codes", ["patient_id"])
    op.create_index("ix_identity_claim_codes_code_hash", "identity_claim_codes", ["code_hash"], unique=True)


def downgrade() -> None:
    for table in (
        "identity_claim_codes", "patient_links", "identity_consent_events",
        "otp_challenges", "person_profiles", "person_accounts",
    ):
        op.drop_table(table)
