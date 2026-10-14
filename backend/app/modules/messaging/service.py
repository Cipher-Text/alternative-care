"""Integration service layer - manages providers and configurations."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_credentials, encrypt_credentials
from app.shared.models import IntegrationLog, IntegrationProvider, TenantIntegration
from app.shared.schemas import TenantIntegrationCreate, TenantIntegrationUpdate


class IntegrationService:
    """Service for managing integration providers and configurations."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    # ===== Provider Catalog Methods =====

    async def list_providers(
        self,
        provider_type: Optional[str] = None,
        is_active: bool = True,
    ) -> list[IntegrationProvider]:
        """List available integration providers (global catalog).

        Args:
            provider_type: Filter by type (sms, email, payment)
            is_active: Filter by active status

        Returns:
            List of integration providers
        """
        query = select(IntegrationProvider)

        if provider_type:
            query = query.where(IntegrationProvider.provider_type == provider_type)
        if is_active:
            query = query.where(IntegrationProvider.is_active == True)

        query = query.order_by(
            IntegrationProvider.provider_type, IntegrationProvider.display_name
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_provider(self, provider_id: int) -> IntegrationProvider:
        """Get provider by ID.

        Args:
            provider_id: Provider ID

        Returns:
            Integration provider

        Raises:
            HTTPException: If provider not found
        """
        result = await self.db.execute(
            select(IntegrationProvider).where(IntegrationProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration provider not found",
            )

        return provider

    # ===== Tenant Integration Methods =====

    async def create_integration(
        self, data: TenantIntegrationCreate, created_by: str
    ) -> TenantIntegration:
        """Create tenant integration with encrypted credentials.

        Args:
            data: Integration creation data
            created_by: User ID creating the integration

        Returns:
            Created tenant integration

        Raises:
            HTTPException: If provider not found or validation fails
        """
        # Verify provider exists and is active
        provider = await self.get_provider(data.provider_id)

        if not provider.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider is not active",
            )

        # Encrypt credentials
        encrypted_creds = encrypt_credentials(data.credentials)

        # Create integration
        integration = TenantIntegration(
            tenant_id=self.tenant_id,
            provider_id=data.provider_id,
            display_name=data.display_name or provider.display_name,
            encrypted_credentials=encrypted_creds,
            is_active=data.is_active,
            is_primary=False,  # Set via set_primary endpoint
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)

        return integration

    async def get_integration(self, integration_id: int) -> TenantIntegration:
        """Get tenant integration by ID.

        Args:
            integration_id: Integration ID

        Returns:
            Tenant integration

        Raises:
            HTTPException: If integration not found
        """
        result = await self.db.execute(
            select(TenantIntegration).where(
                and_(
                    TenantIntegration.id == integration_id,
                    TenantIntegration.tenant_id == self.tenant_id,
                )
            )
        )
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        return integration

    async def list_integrations(
        self,
        provider_type: Optional[str] = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
    ) -> list[TenantIntegration]:
        """List tenant's integrations.

        Args:
            provider_type: Filter by provider type
            is_active: Filter by active status
            is_primary: Filter by primary status

        Returns:
            List of tenant integrations
        """
        query = select(TenantIntegration).where(
            TenantIntegration.tenant_id == self.tenant_id
        )

        if provider_type:
            # Join with provider to filter by type
            query = query.join(
                IntegrationProvider,
                TenantIntegration.provider_id == IntegrationProvider.id,
            ).where(IntegrationProvider.provider_type == provider_type)

        if is_active is not None:
            query = query.where(TenantIntegration.is_active == is_active)

        if is_primary is not None:
            query = query.where(TenantIntegration.is_primary == is_primary)

        query = query.order_by(TenantIntegration.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_integration(
        self, integration_id: int, data: TenantIntegrationUpdate, updated_by: str
    ) -> TenantIntegration:
        """Update tenant integration.

        Args:
            integration_id: Integration ID
            data: Update data
            updated_by: User ID updating the integration

        Returns:
            Updated integration
        """
        integration = await self.get_integration(integration_id)

        # Update fields
        if data.display_name is not None:
            integration.display_name = data.display_name

        if data.credentials is not None:
            # Re-encrypt new credentials
            integration.encrypted_credentials = encrypt_credentials(data.credentials)

        if data.is_active is not None:
            integration.is_active = data.is_active

        integration.updated_by = updated_by
        integration.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(integration)

        return integration

    async def delete_integration(self, integration_id: int) -> None:
        """Delete tenant integration.

        Args:
            integration_id: Integration ID

        Raises:
            HTTPException: If integration is primary (must unset first)
        """
        integration = await self.get_integration(integration_id)

        if integration.is_primary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete primary integration. Set another as primary first.",
            )

        await self.db.delete(integration)
        await self.db.commit()

    async def set_primary(
        self, integration_id: int, updated_by: str
    ) -> TenantIntegration:
        """Set integration as primary for its provider type.

        Args:
            integration_id: Integration ID to set as primary
            updated_by: User ID making the change

        Returns:
            Updated integration
        """
        integration = await self.get_integration(integration_id)

        # Get provider to find type
        provider = await self.get_provider(integration.provider_id)

        # Unset any existing primary for this type
        result = await self.db.execute(
            select(TenantIntegration)
            .join(
                IntegrationProvider,
                TenantIntegration.provider_id == IntegrationProvider.id,
            )
            .where(
                and_(
                    TenantIntegration.tenant_id == self.tenant_id,
                    IntegrationProvider.provider_type == provider.provider_type,
                    TenantIntegration.is_primary == True,
                )
            )
        )
        existing_primary = result.scalar_one_or_none()

        if existing_primary:
            existing_primary.is_primary = False
            existing_primary.updated_at = datetime.utcnow()

        # Set new primary
        integration.is_primary = True
        integration.updated_by = updated_by
        integration.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(integration)

        return integration

    async def get_primary_integration(
        self, provider_type: str
    ) -> Optional[TenantIntegration]:
        """Get tenant's primary integration for a provider type.

        Args:
            provider_type: Provider type (sms, email, payment)

        Returns:
            Primary integration or None
        """
        result = await self.db.execute(
            select(TenantIntegration)
            .join(
                IntegrationProvider,
                TenantIntegration.provider_id == IntegrationProvider.id,
            )
            .where(
                and_(
                    TenantIntegration.tenant_id == self.tenant_id,
                    IntegrationProvider.provider_type == provider_type,
                    TenantIntegration.is_primary == True,
                    TenantIntegration.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_decrypted_credentials(self, integration_id: int) -> dict:
        """Get decrypted credentials for an integration.

        Args:
            integration_id: Integration ID

        Returns:
            Decrypted credentials dict

        Note: Use sparingly - credentials should be loaded only when needed
        """
        integration = await self.get_integration(integration_id)
        return decrypt_credentials(integration.encrypted_credentials)

    # ===== Integration Log Methods =====

    async def create_log(
        self,
        tenant_integration_id: int,
        transaction_type: str,
        status: str,
        request_payload: Optional[dict] = None,
        response_payload: Optional[dict] = None,
        response_status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        external_reference: Optional[str] = None,
        recipient: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> IntegrationLog:
        """Create integration log entry.

        Args:
            tenant_integration_id: Integration ID
            transaction_type: Type (sms_sent, email_sent, payment_initiated, etc.)
            status: Status (pending, success, failed)
            ... (other optional fields)

        Returns:
            Created log entry
        """
        log = IntegrationLog(
            tenant_id=self.tenant_id,
            tenant_integration_id=tenant_integration_id,
            transaction_type=transaction_type,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            response_status_code=response_status_code,
            error_message=error_message,
            external_reference=external_reference,
            recipient=recipient,
            amount=amount,
            currency=currency,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        return log

    async def list_logs(
        self,
        tenant_integration_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IntegrationLog]:
        """List integration logs.

        Args:
            tenant_integration_id: Filter by integration
            transaction_type: Filter by transaction type
            status: Filter by status
            limit: Results limit
            offset: Results offset

        Returns:
            List of integration logs
        """
        query = select(IntegrationLog).where(
            IntegrationLog.tenant_id == self.tenant_id
        )

        if tenant_integration_id:
            query = query.where(
                IntegrationLog.tenant_integration_id == tenant_integration_id
            )

        if transaction_type:
            query = query.where(IntegrationLog.transaction_type == transaction_type)

        if status:
            query = query.where(IntegrationLog.status == status)

        query = query.order_by(IntegrationLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())
