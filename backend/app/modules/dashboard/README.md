# Dashboard & Analytics Module

Comprehensive analytics and reporting system for the AltCare platform, providing real-time insights across all clinic operations.

## Overview

The dashboard module aggregates data from all modules (patients, appointments, visits, prescriptions, payments) to provide:
- High-level overview statistics
- Financial analytics with revenue breakdowns
- Patient demographics and trends
- Appointment booking analytics
- Visit analytics and chief complaints
- Prescription and medication trends

All analytics automatically scope to the authenticated user's tenant and support date range filtering.

## API Endpoints

### GET /api/v1/dashboard/overview

High-level overview statistics across all modules.

**Response:**
```json
{
  "total_patients": 150,
  "new_patients_this_month": 12,
  "active_patients": 45,
  "total_appointments": 320,
  "upcoming_appointments": 28,
  "appointments_today": 5,
  "total_visits": 280,
  "visits_this_month": 42,
  "total_revenue": 125000.0,
  "revenue_this_month": 18500.0,
  "pending_payments": 2500.0,
  "total_prescriptions": 265,
  "prescriptions_this_month": 38,
  "period_start": "2026-04-01",
  "period_end": "2026-05-01"
}
```

### GET /api/v1/dashboard/financial

Financial analytics and revenue metrics.

**Query Parameters:**
- `date_from` (optional): Start date (YYYY-MM-DD)
- `date_to` (optional): End date (YYYY-MM-DD)

**Response:**
```json
{
  "total_revenue": 125000.0,
  "total_payments": 85,
  "average_payment": 1470.59,
  "paid_amount": 120000.0,
  "pending_amount": 5000.0,
  "refunded_amount": 0.0,
  "revenue_by_method": {
    "cash": 80000.0,
    "bkash": 40000.0,
    "other": 0.0
  },
  "total_invoices": 85,
  "paid_invoices": 80,
  "overdue_invoices": 3,
  "overdue_amount": 4500.0,
  "daily_revenue": [
    {"trend_date": "2026-04-01", "value": 3500.0},
    {"trend_date": "2026-04-02", "value": 4200.0}
  ]
}
```

### GET /api/v1/dashboard/patients

Patient analytics and demographics.

**Query Parameters:**
- `date_from` (optional): Start date for new patients filter
- `date_to` (optional): End date for new patients filter

**Response:**
```json
{
  "total_patients": 150,
  "new_patients": 12,
  "active_patients": 45,
  "demographics": {
    "male": 75,
    "female": 72,
    "other": 3
  },
  "age_distribution": {
    "age_0_18": 20,
    "age_19_35": 45,
    "age_36_50": 50,
    "age_51_65": 25,
    "age_66_plus": 10
  },
  "top_diagnoses": [
    {"diagnosis": "Headache", "count": 35},
    {"diagnosis": "Fever", "count": 28}
  ],
  "patient_growth": [
    {"trend_date": "2026-04-01", "value": 2},
    {"trend_date": "2026-04-02", "value": 1}
  ]
}
```

### GET /api/v1/dashboard/appointments

Appointment analytics and booking metrics.

**Response:**
```json
{
  "total_appointments": 320,
  "upcoming_appointments": 28,
  "completed_appointments": 265,
  "cancellation_rate": 8.4,
  "by_status": {
    "scheduled": 20,
    "confirmed": 8,
    "completed": 265,
    "cancelled": 27,
    "no_show": 0
  },
  "by_type": {
    "consultation": 180,
    "follow_up": 130,
    "emergency": 10
  },
  "booking_trend": [...],
  "peak_hours": [
    {"hour": 10, "count": 45, "label": "10:00"},
    {"hour": 14, "count": 38, "label": "14:00"}
  ]
}
```

### GET /api/v1/dashboard/visits

Visit analytics and encounter metrics.

**Response:**
```json
{
  "total_visits": 280,
  "average_visits_per_patient": 1.87,
  "by_type": {
    "consultation": 160,
    "follow_up": 110,
    "emergency": 10
  },
  "top_complaints": [
    {"complaint": "Headache", "count": 45},
    {"complaint": "Fever", "count": 38}
  ],
  "visit_trend": [...]
}
```

### GET /api/v1/dashboard/prescriptions

Prescription and medication analytics.

