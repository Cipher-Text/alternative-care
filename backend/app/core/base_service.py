"""Base service class for tenant-scoped business logic."""

from typing import Any, Generic, Type, TypeVar
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# Generic type for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)
# Generic type for Pydantic schemas
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseTenantService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class with tenant context and common CRUD operations.

    Provides reusable methods for:
    - Tenant-scoped queries
    - Get with 404 handling
    - Pagination
    - Soft delete patterns
    - Common filters

    Usage:
        class PatientService(BaseTenantService[Patient, PatientCreate, PatientUpdate]):
            model = Patient

            def __init__(self, db: AsyncSession, tenant_id: str):
                super().__init__(db, tenant_id)
                # Add custom initialization if needed
    """

    # Subclasses must set this
    model: Type[ModelType] = None

    def __init__(self, db: AsyncSession, tenant_id: str):
        """
        Initialize service with database session and tenant context.

        Args:
            db: SQLAlchemy async session
            tenant_id: Tenant ID used for application-level row isolation
        """
        self.db = db
        self.tenant_id = tenant_id

    def _get_base_query(self):
        """
        Get base query with tenant filter.

        Returns:
            SQLAlchemy select query filtered by tenant_id
        """
        return select(self.model).where(self.model.tenant_id == self.tenant_id)

    async def get_by_id(
        self,
        id: str | int,
        raise_404: bool = True,
        extra_filters: dict[str, Any] | None = None
    ) -> ModelType | None:
        """
        Get entity by ID with tenant filtering.

        Args:
            id: Entity ID
            raise_404: Raise HTTPException if not found (default True)
            extra_filters: Additional filters as dict (e.g., {"is_active": True})

        Returns:
            Entity instance or None

        Raises:
            HTTPException: 404 if not found and raise_404=True
        """
        query = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.tenant_id == self.tenant_id,
            )
        )

        # Apply extra filters
        if extra_filters:
            for field, value in extra_filters.items():
                query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        entity = result.scalar_one_or_none()

        if not entity and raise_404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found",
            )

        return entity

    async def list_with_pagination(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        search_fields: list[str] | None = None,
        search_query: str | None = None,
        order_by: Any = None,
    ) -> list[ModelType]:
        """
        List entities with pagination and optional filters.

        Args:
            limit: Maximum results
            offset: Pagination offset
            filters: Field filters as dict (e.g., {"is_active": True})
            search_fields: Fields to search (e.g., ["full_name", "phone"])
            search_query: Search string (applied to search_fields with ILIKE)
            order_by: SQLAlchemy column for ordering (default: created_at desc)

        Returns:
            List of entities
        """
        query = self._get_base_query()

        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = query.where(getattr(self.model, field) == value)

        # Apply search
        if search_query and search_fields:
            search_pattern = f"%{search_query}%"
            search_conditions = [
                getattr(self.model, field).ilike(search_pattern)
                for field in search_fields
            ]
            query = query.where(or_(*search_conditions))

        # Apply ordering
        if order_by is not None:
            query = query.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities with optional filters.

        Args:
            filters: Field filters as dict (e.g., {"is_active": True})

        Returns:
            Total count
        """
        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == self.tenant_id
        )

        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(
        self,
        data: CreateSchemaType,
        created_by: str,
        **extra_fields
    ) -> ModelType:
        """
        Create a new entity.

        Args:
            data: Pydantic schema with creation data
            created_by: User ID creating the entity
            **extra_fields: Additional fields to set (e.g., id=uuid4())

        Returns:
            Created entity
        """
        # Generate ID if model uses UUID and not provided
        if "id" not in extra_fields and hasattr(self.model, "id"):
            # Check if id column is String type (UUID)
            id_column = getattr(self.model, "id")
            if hasattr(id_column.type, "python_type"):
                if id_column.type.python_type == str:
                    extra_fields["id"] = str(uuid4())

        entity = self.model(
            **data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=created_by,
            updated_by=created_by,
            **extra_fields
        )

        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)

        return entity

    async def update(
        self,
        id: str | int,
        data: UpdateSchemaType,
        updated_by: str,
    ) -> ModelType:
        """
        Update an entity with partial data.

        Args:
            id: Entity ID
            data: Pydantic schema with update data (partial)
            updated_by: User ID performing the update

        Returns:
            Updated entity
        """
        entity = await self.get_by_id(id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entity, field, value)

        # Update audit fields
        if hasattr(entity, "updated_by"):
            entity.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(entity)

        return entity

    async def soft_delete(
        self,
        id: str | int,
        updated_by: str,
    ) -> ModelType:
        """
        Soft delete an entity (set is_active=False).

        Args:
            id: Entity ID
            updated_by: User ID performing the delete

        Returns:
            Updated entity (is_active=False)
        """
        entity = await self.get_by_id(id)

        if hasattr(entity, "is_active"):
            entity.is_active = False

        if hasattr(entity, "updated_by"):
            entity.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(entity)

        return entity

    async def hard_delete(self, id: str | int) -> None:
        """
        Hard delete an entity (permanent deletion).

        WARNING: Use with caution. Prefer soft_delete for clinical data.

        Args:
            id: Entity ID
        """
        entity = await self.get_by_id(id)
        await self.db.delete(entity)
        await self.db.commit()


class GlobalCatalogService(Generic[ModelType]):
    """
    Base service class for hybrid global-or-tenant catalog tables
    (GlobalCatalogModel subclasses with their own nullable tenant_id +
    is_global column, e.g. Medicine, Symptom).

    Unlike BaseTenantService, tenant_id may be None here — a platform
    admin managing the global catalog has no tenant of their own.

    Usage:
        class MedicineService(GlobalCatalogService[Medicine]):
            model = Medicine
    """

    # Subclasses must set this
    model: Type[ModelType] = None

    def __init__(self, db: AsyncSession, tenant_id: str | None):
        """
        Args:
            db: SQLAlchemy async session
            tenant_id: Caller's tenant, or None for a platform admin
        """
        self.db = db
        self.tenant_id = tenant_id

    def _visible_query(self):
        """
        Base query for rows visible to the caller: global rows, or rows
        owned by their tenant.

        For a platform admin (tenant_id=None), this narrows to global-only
        rows without any special-casing — SQLAlchemy compiles
        `Model.tenant_id == None` to `IS NULL`, and every model this base
        supports has a CHECK constraint guaranteeing only global rows have
        a null tenant_id.
        """
        return select(self.model).where(
            or_(self.model.is_global == True, self.model.tenant_id == self.tenant_id)  # noqa: E712
        )

    async def get_visible_or_404(
        self, id: str | int, *, detail: str | None = None
    ) -> ModelType:
        """Get a visible (global or own-tenant) row by ID, or raise 404."""
        result = await self.db.execute(self._visible_query().where(self.model.id == id))
        entity = result.scalar_one_or_none()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail or f"{self.model.__name__} not found",
            )

        return entity

    async def get_own_or_404(
        self, id: str | int, *, detail: str | None = None
    ) -> ModelType:
        """
        Get a tenant-owned, non-global row by ID, or raise 404.

        For update/delete — a caller (including an admin) can only modify
        rows their own tenant owns, never a global row, through this path.
        """
        result = await self.db.execute(
            select(self.model).where(
                and_(
                    self.model.id == id,
                    self.model.tenant_id == self.tenant_id,
                    self.model.is_global == False,  # noqa: E712
                )
            )
        )
        entity = result.scalar_one_or_none()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail or f"{self.model.__name__} not found or cannot be modified",
            )

        return entity
