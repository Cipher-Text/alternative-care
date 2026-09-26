"""Add row-level security policies to the 8 clinical tables

Revision ID: 273747e56a3f
Revises: ed07cf4aebc7
Create Date: 2026-09-26 01:38:10.267176

Stage 2 (docs/planning/revision-2026-09.md, D2). A second layer, not a
replacement — application-level filtering (BaseTenantService) is
unchanged. The point is to convert the failure mode of a hand-written
query that forgets its tenant_id predicate from a silent cross-tenant
leak into either an empty result (SELECT) or a hard error (INSERT/UPDATE
of a row for a different tenant than the session's).

Each table gets the same policy: rows are visible/writable only when
`tenant_id` matches the per-request GUC `app.tenant_id`, set in
`app/core/dependencies.py:get_current_user()` via `set_config(...)`
(transaction-scoped, so it can't leak across pooled-connection reuse
between requests). `current_setting(..., true)` returns NULL rather than
raising when the GUC is unset (e.g. a platform admin, tenant_id=None,
simply never sets it) — NULL compared against tenant_id is never true,
so an admin session sees zero rows through these policies, which is a
safe default since no current admin code path reads these tables. No
`WITH CHECK` clause is given because Postgres reuses `USING` for the
check when none is specified, which is exactly the "reject a write for
another tenant" behavior wanted here.

FORCE ROW LEVEL SECURITY closes the loophole where the *table-owning*
role would otherwise bypass its own table's policies. It does **not**
close the *superuser* bypass — PostgreSQL superusers unconditionally
bypass RLS, full stop, with no flag to override it. Both the local dev
DB role and CI's bootstrapped POSTGRES_USER are superusers today (single
DATABASE_URL, no dedicated least-privileged application role exists
anywhere in this codebase's config/infra), so this migration is currently
inert in practice for both environments. It becomes fully protective the
moment a non-superuser application role is introduced and DATABASE_URL
points at it — a deployment/provisioning change, intentionally not done
here. Don't remove this paragraph when that follow-up lands; replace it
with what changed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '273747e56a3f'
down_revision: Union[str, None] = 'ed07cf4aebc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Every table here is a plain TenantScopedModel subclass: one NOT NULL
# tenant_id column, same FK target, no joins needed for the policy.
CLINICAL_TABLES = (
    "patients",
    "appointments",
    "visits",
    "prescriptions",
    "prescription_items",
    "payments",
    "invoices",
    "patient_diagnoses",
)

POLICY_NAME = "tenant_isolation"


def upgrade() -> None:
    for table in CLINICAL_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(
                f"CREATE POLICY {POLICY_NAME} ON {table} "
                "USING (tenant_id = current_setting('app.tenant_id', true))"
            )
        )


def downgrade() -> None:
    for table in CLINICAL_TABLES:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {POLICY_NAME} ON {table}"))
        op.execute(sa.text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
