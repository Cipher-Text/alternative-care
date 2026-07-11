"""Dashboard and analytics API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.dashboard.service import DashboardService
from app.shared.schemas import (
    OverviewStats,
    FinancialAnalytics,
    PatientAnalytics,
    AppointmentAnalytics,
    VisitAnalytics,
    PrescriptionAnalytics,
)

router = APIRouter()


def get_dashboard_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> DashboardService:
    """Dependency for dashboard service with tenant context."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform users cannot access tenant dashboard. Use a tenant account.",
        )
    return DashboardService(db=db, tenant_id=current_user.tenant_id)


# ===== Dashboard Endpoints =====


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date for stats"),
    date_to: date | None = Query(None, description="End date for stats"),
):
    """
    Get high-level overview statistics.

    - Patient stats (total, new, active)
    - Appointment stats (total, upcoming, today)
    - Visit stats (total, this month)
    - Financial stats (revenue, pending)
    - Prescription stats (total, this month)
    - Defaults to last 30 days
    """
    return await service.get_overview(date_from=date_from, date_to=date_to)


@router.get("/financial", response_model=FinancialAnalytics)
async def get_financial_analytics(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date"),
    date_to: date | None = Query(None, description="End date"),
):
    """
    Get financial analytics and revenue metrics.

    - Total revenue and payments
    - Revenue by status (paid, pending, refunded)
    - Revenue by method (cash, bKash)
    - Invoice metrics (total, paid, overdue)
    - Daily revenue trend
    - Supports date range filtering
    """
    return await service.get_financial_analytics(date_from=date_from, date_to=date_to)


@router.get("/patients", response_model=PatientAnalytics)
async def get_patient_analytics(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date for new patients"),
    date_to: date | None = Query(None, description="End date for new patients"),
):
    """
    Get patient analytics and demographics.

    - Total, new, and active patients
    - Gender distribution
    - Age group distribution
    - Top diagnoses
    - Patient growth trend
    - Date filter applies to new patients
    """
    return await service.get_patient_analytics(date_from=date_from, date_to=date_to)


@router.get("/appointments", response_model=AppointmentAnalytics)
async def get_appointment_analytics(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date"),
    date_to: date | None = Query(None, description="End date"),
):
    """
    Get appointment analytics and booking metrics.

    - Total, upcoming, and completed appointments
    - Cancellation rate
    - Appointments by status (scheduled, confirmed, completed, cancelled, no-show)
    - Appointments by type (consultation, follow-up, emergency)
    - Booking trend
    - Peak appointment hours
    - Supports date range filtering
    """
    return await service.get_appointment_analytics(date_from=date_from, date_to=date_to)


@router.get("/visits", response_model=VisitAnalytics)
async def get_visit_analytics(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date"),
    date_to: date | None = Query(None, description="End date"),
):
    """
    Get visit analytics and patient encounter metrics.

    - Total visits
    - Average visits per patient
    - Visits by type (consultation, follow-up, emergency)
    - Top chief complaints
    - Daily visit trend
    - Supports date range filtering
    """
    return await service.get_visit_analytics(date_from=date_from, date_to=date_to)


@router.get("/prescriptions", response_model=PrescriptionAnalytics)
async def get_prescription_analytics(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    date_from: date | None = Query(None, description="Start date"),
    date_to: date | None = Query(None, description="End date"),
):
    """
    Get prescription analytics and medication metrics.

    - Total prescriptions and items
    - Average items per prescription
    - Prescriptions by status (draft, issued, voided)
    - Top prescribed medicines
    - Daily prescription trend
    - Supports date range filtering
    """
    return await service.get_prescription_analytics(date_from=date_from, date_to=date_to)
