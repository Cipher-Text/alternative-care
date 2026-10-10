"""clear placeholder pdf_url values

Revision ID: c8d52e0f3b21
Revises: b7c41d9e2a10
Create Date: 2026-10-10 17:00:00.000000

Before real PDF rendering existed, issuing a PDF stored a made-up
`https://storage.example.com/...` link. Documents are now rendered on demand and not stored, so
those links are dead and misleading. Data-only; nothing to restore on downgrade.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c8d52e0f3b21'
down_revision: Union[str, None] = 'b7c41d9e2a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("prescriptions", "invoices"):
        op.execute(
            f"UPDATE {table} SET pdf_url = NULL, pdf_generated_at = NULL "
            "WHERE pdf_url LIKE 'https://storage.example.com/%'"
            if table == "prescriptions"
            else f"UPDATE {table} SET pdf_url = NULL WHERE pdf_url LIKE 'https://storage.example.com/%'"
        )


def downgrade() -> None:
    pass
