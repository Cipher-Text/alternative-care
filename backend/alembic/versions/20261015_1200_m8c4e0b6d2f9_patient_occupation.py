"""Patients get an occupation (the paper case form's "পেশা")

Revision ID: m8c4e0b6d2f9
Revises: l7b3d9a5c1e8
Create Date: 2026-10-15 12:00:00

A short free-text field on the patient, optional. It sits on the patient record rather than in a system's case profile
because every system's first page asks for it.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m8c4e0b6d2f9"
down_revision: Union[str, None] = "l7b3d9a5c1e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("occupation", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("patients", "occupation")
