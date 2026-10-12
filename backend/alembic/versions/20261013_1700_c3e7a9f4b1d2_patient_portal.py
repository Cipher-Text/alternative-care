"""patient portal (ADR 009 phase 2): portal registration, per-link portal access, portal codes

Revision ID: c3e7a9f4b1d2
Revises: b9d5f2a8c1e6
Create Date: 2026-10-13 17:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3e7a9f4b1d2"
down_revision: Union[str, None] = "b9d5f2a8c1e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("person_accounts", sa.Column("portal_registered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("patient_links", sa.Column("portal_access_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "identity_claim_codes",
        sa.Column("purpose", sa.String(length=10), nullable=False, server_default="link"),
    )
    op.add_column("identity_claim_codes", sa.Column("link_id", sa.String(length=36), nullable=True))

    op.drop_constraint("ck_otp_challenge_purpose", "otp_challenges", type_="check")
    op.create_check_constraint(
        "ck_otp_challenge_purpose", "otp_challenges", "purpose IN ('clinic_verify','claim','portal_login')"
    )
    op.alter_column("identity_consent_events", "kind", existing_type=sa.String(length=10), type_=sa.String(length=20))
    op.drop_constraint("ck_identity_consent_kind", "identity_consent_events", type_="check")
    op.create_check_constraint(
        "ck_identity_consent_kind", "identity_consent_events", "kind IN ('link','revoke','portal_access')"
    )


def downgrade() -> None:
    op.execute("DELETE FROM identity_consent_events WHERE kind = 'portal_access'")
    op.execute("DELETE FROM otp_challenges WHERE purpose = 'portal_login'")
    op.drop_constraint("ck_identity_consent_kind", "identity_consent_events", type_="check")
    op.create_check_constraint("ck_identity_consent_kind", "identity_consent_events", "kind IN ('link','revoke')")
    op.alter_column("identity_consent_events", "kind", existing_type=sa.String(length=20), type_=sa.String(length=10))
    op.drop_constraint("ck_otp_challenge_purpose", "otp_challenges", type_="check")
    op.create_check_constraint("ck_otp_challenge_purpose", "otp_challenges", "purpose IN ('clinic_verify','claim')")
    op.drop_column("identity_claim_codes", "link_id")
    op.drop_column("identity_claim_codes", "purpose")
    op.drop_column("patient_links", "portal_access_at")
    op.drop_column("person_accounts", "portal_registered_at")
