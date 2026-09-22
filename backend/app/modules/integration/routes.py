"""Integration API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_tenant_user
from app.core.security import decrypt_credentials
from app.modules.integration.factory import IntegrationProviderFactory
from app.modules.integration.service import IntegrationService
from app.modules.integration.tasks import send_email_task, send_sms_task
from app.shared.schemas import (
    IntegrationLogListItem,
    IntegrationProviderListItem,
    IntegrationProviderResponse,
    IntegrationTestRequest,
    IntegrationTestResponse,
    SendEmailRequest,
    SendOperationResponse,
    SendSMSRequest,
    TenantIntegrationCreate,
    TenantIntegrationListItem,
    TenantIntegrationResponse,
    TenantIntegrationUpdate,
)

router = APIRouter()


def get_integration_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> IntegrationService:
    """Dependency for integration service with tenant context."""
    return IntegrationService(db=db, tenant_id=current_user.tenant_id)


def get_tenant_integration_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_tenant_user)],
) -> IntegrationService:
    """Build an integration service only for tenant-owned settings and logs."""
    return IntegrationService(db=db, tenant_id=current_user.tenant_id)


# ===== Provider Catalog Endpoints =====


@router.get("/providers", response_model=list[IntegrationProviderListItem])
async def list_providers(
    service: Annotated[IntegrationService, Depends(get_integration_service)],
    provider_type: str | None = Query(
        None, description="Filter by type (sms, email, payment)"
    ),
    is_active: bool = Query(True, description="Filter by active status"),
):
    """
    List available integration providers (global catalog).

    - Filter by provider type (sms, email, payment)
    - Shows all platform-supported providers
    - Use this to see what integrations are available
    """
    return await service.list_providers(provider_type=provider_type, is_active=is_active)


@router.get("/providers/{provider_id}", response_model=IntegrationProviderResponse)
async def get_provider(
    provider_id: int,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
):
    """
    Get integration provider details.

    - Shows provider configuration schema
    - Shows supported countries
    - Use this before creating a tenant integration
    """
    return await service.get_provider(provider_id)


# ===== Tenant Integration Endpoints =====


@router.post("/", response_model=TenantIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: TenantIntegrationCreate,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create tenant integration with encrypted credentials.

    - Configure a provider for your tenant
    - Credentials are automatically encrypted
    - Test the integration before using in production
    - Set as primary to use by default
    """
    return await service.create_integration(data, created_by=current_user.user_id)


