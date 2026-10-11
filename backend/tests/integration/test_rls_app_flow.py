"""RLS under the application's real session behaviour: commit mid-request, then keep reading.

The tenant GUC is transaction-local, so before `bind_tenant()` a `commit()` followed by
`refresh()` (what `BaseService.create` does) lost the tenant and RLS hid the just-inserted row
("Could not refresh instance" -> HTTP 500). These tests use a session whose connections run as a
non-superuser role, i.e. with RLS genuinely enforced, and exercise commit boundaries directly.
"""

from uuid import uuid4

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import bind_tenant
from app.shared.models import Patient
from tests.integration.test_rls_policies import (  # noqa: F401  (fixtures)
    rls_enabled,
    rls_probe_role,
    tenant_a,
    tenant_b,
)


@pytest.fixture
async def rls_sessionmaker(test_engine, rls_enabled, rls_probe_role, tenant_a, tenant_b):
    engine = create_async_engine(test_engine.url, poolclass=None)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_role(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute(f"SET ROLE {rls_probe_role}")
        cur.close()

    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _patient(tenant_id: str, name: str) -> Patient:
    return Patient(id=str(uuid4()), tenant_id=tenant_id, full_name=name, is_active=True)


@pytest.mark.asyncio
async def test_create_commit_refresh_survives_rls(rls_sessionmaker, tenant_a):
    async with rls_sessionmaker() as db:
        await bind_tenant(db, tenant_a.id)
        patient = _patient(tenant_a.id, "Refresh Me")
        db.add(patient)
        await db.commit()
        await db.refresh(patient)  # raised InvalidRequestError before the fix
        assert patient.full_name == "Refresh Me"


@pytest.mark.asyncio
async def test_tenant_persists_across_several_commits(rls_sessionmaker, tenant_a):
    async with rls_sessionmaker() as db:
        await bind_tenant(db, tenant_a.id)
        for i in range(3):
            db.add(_patient(tenant_a.id, f"P{i}"))
            await db.commit()
        rows = (await db.execute(select(Patient))).scalars().all()
        assert len(rows) == 3


@pytest.mark.asyncio
async def test_other_tenant_rows_stay_hidden_and_unwritable(rls_sessionmaker, tenant_a, tenant_b):
    async with rls_sessionmaker() as db:
        await bind_tenant(db, tenant_b.id)
        db.add(_patient(tenant_b.id, "B's patient"))
        await db.commit()

    async with rls_sessionmaker() as db:
        await bind_tenant(db, tenant_a.id)
        assert (await db.execute(select(Patient))).scalars().all() == []
        db.add(_patient(tenant_b.id, "Forged"))
        with pytest.raises(Exception):
            await db.commit()


@pytest.mark.asyncio
async def test_tenantless_caller_clears_stale_binding(rls_sessionmaker, tenant_a):
    async with rls_sessionmaker() as db:
        await bind_tenant(db, tenant_a.id)
        db.add(_patient(tenant_a.id, "Visible to A"))
        await db.commit()
        # same session re-used by a platform user (no tenant)
        await bind_tenant(db, None)
        await db.rollback()
        assert db.info.get("tenant_id") is None
        assert (await db.execute(select(Patient))).scalars().all() == []