**Response:**
```json
{
  "total_prescriptions": 265,
  "total_items": 892,
  "average_items_per_prescription": 3.37,
  "by_status": {
    "draft": 5,
    "issued": 250,
    "voided": 10
  },
  "top_medicines": [
    {"medicine_name": "Arnica Montana 30C", "count": 85},
    {"medicine_name": "Belladonna 200C", "count": 72}
  ],
  "prescription_trend": [...]
}
```

## Usage Examples

### Basic Overview
```python
import httpx

async def get_clinic_overview(jwt_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        stats = response.json()
        print(f"Total Patients: {stats['total_patients']}")
        print(f"Revenue This Month: {stats['revenue_this_month']} BDT")
```

### Financial Report with Date Range
```python
from datetime import date

async def monthly_financial_report(jwt_token: str, year: int, month: int):
    from calendar import monthrange
    
    date_from = date(year, month, 1)
    _, last_day = monthrange(year, month)
    date_to = date(year, month, last_day)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/dashboard/financial",
            params={"date_from": date_from, "date_to": date_to},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        analytics = response.json()
        
        print(f"Financial Report - {year}-{month:02d}")
        print(f"Total Revenue: {analytics['total_revenue']} BDT")
        print(f"Cash: {analytics['revenue_by_method']['cash']} BDT")
        print(f"bKash: {analytics['revenue_by_method']['bkash']} BDT")
        print(f"Average Payment: {analytics['average_payment']:.2f} BDT")
```

### Patient Demographics
```python
async def analyze_patient_base(jwt_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/dashboard/patients",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        analytics = response.json()
        
        print("Patient Demographics:")
        print(f"Male: {analytics['demographics']['male']}")
        print(f"Female: {analytics['demographics']['female']}")
        
        print("\nAge Distribution:")
        for age_group, count in analytics['age_distribution'].items():
            print(f"{age_group}: {count}")
        
        print("\nTop Diagnoses:")
        for diag in analytics['top_diagnoses'][:5]:
            print(f"{diag['diagnosis']}: {diag['count']} patients")
```

## Features

### Multi-Tenant Isolation
All analytics queries automatically scope to the authenticated user's tenant - no cross-tenant data leakage possible.

### Date Range Filtering
Most endpoints support `date_from` and `date_to` query parameters for flexible time-based analysis.

### Trend Data
Financial, patient, appointment, visit, and prescription endpoints include time-series trend data for visualization.

### Peak Hour Analysis
Appointment analytics include peak hour detection to optimize scheduling.

### Real-Time Stats
All metrics are calculated in real-time from live data - no pre-aggregation or caching.

## Security

- **Authentication Required**: All endpoints require valid JWT token
- **Tenant Scoping**: Automatic filtering by tenant_id from JWT
- **Role-Based Access**: Currently requires authenticated user (doctor/receptionist)
- **No Data Leakage**: Impossible to access other tenants' analytics

## Performance Considerations

- **Efficient Queries**: Uses database aggregation functions (COUNT, SUM, GROUP BY)
- **Selective Loading**: Only loads data needed for requested analytics
- **Date Filtering**: Apply date filters to reduce query scope
- **Consider Caching**: For high-traffic dashboards, consider caching with 5-15 minute TTL

## Testing

```bash
# Run unit tests
pytest tests/unit/test_dashboard_service.py -v

# Run integration tests
pytest tests/integration/test_dashboard_routes.py -v

# Run all dashboard tests
pytest tests/ -k dashboard -v
```

## Future Enhancements

- **Export to PDF/Excel**: Download analytics reports
- **Custom Date Ranges**: Preset options (this week, last month, this quarter)
- **Comparison Mode**: Compare current period vs previous period
- **Alerts & Notifications**: Auto-alert on anomalies (revenue drop, high cancellation rate)
- **Custom Dashboards**: User-configurable widget layouts
- **Data Caching**: Redis caching for frequently accessed analytics
- **Forecasting**: Revenue and patient growth predictions

## Architecture

```
dashboard/
├── routes.py           # 6 API endpoints
├── service.py          # Analytics business logic (700+ lines)
└── README.md           # This file

Data Flow:
Request → Route → Service → Database → Aggregation → Response Schema → JSON
```

All analytics leverage SQLAlchemy's async query capabilities and Python's list comprehensions for efficient in-memory aggregation.

---

**Documentation**: See `/docs` for OpenAPI spec  
**Module Owner**: Backend Team  
**Last Updated**: 2026-05-01
