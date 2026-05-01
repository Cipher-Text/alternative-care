"""Dashboard and analytics schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===== Base Analytics Schemas =====


class DateRangeFilter(BaseModel):
    """Date range filter for analytics queries."""

    date_from: Optional[date] = Field(None, description="Start date for analytics")
    date_to: Optional[date] = Field(None, description="End date for analytics")


class TrendData(BaseModel):
    """Single data point in a trend series."""

    trend_date: date = Field(..., description="Date of the data point", alias="date")
    value: float = Field(..., description="Value at this date")
    label: Optional[str] = Field(None, description="Human-readable label")

    class Config:
        populate_by_name = True


# ===== Overview Dashboard =====


class OverviewStats(BaseModel):
    """High-level overview statistics for dashboard."""

    # Patient stats
    total_patients: int = Field(..., description="Total number of patients")
    new_patients_this_month: int = Field(..., description="New patients this month")
    active_patients: int = Field(..., description="Active patients (visited in last 30 days)")

    # Appointment stats
    total_appointments: int = Field(..., description="Total appointments")
    upcoming_appointments: int = Field(..., description="Upcoming scheduled appointments")
    appointments_today: int = Field(..., description="Appointments scheduled for today")

    # Visit stats
    total_visits: int = Field(..., description="Total completed visits")
    visits_this_month: int = Field(..., description="Visits this month")

    # Financial stats
    total_revenue: float = Field(..., description="Total revenue (all time)")
    revenue_this_month: float = Field(..., description="Revenue this month")
    pending_payments: float = Field(..., description="Total pending payment amount")

    # Prescription stats
    total_prescriptions: int = Field(..., description="Total prescriptions issued")
    prescriptions_this_month: int = Field(..., description="Prescriptions this month")

    # Period info
    period_start: Optional[date] = Field(None, description="Start of reporting period")
    period_end: Optional[date] = Field(None, description="End of reporting period")

    class Config:
        from_attributes = True


# ===== Financial Analytics =====


class RevenueByMethod(BaseModel):
    """Revenue breakdown by payment method."""

    cash: float = Field(..., description="Revenue from cash payments")
    bkash: float = Field(..., description="Revenue from bKash payments")
    other: float = Field(0.0, description="Revenue from other methods")


class FinancialAnalytics(BaseModel):
    """Financial analytics and revenue metrics."""

    # Total metrics
    total_revenue: float = Field(..., description="Total revenue in period")
    total_payments: int = Field(..., description="Total number of payments")
    average_payment: float = Field(..., description="Average payment amount")

    # Status breakdown
    paid_amount: float = Field(..., description="Amount from paid payments")
    pending_amount: float = Field(..., description="Amount from pending payments")
    refunded_amount: float = Field(0.0, description="Amount refunded")

    # Method breakdown
    revenue_by_method: RevenueByMethod = Field(..., description="Revenue by payment method")

    # Invoice metrics
    total_invoices: int = Field(..., description="Total invoices")
    paid_invoices: int = Field(..., description="Paid invoices")
    overdue_invoices: int = Field(..., description="Overdue invoices")
    overdue_amount: float = Field(..., description="Total overdue amount")

    # Trends
    daily_revenue: list[TrendData] = Field(
        default_factory=list, description="Daily revenue trend"
    )

    # Period
    period_start: Optional[date] = Field(None, description="Start date")
    period_end: Optional[date] = Field(None, description="End date")

    class Config:
        from_attributes = True


# ===== Patient Analytics =====


class PatientDemographics(BaseModel):
    """Patient demographics breakdown."""

    male: int = Field(..., description="Number of male patients")
    female: int = Field(..., description="Number of female patients")
    other: int = Field(0, description="Number of other/unspecified gender patients")


class AgeGroupDistribution(BaseModel):
    """Patient distribution by age group."""

    age_0_18: int = Field(0, description="Patients aged 0-18")
    age_19_35: int = Field(0, description="Patients aged 19-35")
    age_36_50: int = Field(0, description="Patients aged 36-50")
    age_51_65: int = Field(0, description="Patients aged 51-65")
    age_66_plus: int = Field(0, description="Patients aged 66+")


class TopDiagnosis(BaseModel):
    """Common diagnosis with count."""

    diagnosis: str = Field(..., description="Diagnosis name")
    count: int = Field(..., description="Number of patients")


class PatientAnalytics(BaseModel):
    """Patient analytics and demographics."""

    # Total metrics
    total_patients: int = Field(..., description="Total patients")
    new_patients: int = Field(..., description="New patients in period")
    active_patients: int = Field(..., description="Active patients (visited recently)")

    # Demographics
    demographics: PatientDemographics = Field(..., description="Gender distribution")
    age_distribution: AgeGroupDistribution = Field(..., description="Age group distribution")

    # Top diagnoses
    top_diagnoses: list[TopDiagnosis] = Field(
        default_factory=list, description="Most common diagnoses"
    )

    # Trends
    patient_growth: list[TrendData] = Field(
        default_factory=list, description="Patient growth over time"
    )

    # Period
    period_start: Optional[date] = Field(None, description="Start date")
    period_end: Optional[date] = Field(None, description="End date")

    class Config:
        from_attributes = True


# ===== Appointment Analytics =====


class AppointmentByStatus(BaseModel):
    """Appointment count by status."""

    scheduled: int = Field(0, description="Scheduled appointments")
    confirmed: int = Field(0, description="Confirmed appointments")
    completed: int = Field(0, description="Completed appointments")
    cancelled: int = Field(0, description="Cancelled appointments")
    no_show: int = Field(0, description="No-show appointments")


class AppointmentByType(BaseModel):
    """Appointment count by type."""

    consultation: int = Field(0, description="Consultation appointments")
    follow_up: int = Field(0, description="Follow-up appointments")
    emergency: int = Field(0, description="Emergency appointments")


class AppointmentAnalytics(BaseModel):
    """Appointment analytics and booking metrics."""

    # Total metrics
    total_appointments: int = Field(..., description="Total appointments")
    upcoming_appointments: int = Field(..., description="Upcoming appointments")
    completed_appointments: int = Field(..., description="Completed appointments")
    cancellation_rate: float = Field(..., description="Cancellation rate (percentage)")

    # Status breakdown
    by_status: AppointmentByStatus = Field(..., description="Appointments by status")

    # Type breakdown
    by_type: AppointmentByType = Field(..., description="Appointments by type")

    # Trends
    booking_trend: list[TrendData] = Field(
        default_factory=list, description="Daily booking trend"
    )

    # Peak hours (hour of day with most appointments)
    peak_hours: list[dict] = Field(
        default_factory=list, description="Peak appointment hours"
    )

    # Period
    period_start: Optional[date] = Field(None, description="Start date")
    period_end: Optional[date] = Field(None, description="End date")

    class Config:
        from_attributes = True


# ===== Visit Analytics =====


class VisitByType(BaseModel):
    """Visit count by type."""

    consultation: int = Field(0, description="Consultation visits")
    follow_up: int = Field(0, description="Follow-up visits")
    emergency: int = Field(0, description="Emergency visits")


class TopChiefComplaint(BaseModel):
    """Common chief complaint with count."""

    complaint: str = Field(..., description="Chief complaint")
    count: int = Field(..., description="Number of visits")


class VisitAnalytics(BaseModel):
    """Visit analytics and patient encounter metrics."""

    # Total metrics
    total_visits: int = Field(..., description="Total visits")
    average_visits_per_patient: float = Field(..., description="Average visits per patient")

    # Type breakdown
    by_type: VisitByType = Field(..., description="Visits by type")

    # Top complaints
    top_complaints: list[TopChiefComplaint] = Field(
        default_factory=list, description="Most common chief complaints"
    )

    # Trends
    visit_trend: list[TrendData] = Field(
        default_factory=list, description="Daily visit trend"
    )

    # Period
    period_start: Optional[date] = Field(None, description="Start date")
    period_end: Optional[date] = Field(None, description="End date")

    class Config:
        from_attributes = True


# ===== Prescription Analytics =====


class TopMedicine(BaseModel):
    """Top prescribed medicine."""

    medicine_name: str = Field(..., description="Medicine name")
    count: int = Field(..., description="Times prescribed")


class PrescriptionByStatus(BaseModel):
    """Prescription count by status."""

    draft: int = Field(0, description="Draft prescriptions")
    issued: int = Field(0, description="Issued prescriptions")
    voided: int = Field(0, description="Voided prescriptions")


class PrescriptionAnalytics(BaseModel):
    """Prescription analytics and medication metrics."""

    # Total metrics
    total_prescriptions: int = Field(..., description="Total prescriptions")
    total_items: int = Field(..., description="Total prescription items")
    average_items_per_prescription: float = Field(
        ..., description="Average items per prescription"
    )

    # Status breakdown
    by_status: PrescriptionByStatus = Field(..., description="Prescriptions by status")

    # Top medicines
    top_medicines: list[TopMedicine] = Field(
        default_factory=list, description="Most prescribed medicines"
    )

    # Trends
    prescription_trend: list[TrendData] = Field(
        default_factory=list, description="Daily prescription trend"
    )

    # Period
    period_start: Optional[date] = Field(None, description="Start date")
    period_end: Optional[date] = Field(None, description="End date")

    class Config:
        from_attributes = True
