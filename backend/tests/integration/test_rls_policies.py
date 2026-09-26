"""Integration tests for PostgreSQL row-level security on the clinical tables.

D2 (docs/planning/revision-2026-09.md). The migration (revision
273747e56a3f, backend/alembic/versions/20260926_0138_273747e56a3f_*.py) is
the source of truth for the table list and policy shape — duplicated here
(not imported: Alembic migrations must stay self-contained, never coupled
to application code that can change independently) because tests build
their schema via Base.metadata.create_all(), never `alembic upgrade head`
(see conftest.py's `test_engine` fixture), so the migration's CREATE
POLICY statements never exist in the test database on their own.

Both the local dev DB role and the CI Postgres container's bootstrapped
user are PostgreSQL superusers, which unconditionally bypass RLS no
matter what the policies say. So these tests don't observe RLS through
the normal `db_session`/`client` fixtures at all — they create a
throwaway, non-superuser role and `SET ROLE` into it for the duration of
one raw query. Postgres's RLS/ownership bypass checks are based on the
*current* effective role, which SET ROLE does change even though the
original login was as a superuser, so this genuinely proves the policies
work — it just proves it under the role the application isn't actually
running as yet (see the migration docstring for that gap).
"""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.shared.models import Tenant

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

PROBE_ROLE = "altcare_rls_probe"


@pytest.fixture
async def rls_enabled(test_engine):
    """Apply the same DDL as migration 273747e56a3f directly to the test schema."""
    async with test_engine.begin() as conn:
        for table in CLINICAL_TABLES:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            await conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
            await conn.execute(
                text(
                    f"CREATE POLICY tenant_isolation ON {table} "
                    "USING (tenant_id = current_setting('app.tenant_id', true))"
                )
            )
    yield


@pytest.fixture
async def rls_probe_role(test_engine):
    """A throwaway, non-superuser role to SET ROLE into for these tests."""
    async with test_engine.begin() as conn:
        exists = await conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": PROBE_ROLE}
        )
        if not exists.first():
            await conn.execute(text(f"CREATE ROLE {PROBE_ROLE} NOSUPERUSER NOBYPASSRLS"))
        await conn.execute(
            text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {PROBE_ROLE}")
        )
        await conn.execute(
            text(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {PROBE_ROLE}")
        )
    yield PROBE_ROLE


@pytest.fixture
async def tenant_a(db_session):
    tenant = Tenant(
        id=str(uuid4()),
        name="RLS Tenant A",
        email="rls-a@clinic.com",
        clinic_name="RLS Tenant A",
        specializations=["homeopathy"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_b(db_session):
    tenant = Tenant(
        id=str(uuid4()),
        name="RLS Tenant B",
        email="rls-b@clinic.com",
        clinic_name="RLS Tenant B",
        specializations=["homeopathy"],
        plan="free",
        is_active=True,
        is_approved=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.mark.asyncio
async def test_unscoped_select_does_not_leak_across_tenants(
    test_engine, rls_enabled, rls_probe_role, db_session, tenant_a, tenant_b
):
    """The exact bug D2 defends against: a raw query with no WHERE clause
    at all must not return another tenant's rows."""
    patient_a_id, patient_b_id = str(uuid4()), str(uuid4())
    await db_session.execute(
        text(
            "INSERT INTO patients (id, tenant_id, full_name, is_active) "
            "VALUES (:id, :tenant_id, :full_name, true)"
        ),
        {"id": patient_a_id, "tenant_id": tenant_a.id, "full_name": "Patient A"},
    )
    await db_session.execute(
        text(
            "INSERT INTO patients (id, tenant_id, full_name, is_active) "
            "VALUES (:id, :tenant_id, :full_name, true)"
        ),
        {"id": patient_b_id, "tenant_id": tenant_b.id, "full_name": "Patient B"},
    )
    await db_session.commit()

    async with test_engine.begin() as conn:
        await conn.execute(text(f"SET ROLE {rls_probe_role}"))
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a.id}
        )

        result = await conn.execute(text("SELECT id FROM patients"))
        visible_ids = {row[0] for row in result.fetchall()}

        await conn.execute(text("RESET ROLE"))

    assert visible_ids == {patient_a_id}


@pytest.mark.asyncio
async def test_cross_tenant_insert_is_rejected(
    test_engine, rls_enabled, rls_probe_role, tenant_a, tenant_b
):
    """The "hard error" half of the doc's language — a write for another
    tenant than the session's is rejected, not silently misfiled."""
    async with test_engine.connect() as conn:
        await conn.execute(text(f"SET ROLE {rls_probe_role}"))
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a.id}
        )

        with pytest.raises(Exception, match="row-level security"):
            await conn.execute(
                text(
                    "INSERT INTO patients (id, tenant_id, full_name, is_active) "
                    "VALUES (:id, :tenant_id, :full_name, true)"
                ),
                {"id": str(uuid4()), "tenant_id": tenant_b.id, "full_name": "Sneaky"},
            )

        await conn.rollback()
        await conn.execute(text("RESET ROLE"))


@pytest.mark.asyncio
async def test_unscoped_select_does_not_leak_on_a_second_table(
    test_engine, rls_enabled, rls_probe_role, db_session, tenant_a, tenant_b
):
    """Prove the policy pattern isn't patients-specific — one more table,
    not all 8 (the migration's loop already guarantees uniformity there)."""
    prescription_a_id, prescription_b_id = str(uuid4()), str(uuid4())
    await db_session.execute(
        text(
            "INSERT INTO prescriptions (id, tenant_id, patient_id, prescribed_by, status) "
            "VALUES (:id, :tenant_id, :patient_id, :prescribed_by, 'draft')"
        ),
        {
            "id": prescription_a_id,
            "tenant_id": tenant_a.id,
            "patient_id": str(uuid4()),
            "prescribed_by": str(uuid4()),
        },
    )
    await db_session.execute(
        text(
            "INSERT INTO prescriptions (id, tenant_id, patient_id, prescribed_by, status) "
            "VALUES (:id, :tenant_id, :patient_id, :prescribed_by, 'draft')"
        ),
        {
            "id": prescription_b_id,
            "tenant_id": tenant_b.id,
            "patient_id": str(uuid4()),
            "prescribed_by": str(uuid4()),
        },
    )
    await db_session.commit()

    async with test_engine.begin() as conn:
        await conn.execute(text(f"SET ROLE {rls_probe_role}"))
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b.id}
        )

        result = await conn.execute(text("SELECT id FROM prescriptions"))
        visible_ids = {row[0] for row in result.fetchall()}

        await conn.execute(text("RESET ROLE"))

    assert visible_ids == {prescription_b_id}
