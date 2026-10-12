"""add the Enterprise plan and seed plan prices/descriptions

Revision ID: d2a8e4b6f1c7
Revises: c5f2a7d9e1b3
Create Date: 2026-10-12 21:00:00

Prices are filled in ONLY where none is set (an admin's saved price is never overwritten), and
descriptions are replaced ONLY where they still equal the earlier built-in text. Entitlement values
are not stored: plans without stored rows use the code defaults in app/core/entitlements.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2a8e4b6f1c7"
down_revision: Union[str, None] = "c5f2a7d9e1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# key -> (monthly, yearly)  BDT
PRICES = {"free": (0, 0), "plus": (1000, 10000), "pro": (3000, 30000)}

# key -> (old en, old bn, new en, new bn)
DESCRIPTIONS = {
    "free": (
        "For solo practitioners getting started", "শুরু করা একক চিকিৎসকদের জন্য",
        "Try AltCare in your own chamber", "নিজের চেম্বারে AltCare ব্যবহার করে দেখুন",
    ),
    "plus": (
        "For growing clinics", "বর্ধনশীল ক্লিনিকের জন্য",
        "For a working chamber or small clinic", "চালু চেম্বার বা ছোট ক্লিনিকের জন্য",
    ),
    "pro": (
        "For established practices", "প্রতিষ্ঠিত প্র্যাকটিসের জন্য",
        "For established clinics with several doctors", "একাধিক চিকিৎসকের প্রতিষ্ঠিত ক্লিনিকের জন্য",
    ),
}


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO plans (key, name_en, name_bn, description_en, description_bn, price_monthly, "
            "price_yearly, currency, is_public, sort_order) "
            "SELECT 'enterprise', 'Enterprise', 'এন্টারপ্রাইজ', "
            "'For hospitals, chains and institutions: custom plan and pricing', "
            "'হাসপাতাল, চেইন ও প্রতিষ্ঠানের জন্য: কাস্টম প্ল্যান ও মূল্য', NULL, NULL, 'BDT', true, 4 "
            "WHERE NOT EXISTS (SELECT 1 FROM plans WHERE key = 'enterprise')"
        )
    )
    for key, (monthly, yearly) in PRICES.items():
        conn.execute(
            sa.text(
                "UPDATE plans SET price_monthly = :m, price_yearly = :y "
                "WHERE key = :k AND price_monthly IS NULL AND price_yearly IS NULL"
            ),
            {"m": monthly, "y": yearly, "k": key},
        )
    for key, (old_en, old_bn, new_en, new_bn) in DESCRIPTIONS.items():
        conn.execute(
            sa.text(
                "UPDATE plans SET description_en = :ne, description_bn = :nb "
                "WHERE key = :k AND description_en = :oe AND description_bn = :ob"
            ),
            {"k": key, "oe": old_en, "ob": old_bn, "ne": new_en, "nb": new_bn},
        )


def downgrade() -> None:
    # Moves any tenant on Enterprise to Pro so no row points at a deleted plan, then removes the plan.
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE tenants SET plan = 'pro' WHERE plan = 'enterprise'"))
    conn.execute(sa.text("DELETE FROM plan_entitlements WHERE plan_key = 'enterprise'"))
    conn.execute(sa.text("DELETE FROM plans WHERE key = 'enterprise'"))
