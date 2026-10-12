"""Tenant/Clinic service with business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.images import process_logo
from app.core.storage import Storage, key_from_public_url
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

    async def set_logo(self, raw: bytes, storage: Storage, updated_by: str) -> Tenant:
        """Replace the clinic logo: validate and re-encode the image, store it, then drop the old file.

        The key contains the content hash, so a new logo is a new URL (no stale browser or CDN copy)."""
        data, digest = process_logo(raw)
        tenant = await self.get_tenant_profile()
        previous = key_from_public_url(tenant.logo_url)
        key = f"public/tenants/{self.tenant_id}/logo-{digest}.png"
        tenant.logo_url = await storage.put_public(key, data, "image/png")
        tenant.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(tenant)
        if previous and previous != key:
            await self._forget(storage, previous)
        return tenant

    async def remove_logo(self, storage: Storage, updated_by: str) -> Tenant:
        tenant = await self.get_tenant_profile()
        previous = key_from_public_url(tenant.logo_url)
        tenant.logo_url = None
        tenant.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(tenant)
        if previous:
            await self._forget(storage, previous)
        return tenant

    @staticmethod
    async def _forget(storage: Storage, key: str) -> None:
        """Best effort: a leftover old file is harmless, so a failed delete must not fail the request."""
        try:
            await storage.delete(key)
        except HTTPException:
            pass
