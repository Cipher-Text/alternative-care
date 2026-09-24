"""nullable tenant_id for global catalog tables

Revision ID: ba209a25bf7d
Revises: 283e895eb3eb
Create Date: 2026-09-24 18:48:00.000000

Makes tenant_id nullable on the five hybrid global-or-tenant catalog tables
(medicines, symptoms, medicine_aliases, symptom_aliases,
medicine_symptom_mappings), so an admin can create a genuinely global
(tenant_id = NULL) row instead of the insert failing on the previous
NOT NULL constraint. A CHECK constraint on medicines/symptoms (the two
tables with their own is_global column) makes the invalid combination
unrepresentable: a row must be either global-with-no-tenant or
tenant-owned-with-a-tenant, never both or neither.

No backfill needed: every existing row already has a non-null tenant_id,
which already satisfies "NOT is_global AND tenant_id IS NOT NULL" for any
row where is_global is false, and no row can violate the constraint by
having is_global true with a non-null tenant_id without this migration
having run (that state was never reachable before now).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba209a25bf7d'
down_revision: Union[str, None] = '283e895eb3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('medicines', 'tenant_id', existing_type=sa.String(length=36), nullable=True)
    op.alter_column('symptoms', 'tenant_id', existing_type=sa.String(length=36), nullable=True)
    op.alter_column('medicine_aliases', 'tenant_id', existing_type=sa.String(length=36), nullable=True)
    op.alter_column('symptom_aliases', 'tenant_id', existing_type=sa.String(length=36), nullable=True)
    op.alter_column('medicine_symptom_mappings', 'tenant_id', existing_type=sa.String(length=36), nullable=True)

    op.create_check_constraint(
        'ck_medicines_tenant_global',
        'medicines',
        '(is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL)',
    )
    op.create_check_constraint(
        'ck_symptoms_tenant_global',
        'symptoms',
        '(is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL)',
    )


def downgrade() -> None:
    op.drop_constraint('ck_symptoms_tenant_global', 'symptoms', type_='check')
    op.drop_constraint('ck_medicines_tenant_global', 'medicines', type_='check')

    # Reverting to NOT NULL will fail here if any global (tenant_id IS NULL)
    # rows were created while this migration was active — that data loss
    # risk is intentional: downgrading past this point means deciding what
    # to do with those rows first (delete, or assign a tenant), not silently
    # coercing them.
    op.alter_column('medicine_symptom_mappings', 'tenant_id', existing_type=sa.String(length=36), nullable=False)
    op.alter_column('symptom_aliases', 'tenant_id', existing_type=sa.String(length=36), nullable=False)
    op.alter_column('medicine_aliases', 'tenant_id', existing_type=sa.String(length=36), nullable=False)
    op.alter_column('symptoms', 'tenant_id', existing_type=sa.String(length=36), nullable=False)
    op.alter_column('medicines', 'tenant_id', existing_type=sa.String(length=36), nullable=False)
