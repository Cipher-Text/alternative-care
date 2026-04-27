"""Appointment service layer with business logic."""

from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Appointment, Visit
from app.shared.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentCancel,
    VisitCreate,
    VisitUpdate,
)


class AppointmentService:
    """Service for managing appointments and visits."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    # ===== Appointment Methods =====

    async def create_appointment(
        self, data: AppointmentCreate, created_by: str
    ) -> Appointment:
        """
        Create a new appointment with time slot validation.

        Args:
            data: Appointment creation data
            created_by: User ID creating the appointment

        Returns:
            Created appointment

        Raises:
            HTTPException: If time slot is unavailable or invalid
        """
        # Validate time slot availability
        is_available = await self.check_time_slot_available(
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            appointment_time=data.appointment_time,
            duration_minutes=data.duration_minutes,
        )

        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot is not available. Doctor has a conflicting appointment.",
            )

        # Create appointment
        appointment = Appointment(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            appointment_time=data.appointment_time,
            duration_minutes=data.duration_minutes,
            reason=data.reason,
            notes=data.notes,
            status="scheduled",
            reminder_sent=False,
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        return appointment

    async def check_time_slot_available(
        self,
        doctor_id: str,
        appointment_date: date,
        appointment_time: time,
        duration_minutes: int,
        exclude_appointment_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a time slot is available for a doctor.

        Args:
            doctor_id: Doctor's user ID
            appointment_date: Date of appointment
            appointment_time: Start time of appointment
            duration_minutes: Duration in minutes
            exclude_appointment_id: Appointment ID to exclude (for updates)

        Returns:
            True if slot is available, False otherwise
        """
        # Calculate new appointment time range
        new_start = datetime.combine(appointment_date, appointment_time)
        new_end = new_start + timedelta(minutes=duration_minutes)

        # Query all appointments for doctor on that date
        query = select(Appointment).where(
            and_(
                Appointment.tenant_id == self.tenant_id,
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status.in_(["scheduled", "confirmed", "in_progress"]),
            )
        )

        # Exclude specific appointment (for updates)
        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)

        result = await self.db.execute(query)
        existing_appointments = result.scalars().all()

        # Check for overlaps in Python
        for existing in existing_appointments:
            existing_start = datetime.combine(
                existing.appointment_date, existing.appointment_time
            )
            existing_end = existing_start + timedelta(
                minutes=existing.duration_minutes
            )

            # Check if time ranges overlap
            if new_start < existing_end and new_end > existing_start:
                return False  # Conflict found

        return True  # No conflicts

    async def get_appointment(self, appointment_id: str) -> Appointment:
        """Get appointment by ID with tenant filtering."""
        result = await self.db.execute(
            select(Appointment).where(
                and_(
                    Appointment.id == appointment_id,
                    Appointment.tenant_id == self.tenant_id,
                )
            )
        )
        appointment = result.scalar_one_or_none()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

        return appointment

    async def list_appointments(
        self,
        appointment_date: Optional[date] = None,
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Appointment]:
        """List appointments with filters."""
        query = select(Appointment).where(Appointment.tenant_id == self.tenant_id)

        if appointment_date:
            query = query.where(Appointment.appointment_date == appointment_date)
        if patient_id:
            query = query.where(Appointment.patient_id == patient_id)
        if doctor_id:
            query = query.where(Appointment.doctor_id == doctor_id)
        if status_filter:
            query = query.where(Appointment.status == status_filter)

        query = (
            query.order_by(
                Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_appointment(
        self, appointment_id: str, data: AppointmentUpdate, updated_by: str
    ) -> Appointment:
        """
        Update appointment with time slot validation.

        Args:
            appointment_id: Appointment ID
            data: Update data
            updated_by: User ID updating the appointment

        Returns:
            Updated appointment
        """
        appointment = await self.get_appointment(appointment_id)

        # If date/time is being changed, validate new time slot
        if data.appointment_date or data.appointment_time or data.duration_minutes:
            new_date = data.appointment_date or appointment.appointment_date
            new_time = data.appointment_time or appointment.appointment_time
            new_duration = data.duration_minutes or appointment.duration_minutes

            is_available = await self.check_time_slot_available(
                doctor_id=appointment.doctor_id,
                appointment_date=new_date,
                appointment_time=new_time,
                duration_minutes=new_duration,
                exclude_appointment_id=appointment_id,
            )

            if not is_available:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="New time slot is not available",
                )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)

        appointment.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(appointment)

        return appointment

    async def cancel_appointment(
        self, appointment_id: str, data: AppointmentCancel, updated_by: str
    ) -> Appointment:
        """Cancel an appointment."""
        appointment = await self.get_appointment(appointment_id)

        appointment.status = "cancelled"
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancellation_reason = data.cancellation_reason
        appointment.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(appointment)

        return appointment

    async def delete_appointment(self, appointment_id: str) -> None:
        """Delete an appointment (hard delete)."""
        appointment = await self.get_appointment(appointment_id)
        await self.db.delete(appointment)
        await self.db.commit()

    async def get_doctor_schedule(
        self, doctor_id: str, start_date: date, end_date: date
    ) -> List[Appointment]:
        """Get all appointments for a doctor in a date range."""
        query = select(Appointment).where(
            and_(
                Appointment.tenant_id == self.tenant_id,
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
                Appointment.status.in_(["scheduled", "confirmed", "in_progress"]),
            )
        ).order_by(Appointment.appointment_date, Appointment.appointment_time)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ===== Visit Methods =====

    async def create_visit(self, data: VisitCreate, created_by: str) -> Visit:
        """
        Create a new visit record.

        Args:
            data: Visit creation data
            created_by: User ID creating the visit

        Returns:
            Created visit
        """
        visit = Visit(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
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
            created_by=created_by,
            updated_by=created_by,
        )

        self.db.add(visit)

        # If linked to appointment, update appointment status
        if data.appointment_id:
            result = await self.db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.id == data.appointment_id,
                        Appointment.tenant_id == self.tenant_id,
                    )
                )
            )
            appointment = result.scalar_one_or_none()
            if appointment:
                appointment.status = "in_progress"

        await self.db.commit()
        await self.db.refresh(visit)

        return visit

    async def get_visit(self, visit_id: str) -> Visit:
        """Get visit by ID with tenant filtering."""
        result = await self.db.execute(
            select(Visit).where(
                and_(
                    Visit.id == visit_id,
                    Visit.tenant_id == self.tenant_id,
                )
            )
        )
        visit = result.scalar_one_or_none()

        if not visit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visit not found",
            )

        return visit

    async def list_visits(
        self,
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        visit_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Visit]:
        """List visits with filters."""
        query = select(Visit).where(Visit.tenant_id == self.tenant_id)

        if patient_id:
            query = query.where(Visit.patient_id == patient_id)
        if doctor_id:
            query = query.where(Visit.doctor_id == doctor_id)
        if visit_date:
            query = query.where(Visit.visit_date == visit_date)

        query = query.order_by(Visit.visit_date.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_visit(
        self, visit_id: str, data: VisitUpdate, updated_by: str
    ) -> Visit:
        """Update visit record."""
        visit = await self.get_visit(visit_id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(visit, field, value)

        visit.updated_by = updated_by

        # If marking as completed, also complete the appointment
        if data.status == "completed" and visit.appointment_id:
            result = await self.db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.id == visit.appointment_id,
                        Appointment.tenant_id == self.tenant_id,
                    )
                )
            )
            appointment = result.scalar_one_or_none()
            if appointment:
                appointment.status = "completed"

        await self.db.commit()
        await self.db.refresh(visit)

        return visit
