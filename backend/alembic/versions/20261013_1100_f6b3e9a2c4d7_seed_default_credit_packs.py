"""seed default SMS and email credit packs (only when no packs exist yet)

Revision ID: f6b3e9a2c4d7
Revises: e4c7a1d8b5f2
Create Date: 2026-10-13 11:00:00

Starting prices for top-up packs, in BDT. They sit above the cost floors in
docs/planning/billing-credits-spec-2026-10.md section 11 (SMS roughly 0.40 to 0.64 BDT each at the
provider, email a few paisa each) with a volume discount. They are hypotheses; an admin edits or
retires any of them in Admin > Billing. Nothing is inserted if an admin has already created packs.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6b3e9a2c4d7"
down_revision: Union[str, None] = "e4c7a1d8b5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# channel, quantity, price (BDT), English name, Bengali name, sort order
PACKS = [
    ("sms", 200, 250, "200 SMS pack", "200 এসএমএস প্যাক", 1),
    ("sms", 500, 550, "500 SMS pack", "500 এসএমএস প্যাক", 2),
    ("sms", 1000, 1000, "1,000 SMS pack", "1,000 এসএমএস প্যাক", 3),
    ("sms", 5000, 4500, "5,000 SMS pack", "5,000 এসএমএস প্যাক", 4),
    ("sms", 10000, 8000, "10,000 SMS pack", "10,000 এসএমএস প্যাক", 5),
    ("email", 1000, 150, "1,000 email pack", "1,000 ইমেইল প্যাক", 1),
    ("email", 5000, 600, "5,000 email pack", "5,000 ইমেইল প্যাক", 2),
    ("email", 20000, 2000, "20,000 email pack", "20,000 ইমেইল প্যাক", 3),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.execute(sa.text("SELECT count(*) FROM credit_packs")).scalar_one() > 0:
        return
    for channel, quantity, price, name_en, name_bn, order in PACKS:
        conn.execute(
            sa.text(
                "INSERT INTO credit_packs (channel, quantity, price, currency, name_en, name_bn, "
                "is_active, sort_order) VALUES (:c, :q, :p, 'BDT', :ne, :nb, true, :o)"
            ),
            {"c": channel, "q": quantity, "p": price, "ne": name_en, "nb": name_bn, "o": order},
        )


def downgrade() -> None:
    # Removes only the packs this migration seeded, by their exact channel and quantity.
    conn = op.get_bind()
    for channel, quantity, _price, name_en, _bn, _order in PACKS:
        conn.execute(
            sa.text("DELETE FROM credit_packs WHERE channel = :c AND quantity = :q AND name_en = :n"),
            {"c": channel, "q": quantity, "n": name_en},
        )
