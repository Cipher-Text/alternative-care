"""Appointment reminder functionality."""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Appointment


class ReminderService:
    """Service for managing appointment reminders."""

    def __init__(self, db: AsyncSession):
        """Initialize reminder service."""
        self.db = db

    async def get_appointments_needing_reminders(
        self, hours_before: int = 24
    ) -> List[Appointment]:
        """
        Get appointments that need reminders sent.

        Args:
            hours_before: How many hours before appointment to send reminder

        Returns:
            List of appointments needing reminders
        """
        now = datetime.utcnow()
        reminder_window_start = now
        reminder_window_end = now + timedelta(hours=hours_before + 1)

        query = select(Appointment).where(
            and_(
                # Appointment is scheduled or confirmed
                Appointment.status.in_(["scheduled", "confirmed"]),
                # Reminder not yet sent
                Appointment.reminder_sent == False,  # noqa: E712
                # Appointment is within reminder window
                Appointment.appointment_date >= reminder_window_start.date(),
                Appointment.appointment_date <= reminder_window_end.date(),
            )
        )

        result = await self.db.execute(query)
        appointments = result.scalars().all()

        # Filter by exact datetime (date + time)
        filtered_appointments = []
        for apt in appointments:
            apt_datetime = datetime.combine(
                apt.appointment_date, apt.appointment_time
            )
            time_until_apt = apt_datetime - now

            # Send reminder if appointment is between hours_before-1 and hours_before hours away
            if timedelta(hours=hours_before - 1) <= time_until_apt <= timedelta(
                hours=hours_before
            ):
                filtered_appointments.append(apt)

        return filtered_appointments

    async def mark_reminder_sent(self, appointment_id: str) -> None:
        """Mark reminder as sent for an appointment."""
        result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()

        if appointment:
            appointment.reminder_sent = True
            await self.db.commit()

    async def send_appointment_reminder(
        self, appointment: Appointment, tenant_id: str
    ) -> bool:
        """
        Send appointment reminder via SMS/Email.

        This is a placeholder that will integrate with the notification module
        and tenant integration settings (SMS/Email providers).

        Args:
            appointment: Appointment to send reminder for
            tenant_id: Tenant ID for fetching integration settings

        Returns:
            True if reminder sent successfully
        """
        # TODO: Integrate with notification module
        # TODO: Fetch tenant's SMS/Email provider settings
        # TODO: Load patient contact information
        # TODO: Send SMS/Email using configured provider
        # TODO: Log to integration_logs table

        # For now, just mark as sent
        await self.mark_reminder_sent(appointment.id)
        return True

    async def send_reminders_batch(self, hours_before: int = 24) -> dict:
        """
        Send reminders for all appointments in the reminder window.

        Args:
            hours_before: Hours before appointment to send reminder

        Returns:
            Summary of reminder sending results
        """
        appointments = await self.get_appointments_needing_reminders(hours_before)

        sent_count = 0
        failed_count = 0
        failed_appointments = []

        for appointment in appointments:
            try:
                success = await self.send_appointment_reminder(
                    appointment, appointment.tenant_id
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    failed_appointments.append(appointment.id)
            except Exception as e:
                failed_count += 1
                failed_appointments.append(
                    {"appointment_id": appointment.id, "error": str(e)}
                )

        return {
            "total_checked": len(appointments),
            "sent": sent_count,
            "failed": failed_count,
            "failed_appointments": failed_appointments,
        }
