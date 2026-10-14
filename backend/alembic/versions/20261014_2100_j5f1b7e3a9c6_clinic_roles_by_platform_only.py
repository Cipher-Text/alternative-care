"""Clinic staff and roles are managed by the platform only (ADR 010, Phase 3 revised)

Revision ID: j5f1b7e3a9c6
Revises: i4e0a6d2f8b5
Create Date: 2026-10-14 21:00:00

The clinic permission `team.manage` is removed from the catalogue and the platform permission `clinic_roles.manage`
added. Re-running the catalogue sync drops `team.manage` from every role that held it (the cascade removes the
`role_permissions` rows) and gives the platform admin role the new permission. A clinic that needs staff or role changes
asks AltCare. Clinic-made roles stay; the platform can edit them.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "j5f1b7e3a9c6"
down_revision: Union[str, None] = "i4e0a6d2f8b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.core.rbac import sync_catalogue

    sync_catalogue(op.get_bind())


def downgrade() -> None:
    # The catalogue lives in code; the previous code's sync restores `team.manage`. Nothing to undo here.
    pass
