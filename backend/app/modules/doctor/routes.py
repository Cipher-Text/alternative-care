"""Doctor API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_tenant_user
from app.modules.doctor.service import DoctorService
from app.shared.schemas import (
    DoctorProfileResponse,
    DoctorProfileUpdate,
    DoctorDegreeCreate,
    DoctorDegreeUpdate,
    DoctorDegreeResponse,
    DoctorTrainingCreate,
    DoctorTrainingUpdate,
    DoctorTrainingResponse,
)

router = APIRouter()


def get_doctor_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_tenant_user)],
) -> DoctorService:
    """Dependency for doctor service with user and tenant context."""
    return DoctorService(
        db=db, user_id=current_user.user_id, tenant_id=current_user.tenant_id
    )


# ===== Doctor Profile Endpoints =====


@router.get("/profile", response_model=DoctorProfileResponse)
async def get_doctor_profile(
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """
    Get doctor profile.

    - Combines user and tenant/clinic information
    - Returns complete doctor profile
    """
    return await service.get_profile()


@router.patch("/profile", response_model=DoctorProfileResponse)
async def update_doctor_profile(
    data: DoctorProfileUpdate,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update doctor profile.

    - All fields are optional
    - Updates user and/or clinic information
    - Maintains audit trail
    """
    return await service.update_profile(data, updated_by=current_user.user_id)


# ===== Doctor Degree Endpoints =====


@router.post("/degrees", response_model=DoctorDegreeResponse, status_code=status.HTTP_201_CREATED)
async def create_degree(
    data: DoctorDegreeCreate,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a new doctor degree.

    - Academic degrees (MBBS, BHMS, BAMS, MD, etc.)
    - Include institution and completion year
    - Optional certificate upload
    - Requires admin verification
    """
    return await service.create_degree(data, created_by=current_user.user_id)


@router.get("/degrees", response_model=list[DoctorDegreeResponse])
async def list_degrees(
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """
    List all degrees for the doctor.

    - Ordered by display_order, then completion year (newest first)
    - Includes verification status
    """
    return await service.list_degrees()


@router.get("/degrees/{degree_id}", response_model=DoctorDegreeResponse)
async def get_degree(
    degree_id: int,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """Get degree by ID."""
    return await service.get_degree(degree_id)


@router.patch("/degrees/{degree_id}", response_model=DoctorDegreeResponse)
async def update_degree(
    degree_id: int,
    data: DoctorDegreeUpdate,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update doctor degree.

    - All fields are optional
    - Only updates fields provided in request
    - Verification status unchanged
    """
    return await service.update_degree(
        degree_id, data, updated_by=current_user.user_id
    )


@router.delete("/degrees/{degree_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_degree(
    degree_id: int,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """Delete degree (hard delete)."""
    await service.delete_degree(degree_id)


# ===== Doctor Training Endpoints =====


@router.post("/trainings", response_model=DoctorTrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_training(
    data: DoctorTrainingCreate,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a new doctor training/certification.

    - Types: Certification, Workshop, Conference, Continuing Education
    - Include provider and completion date
    - Optional expiry date for renewable certifications
    - Optional credential ID from issuing organization
    """
    return await service.create_training(data, created_by=current_user.user_id)


@router.get("/trainings", response_model=list[DoctorTrainingResponse])
async def list_trainings(
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    active_only: bool = Query(False, description="Only show non-expired trainings"),
):
    """
    List all trainings for the doctor.

    - Ordered by display_order, then completion date (newest first)
    - Can filter to active (non-expired) certifications only
    - Includes verification status
    """
    return await service.list_trainings(active_only=active_only)


@router.get("/trainings/{training_id}", response_model=DoctorTrainingResponse)
async def get_training(
    training_id: int,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """Get training by ID."""
    return await service.get_training(training_id)


@router.patch("/trainings/{training_id}", response_model=DoctorTrainingResponse)
async def update_training(
    training_id: int,
    data: DoctorTrainingUpdate,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update doctor training.

    - All fields are optional
    - Only updates fields provided in request
    - Verification status unchanged
    """
    return await service.update_training(
        training_id, data, updated_by=current_user.user_id
    )


@router.delete("/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    training_id: int,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
):
    """Delete training (hard delete)."""
    await service.delete_training(training_id)
