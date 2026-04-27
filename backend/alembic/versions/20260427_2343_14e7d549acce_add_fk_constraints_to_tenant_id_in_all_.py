"""Add FK constraints to tenant_id in all tenant-scoped tables

Revision ID: 14e7d549acce
Revises: f2126bab5d62
Create Date: 2026-04-27 23:43:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14e7d549acce'
down_revision: Union[str, None] = 'f2126bab5d62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add FK constraints to tenant_id columns."""

    # List of tenant-scoped tables
    tenant_scoped_tables = [
        'patients',
        'patient_tags',
        'patient_diagnoses',
        'appointments',
        'visits',
        'prescriptions',
        'prescription_items',
        'payments',
        'invoices',
        'medicines',
        'medicine_aliases',
        'symptoms',
        'symptom_aliases',
        'medicine_symptom_mappings',
        'books',
        'chapters',
        'sections',
        'embeddings',
        'reading_progress',
        'bookmarks',
        'highlights',
        'tenant_integrations',
        'integration_logs',
        'usage_tracking',
    ]

    # Add FK constraint to each table
    for table_name in tenant_scoped_tables:
        try:
            op.create_foreign_key(
                f'fk_{table_name}_tenant_id',
                table_name,
                'tenants',
                ['tenant_id'],
                ['id'],
                ondelete='CASCADE'
            )
        except Exception:
            # Skip if FK already exists or table doesn't exist
            pass


def downgrade() -> None:
    """Remove FK constraints from tenant_id columns."""

    tenant_scoped_tables = [
        'patients',
        'patient_tags',
        'patient_diagnoses',
        'appointments',
        'visits',
        'prescriptions',
        'prescription_items',
        'payments',
        'invoices',
        'medicines',
        'medicine_aliases',
        'symptoms',
        'symptom_aliases',
        'medicine_symptom_mappings',
        'books',
        'chapters',
        'sections',
        'embeddings',
        'reading_progress',
        'bookmarks',
        'highlights',
        'tenant_integrations',
        'integration_logs',
        'usage_tracking',
    ]

    for table_name in tenant_scoped_tables:
        try:
            op.drop_constraint(f'fk_{table_name}_tenant_id', table_name, type_='foreignkey')
        except Exception:
            # Skip if FK doesn't exist
            pass
