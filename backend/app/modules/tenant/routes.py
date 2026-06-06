"""Tenant/Clinic profile management API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.tenant.service import TenantService
from app.shared.schemas import (
    TenantResponse,
    TenantProfileUpdate,
)

router = APIRouter()


def get_tenant_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TenantService:
    """
    Dependency for tenant service.

    Raises:
        HTTPException: 403 if user is not part of a tenant (platform users)
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant users can access clinic profile"
        )
    return TenantService(db=db, tenant_id=current_user.tenant_id)


# ===== Tenant Profile Management =====


@router.get("/profile", response_model=TenantResponse)
async def get_clinic_profile(
    service: Annotated[TenantService, Depends(get_tenant_service)],
):
    """
    Get current clinic/tenant profile.

    - Returns complete clinic information (Phase 1 fields)
    - Available to all tenant users (doctor, receptionist)
    - Includes: contact, address, location, branding, fees, etc.

    **Example Response:**
    ```json
    {
        "id": "uuid",
        "name": "Dr. ABC",
        "clinic_name": "ABC Homeopathic Clinic",
        "clinic_phone": "+8801712345678",
        "clinic_email": "clinic@example.com",
        "address_line_1": "123 Main Street",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "specializations": ["homeopathy"],
        "consultation_fee": 50000,
        "logo_url": "https://..."
    }
    ```
    """
    return await service.get_tenant_profile()


@router.patch("/profile", response_model=TenantResponse)
async def update_clinic_profile(
    data: TenantProfileUpdate,
    service: Annotated[TenantService, Depends(get_tenant_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update clinic/tenant profile.

    - **Only doctors can update** (receptionist read-only)
    - Partial updates supported (only send fields you want to change)
    - All fields are optional

    **Phase 1 Fields:**
    - Contact: `clinic_phone`, `clinic_email`, `clinic_whatsapp`
    - Address: `address_line_1`, `address_line_2`, `postal_code`, `landmark`
    - Location: `division_id`, `district_id`, `upazila_id`, `latitude`, `longitude`
    - Professional: `registration_body`, `registration_number`, `years_of_experience`
    - Branding: `logo_url`, `description_en`, `description_bn`
    - Fees: `consultation_fee`, `follow_up_fee` (in paisa)

    **Example Request:**
    ```json
    {
        "clinic_name": "ABC Homeopathic Clinic",
        "clinic_phone": "+8801712345678",
        "address_line_1": "123 Main Street",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "consultation_fee": 50000,
        "description_en": "Specialized in chronic diseases"
    }
    ```

    **Fee Format:**
    - Fees are stored in **paisa** (100 paisa = 1 BDT)
    - Example: 500 BDT = 50000 paisa
    - This ensures precision for fractional amounts

    **Requires:** Doctor role
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update clinic profile"
        )

    return await service.update_tenant_profile(data, updated_by=current_user.user_id)

