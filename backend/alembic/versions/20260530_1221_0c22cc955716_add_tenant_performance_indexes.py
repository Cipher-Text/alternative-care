"""add_tenant_performance_indexes

Revision ID: 0c22cc955716
Revises: 2d3300438130
Create Date: 2026-05-30 12:21:43.422790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c22cc955716'
down_revision: Union[str, None] = '2d3300438130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add composite indexes for tenant-scoped queries.

    PERFORMANCE: These indexes dramatically improve query performance for:
    - Listing resources by tenant (tenant_id + created_at)
    - Filtering active resources (tenant_id + is_active)
    - Patient-related queries (tenant_id + patient_id)
    - Appointment scheduling (tenant_id + appointment_date)
    """

    # Patients table indexes
    op.create_index(
        'idx_patients_tenant_created',
        'patients',
        ['tenant_id', 'created_at'],
        unique=False
    )

    # Appointments table indexes
    op.create_index(
        'idx_appointments_tenant_date',
        'appointments',
        ['tenant_id', 'appointment_date'],
        unique=False
    )
    op.create_index(
        'idx_appointments_tenant_patient',
        'appointments',
        ['tenant_id', 'patient_id'],
        unique=False
    )

    # Prescriptions table indexes
    op.create_index(
        'idx_prescriptions_tenant_patient',
        'prescriptions',
        ['tenant_id', 'patient_id'],
        unique=False
    )
    op.create_index(
        'idx_prescriptions_tenant_created',
        'prescriptions',
        ['tenant_id', 'created_at'],
        unique=False
    )
    op.create_index(
        'idx_prescriptions_tenant_status',
        'prescriptions',
        ['tenant_id', 'status'],
        unique=False
    )

    # Payments table indexes
    op.create_index(
        'idx_payments_tenant_created',
        'payments',
        ['tenant_id', 'created_at'],
        unique=False
    )
    op.create_index(
        'idx_payments_tenant_status',
        'payments',
        ['tenant_id', 'status'],
        unique=False
    )

    # Medicines table indexes (global + tenant-specific)
    op.create_index(
        'idx_medicines_tenant_active',
        'medicines',
        ['tenant_id', 'is_active'],
        unique=False
    )
    op.create_index(
        'idx_medicines_global_system',
        'medicines',
        ['is_global', 'system'],
        unique=False,
        postgresql_where=sa.text('is_global = true')
    )

    # Symptoms table indexes (global + tenant-specific)
    op.create_index(
        'idx_symptoms_tenant_active',
        'symptoms',
        ['tenant_id', 'is_active'],
        unique=False
    )

    # User sessions table (for token validation performance)
    op.create_index(
        'idx_sessions_user_active',
        'user_sessions',
        ['user_id', 'is_revoked', 'expires_at'],
        unique=False,
        postgresql_where=sa.text('is_revoked = false')
    )


def downgrade() -> None:
    """Remove composite indexes."""
    # User sessions
    op.drop_index('idx_sessions_user_active', table_name='user_sessions')

    # Symptoms
    op.drop_index('idx_symptoms_tenant_active', table_name='symptoms')

    # Medicines
    op.drop_index('idx_medicines_global_system', table_name='medicines')
    op.drop_index('idx_medicines_tenant_active', table_name='medicines')

    # Payments
    op.drop_index('idx_payments_tenant_status', table_name='payments')
    op.drop_index('idx_payments_tenant_created', table_name='payments')

    # Prescriptions
    op.drop_index('idx_prescriptions_tenant_status', table_name='prescriptions')
    op.drop_index('idx_prescriptions_tenant_created', table_name='prescriptions')
    op.drop_index('idx_prescriptions_tenant_patient', table_name='prescriptions')

    # Appointments
    op.drop_index('idx_appointments_tenant_patient', table_name='appointments')
    op.drop_index('idx_appointments_tenant_date', table_name='appointments')

    # Patients
    op.drop_index('idx_patients_tenant_created', table_name='patients')
