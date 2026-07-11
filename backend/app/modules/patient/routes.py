"""Patient API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.patient.service import PatientService
from app.shared.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItem,
    PatientTagCreate,
    PatientTagUpdate,
    PatientTagResponse,
    PatientDiagnosisCreate,
    PatientDiagnosisUpdate,
    PatientDiagnosisResponse,
)

router = APIRouter()


def get_patient_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PatientService:
    """Dependency for patient service with tenant context."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform users cannot manage patient records. Use a tenant account.",
        )
    return PatientService(db=db, tenant_id=current_user.tenant_id)


# ===== Patient Endpoints =====


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a new patient.

    - Automatically scoped to authenticated user's tenant
    - All fields except full_name are optional
    - Returns complete patient record
    """
    return await service.create_patient(data, created_by=current_user.user_id)


@router.get("", response_model=list[PatientListItem])
async def list_patients(
    service: Annotated[PatientService, Depends(get_patient_service)],
    search: str | None = Query(None, description="Search by name, phone, or email"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    has_upcoming_visit: bool | None = Query(
        None, description="Filter patients with upcoming visits"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List patients with filters.

    - Search by name, phone, or email (case-insensitive)
    - Filter by active status
    - Filter patients with upcoming scheduled visits
    - Supports pagination
    - Ordered by most recently created
    """
    return await service.list_patients(
        search=search,
        is_active=is_active,
        has_upcoming_visit=has_upcoming_visit,
        limit=limit,
        offset=offset,
    )


@router.get("/count", response_model=dict)
async def get_patient_count(
    service: Annotated[PatientService, Depends(get_patient_service)],
):
    """
    Get total count of active patients.

    - Returns count of active patients for tenant
    - Useful for dashboard statistics
    """
    count = await service.get_patient_count()
    return {"count": count}


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
):
    """Get patient by ID with full details and tenant filtering."""
    return await service.get_patient(patient_id)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update patient information.

    - All fields are optional
    - Only updates fields provided in request
    - Maintains audit trail (updated_by)
    """
    return await service.update_patient(
        patient_id, data, updated_by=current_user.user_id
    )


@router.delete("/{patient_id}", response_model=PatientResponse)
async def delete_patient(
    patient_id: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Soft delete a patient.

    - Sets is_active=False (soft delete)
    - Patient data is preserved for records
    - Can be reactivated by updating is_active=True
    """
    return await service.delete_patient(patient_id, updated_by=current_user.user_id)


# ===== Patient Tag Endpoints =====


@router.post(
    "/{patient_id}/tags",
    response_model=PatientTagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient_tag(
    patient_id: str,
    data: PatientTagCreate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a tag for a patient.

    - Tag types: special_case, chronic, treatment, allergy
    - Used for categorization and quick filtering
    - Can add multiple tags per patient
    """
    # Override patient_id from URL
    data.patient_id = patient_id
    return await service.create_patient_tag(data, created_by=current_user.user_id)


@router.get("/{patient_id}/tags", response_model=list[PatientTagResponse])
async def list_patient_tags(
    patient_id: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
):
    """
    List all tags for a patient.

    - Ordered by most recently created
    - Returns all tag types
    """
    return await service.list_patient_tags(patient_id)


@router.patch("/tags/{tag_id}", response_model=PatientTagResponse)
async def update_patient_tag(
    tag_id: int,
    data: PatientTagUpdate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Update patient tag."""
    return await service.update_patient_tag(
        tag_id, data, updated_by=current_user.user_id
    )


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_tag(
    tag_id: int,
    service: Annotated[PatientService, Depends(get_patient_service)],
):
    """Delete patient tag (hard delete)."""
    await service.delete_patient_tag(tag_id)


# ===== Patient Diagnosis Endpoints =====


@router.post(
    "/{patient_id}/diagnoses",
    response_model=PatientDiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient_diagnosis(
    patient_id: str,
    data: PatientDiagnosisCreate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a diagnosis for a patient.

    - Can be linked to a visit (optional)
    - Supports ICD codes (optional)
    - Maintains diagnosis history
    """
    # Override patient_id from URL
    data.patient_id = patient_id
    return await service.create_patient_diagnosis(
        data, created_by=current_user.user_id
    )


@router.get("/{patient_id}/diagnoses", response_model=list[PatientDiagnosisResponse])
async def list_patient_diagnoses(
    patient_id: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
    active_only: bool = Query(True, description="Only show active diagnoses"),
):
    """
    List all diagnoses for a patient.

    - Ordered by diagnosis date (most recent first)
    - Can filter to active diagnoses only
    - Includes historical diagnoses
    """
    return await service.list_patient_diagnoses(patient_id, active_only=active_only)


@router.patch("/diagnoses/{diagnosis_id}", response_model=PatientDiagnosisResponse)
async def update_patient_diagnosis(
    diagnosis_id: int,
    data: PatientDiagnosisUpdate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update patient diagnosis.

    - Can update description, ICD code, date, or status
    - Maintains audit trail
    """
    return await service.update_patient_diagnosis(
        diagnosis_id, data, updated_by=current_user.user_id
    )


@router.delete("/diagnoses/{diagnosis_id}", response_model=PatientDiagnosisResponse)
async def delete_patient_diagnosis(
    diagnosis_id: int,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Soft delete a diagnosis.

    - Sets is_active=False (soft delete)
    - Diagnosis is preserved for records
    - Can be reactivated if needed
    """
    return await service.delete_patient_diagnosis(
        diagnosis_id, updated_by=current_user.user_id
    )
