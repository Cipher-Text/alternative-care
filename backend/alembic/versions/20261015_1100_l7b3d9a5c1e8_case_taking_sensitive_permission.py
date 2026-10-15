"""Sensitive case-taking answers get their own permission, `case_taking.sensitive` (ADR 010)

Revision ID: l7b3d9a5c1e8
Revises: k6a2c8f4b0d7
Create Date: 2026-10-15 11:00:00

The paper homeopathy form asks about suicidal tendency and sexual and reproductive history. Those answers are shown and
saved only to people who hold this permission. Re-running the catalogue sync adds it and gives it to the Doctor role
(which holds every clinic-level permission); the Receptionist role does not get it.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "l7b3d9a5c1e8"
down_revision: Union[str, None] = "k6a2c8f4b0d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.core.rbac import sync_catalogue

    sync_catalogue(op.get_bind())


def downgrade() -> None:
    # The catalogue lives in code; the previous code's sync removes the permission. Nothing to undo here.
    pass
