"""Initial database schema with all base tables

Revision ID: 000_initial_schema
Revises:
Create Date: 2026-04-23

This migration creates all base tables needed for the application.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all base tables."""

    # 1. Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('clinic_name', sa.String(255), nullable=True),
        sa.Column('clinic_address', sa.Text(), nullable=True),
        sa.Column('division_id', sa.Integer(), nullable=True),
        sa.Column('district_id', sa.Integer(), nullable=True),
        sa.Column('upazila_id', sa.Integer(), nullable=True),
        sa.Column('specializations', postgresql.ARRAY(sa.String(50)), nullable=False, server_default='{}'),
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='free'),
        sa.Column('plan_started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('plan_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )

    # 2. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, index=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('totp_secret', sa.String(32), nullable=True),
        sa.Column('language', sa.String(5), nullable=False, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )

    # 3. Patients table
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('full_name', sa.String(255), nullable=False, index=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('blood_group', sa.String(10), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('whatsapp', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('division_id', sa.Integer(), nullable=True),
        sa.Column('district_id', sa.Integer(), nullable=True),
        sa.Column('upazila_id', sa.Integer(), nullable=True),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('medical_history', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('next_visit_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )

    # 4. Medicines table
    op.create_table(
        'medicines',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name_en', sa.String(500), nullable=False),
        sa.Column('name_bn', sa.String(500), nullable=True),
        sa.Column('system', sa.String(50), nullable=False, index=True),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_bn', sa.Text(), nullable=True),
        sa.Column('potency', sa.String(50), nullable=True),
        sa.Column('dosage_guidance_en', sa.Text(), nullable=True),
        sa.Column('dosage_guidance_bn', sa.Text(), nullable=True),
        sa.Column('indications_en', sa.Text(), nullable=True),
        sa.Column('indications_bn', sa.Text(), nullable=True),
        sa.Column('contraindications_en', sa.Text(), nullable=True),
        sa.Column('contraindications_bn', sa.Text(), nullable=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )

    # Create GIN index for medicines name search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.create_index(
        'ix_medicines_name_en_trgm',
        'medicines',
        ['name_en'],
        postgresql_using='gin',
        postgresql_ops={'name_en': 'gin_trgm_ops'}
    )


def downgrade() -> None:
    """Drop all base tables."""
    op.drop_index('ix_medicines_name_en_trgm', table_name='medicines')
    op.drop_table('medicines')
    op.drop_table('patients')
    op.drop_table('users')
    op.drop_table('tenants')
