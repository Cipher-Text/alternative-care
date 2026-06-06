"""add_phase1_essential_clinic_fields

Revision ID: ea15c99f558c
Revises: 0c22cc955716
Create Date: 2026-06-06 23:01:16.009605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea15c99f558c'
down_revision: Union[str, None] = '0c22cc955716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 1 essential clinic fields to tenants table."""

    # Clinic contact details (separate from owner)
    op.add_column('tenants', sa.Column('clinic_phone', sa.String(20), nullable=True))
    op.add_column('tenants', sa.Column('clinic_email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('clinic_whatsapp', sa.String(20), nullable=True))

    # Structured address
    op.add_column('tenants', sa.Column('address_line_1', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('address_line_2', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('postal_code', sa.String(10), nullable=True))
    op.add_column('tenants', sa.Column('landmark', sa.String(255), nullable=True))

    # Geolocation for maps
    op.add_column('tenants', sa.Column('latitude', sa.Float, nullable=True))
    op.add_column('tenants', sa.Column('longitude', sa.Float, nullable=True))

    # Branding
    op.add_column('tenants', sa.Column('logo_url', sa.String(500), nullable=True))
    op.add_column('tenants', sa.Column('description_en', sa.Text, nullable=True))
    op.add_column('tenants', sa.Column('description_bn', sa.Text, nullable=True))

    # Professional credentials
    op.add_column('tenants', sa.Column('registration_body', sa.String(100), nullable=True,
                                       comment='e.g., BMDC, Bangladesh Homeopathic Board'))
    op.add_column('tenants', sa.Column('registration_number', sa.String(100), nullable=True))
    op.add_column('tenants', sa.Column('years_of_experience', sa.Integer, nullable=True))

    # Fees (in paisa: 100 paisa = 1 BDT)
    op.add_column('tenants', sa.Column('consultation_fee', sa.Integer, nullable=True,
                                       comment='Fee in paisa (100 paisa = 1 BDT)'))
    op.add_column('tenants', sa.Column('follow_up_fee', sa.Integer, nullable=True,
                                       comment='Follow-up fee in paisa'))


def downgrade() -> None:
    """Remove Phase 1 essential clinic fields from tenants table."""

    # Drop all Phase 1 columns
    columns_to_drop = [
        'clinic_phone', 'clinic_email', 'clinic_whatsapp',
        'address_line_1', 'address_line_2', 'postal_code', 'landmark',
        'latitude', 'longitude',
        'logo_url', 'description_en', 'description_bn',
        'registration_body', 'registration_number', 'years_of_experience',
        'consultation_fee', 'follow_up_fee'
    ]

    for col in columns_to_drop:
        op.drop_column('tenants', col)