@router.get("/", response_model=list[TenantIntegrationListItem])
async def list_integrations(
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    provider_type: str | None = Query(None, description="Filter by type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_primary: bool | None = Query(None, description="Filter by primary status"),
):
    """
    List tenant's configured integrations.

    - Filter by provider type
    - See which integrations are active
    - Identify primary integrations per type
    """
    return await service.list_integrations(
        provider_type=provider_type,
        is_active=is_active,
        is_primary=is_primary,
    )


@router.get("/{integration_id}", response_model=TenantIntegrationResponse)
async def get_integration(
    integration_id: int,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
):
    """
    Get integration details.

    - Returns integration configuration
    - Credentials are NOT returned (security)
    - Shows last test status and timestamp
    """
    return await service.get_integration(integration_id)


@router.patch("/{integration_id}", response_model=TenantIntegrationResponse)
async def update_integration(
    integration_id: int,
    data: TenantIntegrationUpdate,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update tenant integration.

    - Update display name
    - Update credentials (re-encrypted automatically)
    - Enable/disable integration
    """
    return await service.update_integration(
        integration_id, data, updated_by=current_user.user_id
    )


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
):
    """
    Delete tenant integration.

    - Cannot delete primary integration (unset first)
    - Permanent deletion
    - Logs are retained for audit trail
    """
    await service.delete_integration(integration_id)


@router.post("/{integration_id}/set-primary", response_model=TenantIntegrationResponse)
async def set_primary_integration(
    integration_id: int,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Set integration as primary for its provider type.

    - Automatically unsets existing primary
    - Primary integration used by default in send operations
    - Only one primary per type (sms, email, payment)
    """
    return await service.set_primary(integration_id, updated_by=current_user.user_id)


# ===== Integration Testing =====


@router.post("/{integration_id}/test", response_model=IntegrationTestResponse)
async def test_integration(
    integration_id: int,
    data: IntegrationTestRequest,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Test integration connection and credentials.

    - For SMS: sends test SMS to provided phone number
    - For Email: sends test email to provided address
    - For Payment: validates credentials (no actual charge)
    - Updates last_tested_at and test_status
    """
    # Get integration and provider
    integration = await service.get_integration(integration_id)
    provider = await service.get_provider(integration.provider_id)

    # Decrypt credentials
    credentials = decrypt_credentials(integration.encrypted_credentials)

    # Create provider service
    provider_service = IntegrationProviderFactory.create_provider(
        provider_name=provider.name,
        credentials=credentials,
    )

    # Test based on provider type
    try:
        if provider.provider_type == "sms":
            if not data.test_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="test_phone required for SMS provider test",
                )

            # Send test SMS
            result = await provider_service.send_sms(
                recipient=data.test_phone,
                message=f"Test SMS from AltCare via {provider.display_name}",
            )

            test_result = IntegrationTestResponse(
                success=result.get("success", False),
                message=f"Test SMS sent to {data.test_phone}",
                test_type="sms",
                provider_name=provider.display_name,
                details=result,
            )

        elif provider.provider_type == "email":
            if not data.test_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="test_email required for Email provider test",
                )

            # Send test email
            result = await provider_service.send_email(
                recipient=data.test_email,
                subject="Test Email from AltCare",
                body_text=f"This is a test email sent via {provider.display_name}.",
                body_html=f"<p>This is a test email sent via <strong>{provider.display_name}</strong>.</p>",
            )

            test_result = IntegrationTestResponse(
                success=result.get("success", False),
                message=f"Test email sent to {data.test_email}",
                test_type="email",
                provider_name=provider.display_name,
                details=result,
            )

        elif provider.provider_type == "payment":
            # Test connection without actual payment
            result = await provider_service.test_connection()

            test_result = IntegrationTestResponse(
                success=result.get("success", False),
                message=result.get("message", "Test completed"),
                test_type="payment",
                provider_name=provider.display_name,
                details=result,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider type: {provider.provider_type}",
            )

        # Update integration test status
        integration.last_tested_at = datetime.utcnow()
        integration.test_status = "success" if test_result.success else "failed"
        await db.commit()

        return test_result

    except Exception as e:
        # Update integration test status
        integration.last_tested_at = datetime.utcnow()
        integration.test_status = "failed"
        await db.commit()

        return IntegrationTestResponse(
            success=False,
            message="Test failed",
            test_type=provider.provider_type,
            provider_name=provider.display_name,
            error=str(e),
        )


# ===== Integration Logs =====


@router.get("/logs", response_model=list[IntegrationLogListItem])
async def list_integration_logs(
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    integration_id: int | None = Query(None, description="Filter by integration ID"),
    transaction_type: str | None = Query(
        None, description="Filter by type (sms_sent, email_sent, etc.)"
    ),
    status: str | None = Query(
        None, description="Filter by status (success, failed, pending)"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List integration transaction logs.

    - Complete audit trail of all API calls
    - Filter by integration, type, or status
    - Includes request/response payloads
    - Useful for debugging and monitoring
    """
    return await service.list_logs(
        tenant_integration_id=integration_id,
        transaction_type=transaction_type,
        status=status,
        limit=limit,
        offset=offset,
    )


# ===== Send Operations =====


@router.post("/send/sms", response_model=SendOperationResponse)
async def send_sms(
    data: SendSMSRequest,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Send SMS via configured provider.

    - Uses primary SMS provider by default
    - Or specify provider_id to use specific provider
    - Queued via Celery for async processing
    - Returns immediately with transaction ID
    """
    # Get integration (primary or specified)
    if data.provider_id:
        integration = await service.get_integration(data.provider_id)
        provider = await service.get_provider(integration.provider_id)

        if provider.provider_type != "sms":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified provider is not an SMS provider",
            )
    else:
        integration = await service.get_primary_integration("sms")

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No primary SMS provider configured. Configure one first.",
            )

    # Queue SMS send task
    task = send_sms_task.delay(
        tenant_id=current_user.tenant_id,
        tenant_integration_id=integration.id,
        recipient=data.recipient,
        message=data.message,
    )

    return SendOperationResponse(
        success=True,
        message=f"SMS queued for sending to {data.recipient}",
        transaction_id=task.id,
        queued=True,
    )


@router.post("/send/email", response_model=SendOperationResponse)
async def send_email(
    data: SendEmailRequest,
    service: Annotated[IntegrationService, Depends(get_tenant_integration_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Send email via configured provider.

    - Uses primary Email provider by default
    - Or specify provider_id to use specific provider
    - Queued via Celery for async processing
    - Supports both HTML and plain text
    """
    # Get integration (primary or specified)
    if data.provider_id:
        integration = await service.get_integration(data.provider_id)
        provider = await service.get_provider(integration.provider_id)

        if provider.provider_type != "email":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified provider is not an Email provider",
            )
    else:
        integration = await service.get_primary_integration("email")

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No primary Email provider configured. Configure one first.",
            )

    # Queue email send task
    task = send_email_task.delay(
        tenant_id=current_user.tenant_id,
        tenant_integration_id=integration.id,
        recipient=data.recipient,
        subject=data.subject,
        body_html=data.body_html,
        body_text=data.body_text,
    )

    return SendOperationResponse(
        success=True,
        message=f"Email queued for sending to {data.recipient}",
        transaction_id=task.id,
        queued=True,
    )
