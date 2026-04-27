"""Appointment and Visit API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.appointments.service import AppointmentService
from app.shared.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentCancel,
    AppointmentResponse,
    AppointmentListItem,
    VisitCreate,
    VisitUpdate,
    VisitResponse,
    VisitListItem,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def get_appointment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AppointmentService:
    """Dependency for appointment service with tenant context."""
    return AppointmentService(db=db, tenant_id=current_user.tenant_id)


# ===== Appointment Endpoints =====


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a new appointment.

    - Schedules an appointment for a patient with a doctor
    - Validates time slot availability
    - Prevents double-booking
    """
    return await service.create_appointment(data, created_by=current_user.user_id)


@router.get("", response_model=list[AppointmentListItem])
async def list_appointments(
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    appointment_date: date | None = Query(None, description="Filter by date"),
    patient_id: str | None = Query(None, description="Filter by patient"),
    doctor_id: str | None = Query(None, description="Filter by doctor"),
    status_filter: str | None = Query(None, description="Filter by status", alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List appointments with filters.

    - Filter by date, patient, doctor, or status
    - Supports pagination
    - Ordered by appointment date and time (most recent first)
    """
    return await service.list_appointments(
        appointment_date=appointment_date,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
):
    """Get appointment by ID with tenant filtering."""
    return await service.get_appointment(appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update appointment details.

    - Can update date, time, status, notes, etc.
    - Validates new time slot if date/time changed
    - Prevents conflicts with existing appointments
    """
    return await service.update_appointment(
        appointment_id, data, updated_by=current_user.user_id
    )


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: str,
    data: AppointmentCancel,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Cancel an appointment.

    - Sets status to cancelled
    - Records cancellation reason and timestamp
    - Can send notification (if configured)
    """
    return await service.cancel_appointment(
        appointment_id, data, updated_by=current_user.user_id
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
):
    """Delete an appointment (hard delete)."""
    await service.delete_appointment(appointment_id)


# ===== Visit Endpoints =====

visits_router = APIRouter(prefix="/visits", tags=["visits"])


def get_visit_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AppointmentService:
    """Dependency for visit service (uses same AppointmentService)."""
    return AppointmentService(db=db, tenant_id=current_user.tenant_id)


@visits_router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    data: VisitCreate,
    service: Annotated[AppointmentService, Depends(get_visit_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Create a new visit record.

    - Can be linked to an appointment or standalone (walk-in)
    - Records clinical information and vitals
    - Starts in 'in_progress' status
    - Updates linked appointment status if present
    """
    return await service.create_visit(data, created_by=current_user.user_id)


@visits_router.get("", response_model=list[VisitListItem])
async def list_visits(
    service: Annotated[AppointmentService, Depends(get_visit_service)],
    patient_id: str | None = Query(None, description="Filter by patient"),
    doctor_id: str | None = Query(None, description="Filter by doctor"),
    visit_date: date | None = Query(None, description="Filter by date"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List visits with filters.

    - Filter by patient, doctor, or date
    - Supports pagination
    - Ordered by visit date (most recent first)
    """
    return await service.list_visits(
        patient_id=patient_id,
        doctor_id=doctor_id,
        visit_date=visit_date,
        limit=limit,
        offset=offset,
    )


@visits_router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    service: Annotated[AppointmentService, Depends(get_visit_service)],
):
    """Get visit by ID with full clinical details and tenant filtering."""
    return await service.get_visit(visit_id)


@visits_router.patch("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    data: VisitUpdate,
    service: Annotated[AppointmentService, Depends(get_visit_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Update visit record.

    - Update clinical information, vitals, diagnosis, treatment plan
    - Mark as completed
    - Automatically completes linked appointment when visit is completed
    """
    return await service.update_visit(visit_id, data, updated_by=current_user.user_id)


# Include visits router
router.include_router(visits_router)
