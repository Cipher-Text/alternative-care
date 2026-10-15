"""Homeopathy miasm is a multi-select: `dominant_miasm` (one) becomes `miasms` (a list)

Revision ID: k6a2c8f4b0d7
Revises: j5f1b7e3a9c6
Create Date: 2026-10-15 10:00:00

The paper case form ticks any of Psora, Sycosis, Syphilis and Tubercular, so the answer is now a list under `miasms`.
Saved homeopathy profiles are converted in place: "psora" becomes ["psora"]. The downgrade keeps the first tick.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k6a2c8f4b0d7"
down_revision: Union[str, None] = "j5f1b7e3a9c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE patient_case_profiles "
            "SET data = ((data::jsonb - 'dominant_miasm') || jsonb_build_object('miasms', jsonb_build_array(data::jsonb ->> 'dominant_miasm')))::json "
            "WHERE system = 'homeopathy' AND data::jsonb ? 'dominant_miasm'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE patient_case_profiles "
            "SET data = ((data::jsonb - 'miasms') || jsonb_build_object('dominant_miasm', data::jsonb -> 'miasms' ->> 0))::json "
            "WHERE system = 'homeopathy' AND data::jsonb ? 'miasms' AND jsonb_array_length(data::jsonb -> 'miasms') > 0"
        )
    )
