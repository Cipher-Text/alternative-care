"""Base models for all database entities."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BaseAuditModel(Base):
    """
    Abstract base model with common audit fields.

    All models should inherit from this to get:
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update
    - created_by: User ID who created the record
    - updated_by: User ID who last updated the record
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class TenantScopedModel(BaseAuditModel):
    """
    Abstract base model for tenant-scoped entities.

    Adds a required tenant_id field for application-level row isolation.
    SQLAlchemy does not automatically filter queries; services and routes
    must include the appropriate tenant predicate explicitly.
    """

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class GlobalCatalogModel(BaseAuditModel):
    """
    Abstract base for catalog entities that may be admin-curated (global,
    shared across all tenants) or tenant-owned, never both states at once.

    Unlike TenantScopedModel, this base does not declare tenant_id itself —
    subclasses that are hybrid global-or-tenant tables (e.g. Medicine,
    Symptom) add their own nullable tenant_id column plus a CHECK constraint
    making "(is_global AND tenant_id IS NULL) OR (NOT is_global AND
    tenant_id IS NOT NULL)" the only representable state. A purely global
    catalog table (no tenant ownership at all) would add no tenant_id
    column here.
    """

    __abstract__ = True
