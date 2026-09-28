"""add catalog fulltext search

Revision ID: d36407b8b27e
Revises: 273747e56a3f
Create Date: 2026-09-28 13:36:51.403374

Stage 2 (docs/planning/revision-2026-09.md, D5). Adds one `search_vector`
tsvector column, generated and stored, to both `medicines` and `symptoms` —
the same pattern on both tables is the "unified" part: one search
implementation shared across the catalog instead of separately hand-rolled
ILIKE per module (`GlobalCatalogService._fulltext_search`,
`app/core/base_service.py`).

'simple' text-search config, not 'english': Postgres ships no Bengali
config, and 'simple' (tokenize, no stemming) is the one behavior that's
correct for both name_en and name_bn in a single column, rather than
mis-stemming Bengali text through an English-tuned config.

GENERATED ALWAYS ... STORED keeps the column in sync with name_en/name_bn
with no application-level write path — there's nothing to forget to
update, the same reasoning as D1's CHECK constraint one column over.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd36407b8b27e'
down_revision: Union[str, None] = '273747e56a3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATALOG_TABLES = ("medicines", "symptoms")

SEARCH_VECTOR_EXPR = (
    "to_tsvector('simple', coalesce(name_en, '') || ' ' || coalesce(name_bn, ''))"
)


def upgrade() -> None:
    for table in CATALOG_TABLES:
        op.execute(
            sa.text(
                f"ALTER TABLE {table} ADD COLUMN search_vector tsvector "
                f"GENERATED ALWAYS AS ({SEARCH_VECTOR_EXPR}) STORED"
            )
        )
        op.execute(
            sa.text(
                f"CREATE INDEX ix_{table}_search_vector ON {table} "
                "USING gin (search_vector)"
            )
        )


def downgrade() -> None:
    for table in CATALOG_TABLES:
        op.execute(sa.text(f"DROP INDEX IF EXISTS ix_{table}_search_vector"))
        op.execute(sa.text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS search_vector"))
