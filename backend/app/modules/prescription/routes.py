"""Prescription API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, RequireDoctor
from app.modules.prescription.service import PrescriptionService
from app.shared.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
    PrescriptionListItem,
    PrescriptionItemCreate,
    PrescriptionItemResponse,
)

router = APIRouter()


def get_prescription_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PrescriptionService:
    """Dependency for prescription service with tenant context."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform users cannot manage prescription records. Use a tenant account.",
        )
    return PrescriptionService(db=db, tenant_id=current_user.tenant_id)


# ===== Prescription Endpoints =====


@router.post("", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionCreate,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    current_user: RequireDoctor,
):
    """
    Create a new prescription with items.

    - Only doctors can create prescriptions
    - Automatically scoped to authenticated user's tenant
    - Can create as draft or directly issue
    - Items are included in the request body
    - Returns complete prescription with items
    """
    return await service.create_prescription(data, prescribed_by=current_user.user_id)


@router.get("", response_model=list[PrescriptionListItem])
async def list_prescriptions(
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    patient_id: str | None = Query(None, description="Filter by patient ID"),
    visit_id: str | None = Query(None, description="Filter by visit ID"),
    status: str | None = Query(None, description="Filter by status (draft, issued, voided)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List prescriptions with filters.

    - Filter by patient, visit, or status
    - Supports pagination
    - Ordered by most recently created
    - Items not included in list (use get endpoint for details)
    """
    return await service.list_prescriptions(
        patient_id=patient_id,
        visit_id=visit_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: str,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
):
    """
    Get prescription by ID with full details.

    - Returns complete prescription with all items
    - Tenant filtering applied automatically
    """
    return await service.get_prescription(prescription_id)


@router.patch("/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: str,
    data: PrescriptionUpdate,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    current_user: RequireDoctor,
):
    """
    Update a prescription.

    - Only draft prescriptions can be updated
    - Cannot update issued or voided prescriptions
    - All fields are optional
    - Maintains audit trail (updated_by)
    """
    return await service.update_prescription(
        prescription_id, data, updated_by=current_user.user_id
    )


@router.post("/{prescription_id}/void", response_model=PrescriptionResponse)
async def void_prescription(
    prescription_id: str,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    current_user: RequireDoctor,
):
    """
    Void a prescription.

    - Marks prescription as voided (cannot be undone)
    - Voided prescriptions cannot be edited or issued
    - Only doctors can void prescriptions
    """
    return await service.void_prescription(prescription_id, updated_by=current_user.user_id)


@router.post("/{prescription_id}/generate-pdf", response_model=dict)
async def generate_prescription_pdf(
    prescription_id: str,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
):
    """
    Generate PDF for a prescription.

    - Only works for issued prescriptions (not drafts)
    - Returns PDF URL
    - PDF is stored in MinIO/S3
    - Updates prescription with pdf_url and timestamp
    """
    pdf_url = await service.generate_pdf(prescription_id)
    return {"pdf_url": pdf_url}


# ===== Prescription Item Endpoints =====


@router.post(
    "/{prescription_id}/items",
    response_model=PrescriptionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_prescription_item(
    prescription_id: str,
    data: PrescriptionItemCreate,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    current_user: RequireDoctor,
):
    """
    Add an item to a prescription.

    - Only works for draft prescriptions
    - Cannot add items to issued or voided prescriptions
    - Only doctors can add items
    """
    return await service.add_prescription_item(
        prescription_id, data, created_by=current_user.user_id
    )


@router.delete(
    "/{prescription_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_prescription_item(
    prescription_id: str,
    item_id: int,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    current_user: RequireDoctor,
):
    """
    Delete an item from a prescription.

    - Only works for draft prescriptions
    - Cannot delete items from issued or voided prescriptions
    - Only doctors can delete items
    """
    await service.delete_prescription_item(
        prescription_id, item_id, deleted_by=current_user.user_id
    )
    return None
