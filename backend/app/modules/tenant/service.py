"""Tenant/Clinic service with business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.shared.models.tenant import Tenant
from app.shared.schemas import TenantProfileUpdate


class TenantService:
    """Service for managing tenant/clinic profiles."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    async def get_tenant_profile(self) -> Tenant:
        """
        Get complete tenant profile.

        Returns:
            Tenant: Complete clinic profile

        Raises:
            HTTPException: 404 if clinic not found
        """
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic profile not found"
            )

        return tenant

    async def update_tenant_profile(
        self,
        data: TenantProfileUpdate,
        updated_by: str
    ) -> Tenant:
        """
        Update tenant profile information.

        Args:
            data: Profile update data (partial)
            updated_by: User ID performing the update

        Returns:
            Tenant: Updated clinic profile

        Raises:
            HTTPException: 404 if clinic not found
        """
        tenant = await self.get_tenant_profile()

        # Update fields (only fields provided in request)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        tenant.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(tenant)

        return tenant
