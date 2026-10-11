"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# ---------------------------------------------------------------------------------------------
# Row-level security: the tenant GUC
# ---------------------------------------------------------------------------------------------
# RLS policies on the clinical tables compare `tenant_id` with the GUC `app.tenant_id`
# (migration 273747e56a3f). The GUC is set with `set_config(..., is_local => true)`, so it lives
# only as long as the *transaction* — which is what stops it leaking to the next request when a
# pooled connection is reused.
#
# But a request is not one transaction: services call `db.commit()` partway through (e.g. insert,
# commit, refresh). Every commit ends the transaction and the next query silently begins a new one
# with the GUC gone, so RLS then hides the caller's own rows (refresh() after an INSERT raised
# "Could not refresh instance" -> HTTP 500). That stayed invisible while the app ran as a
# PostgreSQL superuser, which bypasses RLS; it broke the moment the app ran as a normal role.
#
# So the tenant is remembered on the session (`session.info`) and re-applied at the start of
# every transaction the session opens.
TENANT_INFO_KEY = "tenant_id"
_SET_TENANT_SQL = text("SELECT set_config('app.tenant_id', :tenant_id, true)")


@event.listens_for(Session, "after_begin")
def _apply_tenant_guc(session, transaction, connection) -> None:
    """Re-apply the tenant GUC at the start of every transaction of a tenant-bound session."""
    tenant_id = session.info.get(TENANT_INFO_KEY)
    if tenant_id:
        connection.execute(_SET_TENANT_SQL, {"tenant_id": tenant_id})


async def bind_tenant(db: AsyncSession, tenant_id: str | None) -> None:
    """
    Bind this session to a tenant for row-level security.

    Sets the GUC for the transaction that is already open and arranges for every later
    transaction on the session to get it too (see above). With no tenant (platform staff) the
    binding is cleared, so a reused session can never carry the previous caller's tenant: RLS then
    sees "no tenant" and returns no clinical rows, a safe default.
    """
    if tenant_id:
        db.info[TENANT_INFO_KEY] = tenant_id
        await db.execute(_SET_TENANT_SQL, {"tenant_id": tenant_id})
    else:
        db.info.pop(TENANT_INFO_KEY, None)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.

    Usage:
        async with get_db_context() as db:
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
