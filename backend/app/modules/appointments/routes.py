"""Appointment and Visit API endpoints."""

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models import Appointment, Visit
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


# ===== Appointment Endpoints =====

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant_id
):
    """
    Create a new appointment.

    - Schedules an appointment for a patient with a doctor
    - Validates time slot availability (TODO)
    - Sends confirmation (TODO)
    """
    appointment = Appointment(
        id=str(uuid4()),
        tenant_id="TEMP_TENANT",  # TODO: Get from current_user
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        duration_minutes=data.duration_minutes,
        reason=data.reason,
        notes=data.notes,
        status="scheduled",
        reminder_sent=False,
    )

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    return appointment


@router.get("", response_model=list[AppointmentListItem])
async def list_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    appointment_date: date | None = Query(None, description="Filter by date"),
    patient_id: str | None = Query(None, description="Filter by patient"),
    doctor_id: str | None = Query(None, description="Filter by doctor"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # TODO: Add current_user dependency for tenant filtering
):
    """
    List appointments with filters.

    - Filter by date, patient, doctor, or status
    - Supports pagination
    - Ordered by appointment date and time
    """
    query = select(Appointment).where(Appointment.tenant_id == "TEMP_TENANT")

    if appointment_date:
        query = query.where(Appointment.appointment_date == appointment_date)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if status:
        query = query.where(Appointment.status == status)

    query = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    appointments = result.scalars().all()

    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """Get appointment by ID."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == "TEMP_TENANT",
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """
    Update appointment details.

    - Can update date, time, status, notes, etc.
    - Validates new time slot if date/time changed (TODO)
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == "TEMP_TENANT",
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)

    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: str,
    data: AppointmentCancel,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """
    Cancel an appointment.

    - Sets status to cancelled
    - Records cancellation reason
    - Sends notification (TODO)
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == "TEMP_TENANT",
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    appointment.status = "cancelled"
    appointment.cancellation_reason = data.cancellation_reason

    await db.commit()
    await db.refresh(appointment)

    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """Delete an appointment (soft delete - just cancel it instead)."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == "TEMP_TENANT",
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await db.delete(appointment)
    await db.commit()


# ===== Visit Endpoints =====

visits_router = APIRouter(prefix="/visits", tags=["visits"])


@visits_router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    data: VisitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant_id
):
    """
    Create a new visit record.

    - Can be linked to an appointment or standalone (walk-in)
    - Records clinical information
    - Starts in 'in_progress' status
    """
    visit = Visit(
        id=str(uuid4()),
        tenant_id="TEMP_TENANT",  # TODO: Get from current_user
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        appointment_id=data.appointment_id,
        visit_date=data.visit_date,
        visit_type=data.visit_type,
        chief_complaint=data.chief_complaint,
        history_of_present_illness=data.history_of_present_illness,
        examination_notes=data.examination_notes,
        temperature=data.temperature,
        blood_pressure=data.blood_pressure,
        pulse_rate=data.pulse_rate,
        weight=data.weight,
        provisional_diagnosis=data.provisional_diagnosis,
        treatment_plan=data.treatment_plan,
        follow_up_date=data.follow_up_date,
        follow_up_notes=data.follow_up_notes,
        status="in_progress",
    )

    db.add(visit)

    # If linked to appointment, update appointment status
    if data.appointment_id:
        result = await db.execute(
            select(Appointment).where(Appointment.id == data.appointment_id)
        )
        appointment = result.scalar_one_or_none()
        if appointment:
            appointment.status = "in_progress"

    await db.commit()
    await db.refresh(visit)

    return visit


@visits_router.get("", response_model=list[VisitListItem])
async def list_visits(
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: str | None = Query(None, description="Filter by patient"),
    doctor_id: str | None = Query(None, description="Filter by doctor"),
    visit_date: date | None = Query(None, description="Filter by date"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # TODO: Add current_user dependency for tenant filtering
):
    """
    List visits with filters.

    - Filter by patient, doctor, or date
    - Supports pagination
    - Ordered by visit date (most recent first)
    """
    query = select(Visit).where(Visit.tenant_id == "TEMP_TENANT")

    if patient_id:
        query = query.where(Visit.patient_id == patient_id)
    if doctor_id:
        query = query.where(Visit.doctor_id == doctor_id)
    if visit_date:
        query = query.where(Visit.visit_date == visit_date)

    query = query.order_by(Visit.visit_date.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    visits = result.scalars().all()

    return visits


@visits_router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """Get visit by ID with full clinical details."""
    result = await db.execute(
        select(Visit).where(
            Visit.id == visit_id,
            Visit.tenant_id == "TEMP_TENANT",
        )
    )
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found"
        )

    return visit


@visits_router.patch("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    data: VisitUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Add current_user dependency for tenant filtering
):
    """
    Update visit record.

    - Update clinical information
    - Update vitals
    - Update diagnosis and treatment plan
    - Mark as completed
    """
    result = await db.execute(
        select(Visit).where(
            Visit.id == visit_id,
            Visit.tenant_id == "TEMP_TENANT",
        )
    )
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(visit, field, value)

    # If marking as completed, also complete the appointment
    if data.status == "completed" and visit.appointment_id:
        result = await db.execute(
            select(Appointment).where(Appointment.id == visit.appointment_id)
        )
        appointment = result.scalar_one_or_none()
        if appointment:
            appointment.status = "completed"

    await db.commit()
    await db.refresh(visit)

    return visit


# Include visits router
router.include_router(visits_router)
