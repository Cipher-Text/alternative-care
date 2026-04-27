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

    Adds tenant_id field for multi-tenant isolation.
    All queries should be automatically filtered by tenant_id.
    """

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
