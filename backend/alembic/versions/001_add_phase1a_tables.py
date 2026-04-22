"""Add appointments, visits, symptoms, and alias tables for Phase 1A

Revision ID: 001_phase1a_tables
Revises:
Create Date: 2026-04-23

This migration:
- DROPS old medicine_symptoms table (no backward compatibility)
- Adds Appointments and Visits tables (Phase 1A requirement)
- Adds Normalized Symptoms table
- Adds Symptom aliases for Bangladesh context search
- Adds Medicine aliases for search
- Adds Medicine-Symptom mapping with FK to normalized symptoms
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_phase1a_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create new tables for Phase 1A."""

    # 0. Drop old medicine_symptoms table (replaced by normalized structure)
    op.execute('DROP TABLE IF EXISTS medicine_symptoms CASCADE')

    # 1. Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('doctor_id', sa.String(36), nullable=False, index=True),
        sa.Column('appointment_date', sa.Date(), nullable=False, index=True),
        sa.Column('appointment_time', sa.Time(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled', index=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.Date(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id']),
    )

    # 2. Create visits table
    op.create_table(
        'visits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('doctor_id', sa.String(36), nullable=False, index=True),
        sa.Column('appointment_id', sa.String(36), nullable=True, index=True),
        sa.Column('visit_date', sa.Date(), nullable=False, index=True),
        sa.Column('visit_type', sa.String(50), nullable=False, server_default='consultation'),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('history_of_present_illness', sa.Text(), nullable=True),
        sa.Column('examination_notes', sa.Text(), nullable=True),
        sa.Column('temperature', sa.String(10), nullable=True),
        sa.Column('blood_pressure', sa.String(20), nullable=True),
        sa.Column('pulse_rate', sa.String(10), nullable=True),
        sa.Column('weight', sa.String(10), nullable=True),
        sa.Column('provisional_diagnosis', sa.Text(), nullable=True),
        sa.Column('treatment_plan', sa.Text(), nullable=True),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='in_progress'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
    )

    # 3. Create normalized symptoms table
    op.create_table(
        'symptoms',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name_en', sa.String(500), nullable=False, index=True),
        sa.Column('name_bn', sa.String(500), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_bn', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )

    # Create GIN indexes for symptom trigram search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.create_index(
        'ix_symptoms_name_en_trgm',
        'symptoms',
        ['name_en'],
        postgresql_using='gin',
        postgresql_ops={'name_en': 'gin_trgm_ops'}
    )
    op.create_index(
        'ix_symptoms_name_bn_trgm',
        'symptoms',
        ['name_bn'],
        postgresql_using='gin',
        postgresql_ops={'name_bn': 'gin_trgm_ops'}
    )

    # 4. Create symptom aliases table (CRITICAL for Bangladesh search)
    op.create_table(
        'symptom_aliases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('symptom_id', sa.Integer(), nullable=False, index=True),
        sa.Column('alias_en', sa.String(500), nullable=True),
        sa.Column('alias_bn', sa.String(500), nullable=True),
        sa.Column('alias_type', sa.String(50), nullable=False, server_default='common_name'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['symptom_id'], ['symptoms.id'], ondelete='CASCADE'),
    )

    # Create GIN indexes for alias search
    op.create_index(
        'ix_symptom_aliases_alias_en_trgm',
        'symptom_aliases',
        ['alias_en'],
        postgresql_using='gin',
        postgresql_ops={'alias_en': 'gin_trgm_ops'}
    )
    op.create_index(
        'ix_symptom_aliases_alias_bn_trgm',
        'symptom_aliases',
        ['alias_bn'],
        postgresql_using='gin',
        postgresql_ops={'alias_bn': 'gin_trgm_ops'}
    )

    # 5. Create medicine aliases table (CRITICAL for Bangladesh search)
    op.create_table(
        'medicine_aliases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('medicine_id', sa.Integer(), nullable=False, index=True),
        sa.Column('alias_en', sa.String(500), nullable=True),
        sa.Column('alias_bn', sa.String(500), nullable=True),
        sa.Column('alias_type', sa.String(50), nullable=False, server_default='common_name'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='CASCADE'),
    )

    # Create GIN indexes for medicine alias search
    op.create_index(
        'ix_medicine_aliases_alias_en_trgm',
        'medicine_aliases',
        ['alias_en'],
        postgresql_using='gin',
        postgresql_ops={'alias_en': 'gin_trgm_ops'}
    )
    op.create_index(
        'ix_medicine_aliases_alias_bn_trgm',
        'medicine_aliases',
        ['alias_bn'],
        postgresql_using='gin',
        postgresql_ops={'alias_bn': 'gin_trgm_ops'}
    )

    # 6. Create medicine-symptom mapping with normalized symptom FK
    op.create_table(
        'medicine_symptom_mappings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('medicine_id', sa.Integer(), nullable=False, index=True),
        sa.Column('symptom_id', sa.Integer(), nullable=False, index=True),
        sa.Column('modality_en', sa.Text(), nullable=True),
        sa.Column('modality_bn', sa.Text(), nullable=True),
        sa.Column('strength', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['symptom_id'], ['symptoms.id'], ondelete='CASCADE'),
    )

    # Create unique index for medicine-symptom pairs
    op.create_index(
        'ix_medicine_symptom_unique',
        'medicine_symptom_mappings',
        ['medicine_id', 'symptom_id'],
        unique=True
    )

    # 7. Add GIN index to medicines.name_bn for better bilingual search
    op.create_index(
        'ix_medicines_name_bn_trgm',
        'medicines',
        ['name_bn'],
        postgresql_using='gin',
        postgresql_ops={'name_bn': 'gin_trgm_ops'}
    )


def downgrade() -> None:
    """Remove all tables created in this migration."""

    # Drop in reverse order to handle foreign key constraints
    op.drop_index('ix_medicine_symptom_unique', table_name='medicine_symptom_mappings')
    op.drop_table('medicine_symptom_mappings')

    op.drop_index('ix_medicine_aliases_alias_bn_trgm', table_name='medicine_aliases')
    op.drop_index('ix_medicine_aliases_alias_en_trgm', table_name='medicine_aliases')
    op.drop_table('medicine_aliases')

    op.drop_index('ix_symptom_aliases_alias_bn_trgm', table_name='symptom_aliases')
    op.drop_index('ix_symptom_aliases_alias_en_trgm', table_name='symptom_aliases')
    op.drop_table('symptom_aliases')

    op.drop_index('ix_symptoms_name_bn_trgm', table_name='symptoms')
    op.drop_index('ix_symptoms_name_en_trgm', table_name='symptoms')
    op.drop_table('symptoms')

    op.drop_table('visits')
    op.drop_table('appointments')

    op.drop_index('ix_medicines_name_bn_trgm', table_name='medicines')
