"""add pharmacies directory

Revision ID: d5a8c3f1e7b2
Revises: 4c91a7d2e6b0
Create Date: 2026-10-11 10:00:00

Admin-curated, always-global directory of pharmacies / wholesalers / depots where practitioners
buy stock. Same shape as `institutions`: no `tenant_id`. Latitude and longitude are nullable but
must be set together (CHECK), and are range-checked.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5a8c3f1e7b2"
down_revision: Union[str, None] = "4c91a7d2e6b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pharmacies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_en", sa.String(length=500), nullable=False),
        sa.Column("name_bn", sa.String(length=500), nullable=True),
        sa.Column("pharmacy_type", sa.String(length=20), nullable=False),
        sa.Column("disciplines", sa.ARRAY(sa.String(length=50)), nullable=False, server_default="{}"),
        sa.Column("notes_en", sa.Text(), nullable=True),
        sa.Column("notes_bn", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("district_id", sa.Integer(), nullable=True),
        sa.Column("upazila_id", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("whatsapp", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("opening_hours", sa.String(length=500), nullable=True),
        sa.Column("delivers", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=36), nullable=True),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["upazila_id"], ["upazilas.id"], ondelete="SET NULL"),
        sa.CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="ck_pharmacies_lat_lon_pair"),
        sa.CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="ck_pharmacies_lat_lon_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pharmacies_name_en", "pharmacies", ["name_en"])
    op.create_index("ix_pharmacies_district_id", "pharmacies", ["district_id"])
    op.create_index("ix_pharmacies_upazila_id", "pharmacies", ["upazila_id"])
    op.create_index("ix_pharmacies_lat_lon", "pharmacies", ["latitude", "longitude"])


def downgrade() -> None:
    op.drop_index("ix_pharmacies_lat_lon", table_name="pharmacies")
    op.drop_index("ix_pharmacies_upazila_id", table_name="pharmacies")
    op.drop_index("ix_pharmacies_district_id", table_name="pharmacies")
    op.drop_index("ix_pharmacies_name_en", table_name="pharmacies")
    op.drop_table("pharmacies")
