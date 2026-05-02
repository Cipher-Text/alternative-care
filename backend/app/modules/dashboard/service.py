"""Dashboard and analytics service layer."""

from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import (
    Patient,
    Appointment,
    Visit,
    Payment,
    Invoice,
    Prescription,
    PrescriptionItem,
    PatientDiagnosis,
)
from app.shared.schemas import (
    OverviewStats,
    FinancialAnalytics,
    RevenueByMethod,
    PatientAnalytics,
    PatientDemographics,
    AgeGroupDistribution,
    TopDiagnosis,
    AppointmentAnalytics,
    AppointmentByStatus,
    AppointmentByType,
    VisitAnalytics,
    VisitByType,
    TopChiefComplaint,
    PrescriptionAnalytics,
    PrescriptionByStatus,
    TopMedicine,
    TrendData,
)


class DashboardService:
    """Service for dashboard analytics and statistics."""

    def __init__(self, db: AsyncSession, tenant_id: str):
        """Initialize service with database session and tenant context."""
        self.db = db
        self.tenant_id = tenant_id

    async def get_overview(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> OverviewStats:
        """Get high-level overview statistics."""
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        total_patients = await self._count_total_patients()
        new_patients_this_month = await self._count_new_patients_in_month()
        active_patients = await self._count_active_patients(days=30)
        total_appointments = await self._count_total_appointments()
        upcoming_appointments = await self._count_upcoming_appointments()
        appointments_today = await self._count_appointments_today()
        total_visits = await self._count_total_visits()
        visits_this_month = await self._count_visits_in_month()
        total_revenue = await self._calculate_total_revenue()
        revenue_this_month = await self._calculate_revenue_in_month()
        pending_payments = await self._calculate_pending_payments()
        total_prescriptions = await self._count_total_prescriptions()
        prescriptions_this_month = await self._count_prescriptions_in_month()

        return OverviewStats(
            total_patients=total_patients,
            new_patients_this_month=new_patients_this_month,
            active_patients=active_patients,
            total_appointments=total_appointments,
            upcoming_appointments=upcoming_appointments,
            appointments_today=appointments_today,
            total_visits=total_visits,
            visits_this_month=visits_this_month,
            total_revenue=total_revenue,
            revenue_this_month=revenue_this_month,
            pending_payments=pending_payments,
            total_prescriptions=total_prescriptions,
            prescriptions_this_month=prescriptions_this_month,
            period_start=date_from,
            period_end=date_to,
        )

    async def get_financial_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> FinancialAnalytics:
        """Get financial analytics and revenue metrics."""
        query = select(Payment).where(Payment.tenant_id == self.tenant_id)

        if date_from:
            query = query.where(Payment.payment_date >= date_from)
        if date_to:
            query = query.where(Payment.payment_date <= date_to)

        result = await self.db.execute(query)
        payments = result.scalars().all()

        total_payments = len(payments)
        total_revenue = sum(p.amount for p in payments)
        average_payment = total_revenue / total_payments if total_payments > 0 else 0.0

        paid_amount = sum(p.amount for p in payments if p.status == "paid")
        pending_amount = sum(p.amount for p in payments if p.status == "pending")
        refunded_amount = sum(p.amount for p in payments if p.status == "refunded")

        cash_amount = sum(
            p.amount for p in payments if p.payment_method == "cash" and p.status == "paid"
        )
        bkash_amount = sum(
            p.amount for p in payments if p.payment_method == "bkash" and p.status == "paid"
        )

        invoice_stats = await self._get_invoice_stats(date_from, date_to)
        daily_revenue = await self._get_daily_revenue_trend(date_from, date_to)

        return FinancialAnalytics(
            total_revenue=total_revenue,
            total_payments=total_payments,
            average_payment=average_payment,
            paid_amount=paid_amount,
            pending_amount=pending_amount,
            refunded_amount=refunded_amount,
            revenue_by_method=RevenueByMethod(
                cash=cash_amount, bkash=bkash_amount, other=0.0
            ),
            total_invoices=invoice_stats["total"],
            paid_invoices=invoice_stats["paid"],
            overdue_invoices=invoice_stats["overdue"],
            overdue_amount=invoice_stats["overdue_amount"],
            daily_revenue=daily_revenue,
            period_start=date_from,
            period_end=date_to,
        )

    async def get_patient_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> PatientAnalytics:
        """Get patient analytics and demographics."""
        total_patients = await self._count_total_patients()
        new_patients = await self._count_new_patients(date_from, date_to)
        active_patients = await self._count_active_patients(days=30)
        demographics = await self._get_patient_demographics()
        age_distribution = await self._get_age_distribution()
        top_diagnoses = await self._get_top_diagnoses(limit=10)
        patient_growth = await self._get_patient_growth_trend(date_from, date_to)

        return PatientAnalytics(
            total_patients=total_patients,
            new_patients=new_patients,
            active_patients=active_patients,
            demographics=demographics,
            age_distribution=age_distribution,
            top_diagnoses=top_diagnoses,
            patient_growth=patient_growth,
            period_start=date_from,
            period_end=date_to,
        )

    async def get_appointment_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> AppointmentAnalytics:
        """Get appointment analytics and booking metrics."""
        query = select(Appointment).where(Appointment.tenant_id == self.tenant_id)

        if date_from:
            query = query.where(func.date(Appointment.appointment_date) >= date_from)
        if date_to:
            query = query.where(func.date(Appointment.appointment_date) <= date_to)

        result = await self.db.execute(query)
        appointments = result.scalars().all()

        total_appointments = len(appointments)
        upcoming_appointments = sum(
            1 for a in appointments if a.status in ["scheduled", "confirmed"]
        )
        completed_appointments = sum(1 for a in appointments if a.status == "completed")

        cancelled_count = sum(1 for a in appointments if a.status == "cancelled")
        cancellation_rate = (
            (cancelled_count / total_appointments * 100) if total_appointments > 0 else 0.0
        )

        by_status = AppointmentByStatus(
            scheduled=sum(1 for a in appointments if a.status == "scheduled"),
            confirmed=sum(1 for a in appointments if a.status == "confirmed"),
            completed=sum(1 for a in appointments if a.status == "completed"),
            cancelled=sum(1 for a in appointments if a.status == "cancelled"),
            no_show=sum(1 for a in appointments if a.status == "no_show"),
        )

        # Note: Appointment model doesn't have appointment_type field, only 'reason' (free text)
        # TODO: Add appointment_type field to Appointment model or parse from reason field
        by_type = AppointmentByType(
            consultation=0,  # Placeholder until appointment_type field is added
            follow_up=0,
            emergency=0,
        )

        booking_trend = await self._get_appointment_booking_trend(date_from, date_to)
        peak_hours = self._calculate_peak_hours(appointments)

        return AppointmentAnalytics(
            total_appointments=total_appointments,
            upcoming_appointments=upcoming_appointments,
            completed_appointments=completed_appointments,
            cancellation_rate=cancellation_rate,
            by_status=by_status,
            by_type=by_type,
            booking_trend=booking_trend,
            peak_hours=peak_hours,
            period_start=date_from,
            period_end=date_to,
        )

    async def get_visit_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> VisitAnalytics:
        """Get visit analytics and patient encounter metrics."""
        query = select(Visit).where(Visit.tenant_id == self.tenant_id)

        if date_from:
            query = query.where(func.date(Visit.visit_date) >= date_from)
        if date_to:
            query = query.where(func.date(Visit.visit_date) <= date_to)

        result = await self.db.execute(query)
        visits = result.scalars().all()

        total_visits = len(visits)
        patient_count = await self._count_total_patients()
        average_visits_per_patient = total_visits / patient_count if patient_count > 0 else 0.0

        by_type = VisitByType(
            consultation=sum(1 for v in visits if v.visit_type == "consultation"),
            follow_up=sum(1 for v in visits if v.visit_type == "follow_up"),
            emergency=sum(1 for v in visits if v.visit_type == "emergency"),
        )

        top_complaints = await self._get_top_complaints(limit=10, date_from=date_from, date_to=date_to)
        visit_trend = await self._get_visit_trend(date_from, date_to)

        return VisitAnalytics(
            total_visits=total_visits,
            average_visits_per_patient=average_visits_per_patient,
            by_type=by_type,
            top_complaints=top_complaints,
            visit_trend=visit_trend,
            period_start=date_from,
            period_end=date_to,
        )

    async def get_prescription_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> PrescriptionAnalytics:
        """Get prescription analytics and medication metrics."""
        query = select(Prescription).where(Prescription.tenant_id == self.tenant_id)

        if date_from:
            query = query.where(func.date(Prescription.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(Prescription.created_at) <= date_to)

        result = await self.db.execute(query)
        prescriptions = result.scalars().all()

        total_prescriptions = len(prescriptions)

        items_query = select(func.count(PrescriptionItem.id)).where(
            PrescriptionItem.prescription_id.in_([p.id for p in prescriptions])
        )
        items_result = await self.db.execute(items_query)
        total_items = items_result.scalar() or 0

        average_items_per_prescription = (
            total_items / total_prescriptions if total_prescriptions > 0 else 0.0
        )

        by_status = PrescriptionByStatus(
            draft=sum(1 for p in prescriptions if p.status == "draft"),
            issued=sum(1 for p in prescriptions if p.status == "issued"),
            voided=sum(1 for p in prescriptions if p.status == "voided"),
        )

        top_medicines = await self._get_top_medicines(limit=10, date_from=date_from, date_to=date_to)
        prescription_trend = await self._get_prescription_trend(date_from, date_to)

        return PrescriptionAnalytics(
            total_prescriptions=total_prescriptions,
            total_items=total_items,
            average_items_per_prescription=average_items_per_prescription,
            by_status=by_status,
            top_medicines=top_medicines,
            prescription_trend=prescription_trend,
            period_start=date_from,
            period_end=date_to,
        )

    # Helper methods
    async def _count_total_patients(self) -> int:
        result = await self.db.execute(
            select(func.count(Patient.id)).where(Patient.tenant_id == self.tenant_id)
        )
        return result.scalar() or 0

    async def _count_new_patients(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> int:
        query = select(func.count(Patient.id)).where(Patient.tenant_id == self.tenant_id)
        if date_from:
            query = query.where(func.date(Patient.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(Patient.created_at) <= date_to)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_new_patients_in_month(self) -> int:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        return await self._count_new_patients(date_from=first_day, date_to=today)

    async def _count_active_patients(self, days: int = 30) -> int:
        cutoff_date = date.today() - timedelta(days=days)
        result = await self.db.execute(
            select(func.count(func.distinct(Visit.patient_id))).where(
                and_(
                    Visit.tenant_id == self.tenant_id,
                    func.date(Visit.visit_date) >= cutoff_date,
                )
            )
        )
        return result.scalar() or 0

    async def _count_total_appointments(self) -> int:
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(Appointment.tenant_id == self.tenant_id)
        )
        return result.scalar() or 0

    async def _count_upcoming_appointments(self) -> int:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.tenant_id == self.tenant_id,
                    Appointment.appointment_date >= now,
                    Appointment.status.in_(["scheduled", "confirmed"]),
                )
            )
        )
        return result.scalar() or 0

    async def _count_appointments_today(self) -> int:
        today = date.today()
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.tenant_id == self.tenant_id,
                    func.date(Appointment.appointment_date) == today,
                )
            )
        )
        return result.scalar() or 0

    async def _count_total_visits(self) -> int:
        result = await self.db.execute(
            select(func.count(Visit.id)).where(Visit.tenant_id == self.tenant_id)
        )
        return result.scalar() or 0

    async def _count_visits_in_month(self) -> int:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        result = await self.db.execute(
            select(func.count(Visit.id)).where(
                and_(
                    Visit.tenant_id == self.tenant_id,
                    func.date(Visit.visit_date) >= first_day,
                    func.date(Visit.visit_date) <= today,
                )
            )
        )
        return result.scalar() or 0

    async def _calculate_total_revenue(self) -> float:
        result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                and_(Payment.tenant_id == self.tenant_id, Payment.status == "paid")
            )
        )
        return float(result.scalar() or 0.0)

    async def _calculate_revenue_in_month(self) -> float:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.tenant_id == self.tenant_id,
                    Payment.status == "paid",
                    Payment.payment_date >= first_day,
                    Payment.payment_date <= today,
                )
            )
        )
        return float(result.scalar() or 0.0)

    async def _calculate_pending_payments(self) -> float:
        result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                and_(Payment.tenant_id == self.tenant_id, Payment.status == "pending")
            )
        )
        return float(result.scalar() or 0.0)

    async def _count_total_prescriptions(self) -> int:
        result = await self.db.execute(
            select(func.count(Prescription.id)).where(Prescription.tenant_id == self.tenant_id)
        )
        return result.scalar() or 0

    async def _count_prescriptions_in_month(self) -> int:
        today = date.today()
        first_day = date(today.year, today.month, 1)
        result = await self.db.execute(
            select(func.count(Prescription.id)).where(
                and_(
                    Prescription.tenant_id == self.tenant_id,
                    func.date(Prescription.created_at) >= first_day,
                    func.date(Prescription.created_at) <= today,
                )
            )
        )
        return result.scalar() or 0

    async def _get_invoice_stats(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> dict:
        query = select(Invoice).where(Invoice.tenant_id == self.tenant_id)
        if date_from:
            query = query.where(func.date(Invoice.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(Invoice.created_at) <= date_to)

        result = await self.db.execute(query)
        invoices = result.scalars().all()

        total = len(invoices)
        paid = sum(1 for i in invoices if i.status == "paid")
        overdue = sum(
            1 for i in invoices if i.status != "paid" and i.due_date < date.today()
        )

        overdue_amount = 0.0
        for invoice in invoices:
            if invoice.status != "paid" and invoice.due_date < date.today():
                payment_result = await self.db.execute(
                    select(Payment.amount).where(Payment.id == invoice.payment_id)
                )
                payment_amount = payment_result.scalar()
                if payment_amount:
                    overdue_amount += float(payment_amount)

        return {
            "total": total,
            "paid": paid,
            "overdue": overdue,
            "overdue_amount": overdue_amount,
        }

    async def _get_daily_revenue_trend(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TrendData]:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        query = (
            select(
                func.date(Payment.payment_date).label("trend_date"),
                func.sum(Payment.amount).label("value"),
            )
            .where(
                and_(
                    Payment.tenant_id == self.tenant_id,
                    Payment.status == "paid",
                    Payment.payment_date >= date_from,
                    Payment.payment_date <= date_to,
                )
            )
            .group_by(func.date(Payment.payment_date))
            .order_by(func.date(Payment.payment_date))
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TrendData(trend_date=row.trend_date, value=float(row.value or 0.0)) for row in rows]

    async def _get_patient_demographics(self) -> PatientDemographics:
        result = await self.db.execute(
            select(Patient.gender, func.count(Patient.id))
            .where(Patient.tenant_id == self.tenant_id)
            .group_by(Patient.gender)
        )
        rows = result.all()

        demographics = {"male": 0, "female": 0, "other": 0}
        for gender, count in rows:
            if gender in demographics:
                demographics[gender] = count
            else:
                demographics["other"] += count

        return PatientDemographics(**demographics)

    async def _get_age_distribution(self) -> AgeGroupDistribution:
        today = date.today()
        result = await self.db.execute(
            select(Patient.date_of_birth).where(Patient.tenant_id == self.tenant_id)
        )
        birthdates = [row[0] for row in result.all() if row[0]]

        distribution = {
            "age_0_18": 0,
            "age_19_35": 0,
            "age_36_50": 0,
            "age_51_65": 0,
            "age_66_plus": 0,
        }

        for birthdate in birthdates:
            age = (today - birthdate).days // 365
            if age <= 18:
                distribution["age_0_18"] += 1
            elif age <= 35:
                distribution["age_19_35"] += 1
            elif age <= 50:
                distribution["age_36_50"] += 1
            elif age <= 65:
                distribution["age_51_65"] += 1
            else:
                distribution["age_66_plus"] += 1

        return AgeGroupDistribution(**distribution)

    async def _get_top_diagnoses(self, limit: int = 10) -> list[TopDiagnosis]:
        result = await self.db.execute(
            select(PatientDiagnosis.description, func.count(PatientDiagnosis.id))
            .where(PatientDiagnosis.tenant_id == self.tenant_id)
            .group_by(PatientDiagnosis.description)
            .order_by(func.count(PatientDiagnosis.id).desc())
            .limit(limit)
        )
        rows = result.all()
        return [TopDiagnosis(diagnosis=diag, count=count) for diag, count in rows]

    async def _get_patient_growth_trend(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TrendData]:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=90)

        query = (
            select(
                func.date(Patient.created_at).label("trend_date"),
                func.count(Patient.id).label("value"),
            )
            .where(
                and_(
                    Patient.tenant_id == self.tenant_id,
                    func.date(Patient.created_at) >= date_from,
                    func.date(Patient.created_at) <= date_to,
                )
            )
            .group_by(func.date(Patient.created_at))
            .order_by(func.date(Patient.created_at))
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TrendData(trend_date=row.trend_date, value=float(row.value or 0)) for row in rows]

    async def _get_appointment_booking_trend(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TrendData]:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        query = (
            select(
                func.date(Appointment.appointment_date).label("trend_date"),
                func.count(Appointment.id).label("value"),
            )
            .where(
                and_(
                    Appointment.tenant_id == self.tenant_id,
                    func.date(Appointment.appointment_date) >= date_from,
                    func.date(Appointment.appointment_date) <= date_to,
                )
            )
            .group_by(func.date(Appointment.appointment_date))
            .order_by(func.date(Appointment.appointment_date))
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TrendData(trend_date=row.trend_date, value=float(row.value or 0)) for row in rows]

    def _calculate_peak_hours(self, appointments: list) -> list[dict]:
        hour_counts = {}
        for appointment in appointments:
            if appointment.appointment_time:
                hour = appointment.appointment_time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"hour": hour, "count": count, "label": f"{hour:02d}:00"}
            for hour, count in sorted_hours[:5]
        ]

    async def _get_top_complaints(
        self, limit: int = 10, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TopChiefComplaint]:
        query = (
            select(Visit.chief_complaint, func.count(Visit.id))
            .where(
                and_(
                    Visit.tenant_id == self.tenant_id, Visit.chief_complaint.isnot(None)
                )
            )
            .group_by(Visit.chief_complaint)
            .order_by(func.count(Visit.id).desc())
            .limit(limit)
        )

        if date_from:
            query = query.where(func.date(Visit.visit_date) >= date_from)
        if date_to:
            query = query.where(func.date(Visit.visit_date) <= date_to)

        result = await self.db.execute(query)
        rows = result.all()
        return [
            TopChiefComplaint(complaint=complaint, count=count) for complaint, count in rows
        ]

    async def _get_visit_trend(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TrendData]:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        query = (
            select(
                func.date(Visit.visit_date).label("trend_date"),
                func.count(Visit.id).label("value"),
            )
            .where(
                and_(
                    Visit.tenant_id == self.tenant_id,
                    func.date(Visit.visit_date) >= date_from,
                    func.date(Visit.visit_date) <= date_to,
                )
            )
            .group_by(func.date(Visit.visit_date))
            .order_by(func.date(Visit.visit_date))
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TrendData(trend_date=row.trend_date, value=float(row.value or 0)) for row in rows]

    async def _get_top_medicines(
        self, limit: int = 10, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TopMedicine]:
        presc_query = select(Prescription.id).where(Prescription.tenant_id == self.tenant_id)

        if date_from:
            presc_query = presc_query.where(func.date(Prescription.created_at) >= date_from)
        if date_to:
            presc_query = presc_query.where(func.date(Prescription.created_at) <= date_to)

        presc_result = await self.db.execute(presc_query)
        prescription_ids = [row[0] for row in presc_result.all()]

        if not prescription_ids:
            return []

        query = (
            select(PrescriptionItem.medicine_name, func.count(PrescriptionItem.id))
            .where(
                and_(
                    PrescriptionItem.prescription_id.in_(prescription_ids),
                    PrescriptionItem.medicine_name.isnot(None),
                )
            )
            .group_by(PrescriptionItem.medicine_name)
            .order_by(func.count(PrescriptionItem.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TopMedicine(medicine_name=name, count=count) for name, count in rows]

    async def _get_prescription_trend(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> list[TrendData]:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        query = (
            select(
                func.date(Prescription.created_at).label("trend_date"),
                func.count(Prescription.id).label("value"),
            )
            .where(
                and_(
                    Prescription.tenant_id == self.tenant_id,
                    func.date(Prescription.created_at) >= date_from,
                    func.date(Prescription.created_at) <= date_to,
                )
            )
            .group_by(func.date(Prescription.created_at))
            .order_by(func.date(Prescription.created_at))
        )

        result = await self.db.execute(query)
        rows = result.all()
        return [TrendData(trend_date=row.trend_date, value=float(row.value or 0)) for row in rows]
