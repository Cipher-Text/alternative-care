---
title: "Dashboard & Analytics API"
type: "api-reference"
module: "dashboard"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "6 endpoints for real-time clinic analytics across patients, appointments, visits, prescriptions, and finances"
endpoints: 6
authentication: "required"
---

# Dashboard & Analytics API

**Module:** Dashboard  
**Endpoints:** 6  
**Base Path:** `/api/v1/dashboard`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [Overview Stats](#overview-stats)
  - [Financial Analytics](#financial-analytics)
  - [Patient Analytics](#patient-analytics)
  - [Appointment Analytics](#appointment-analytics)
  - [Visit Analytics](#visit-analytics)
  - [Prescription Analytics](#prescription-analytics)
- [Examples](#examples)

---

## 🌐 Overview

Real-time analytics and reporting system aggregating data from all modules.

**Key Features:**
- ✅ High-level overview statistics
- ✅ Financial analytics with revenue breakdowns
- ✅ Patient demographics and trends
- ✅ Appointment booking analytics
- ✅ Visit analytics and chief complaints
- ✅ Prescription and medication trends
- ✅ Date range filtering
- ✅ Time-series trend data
- ✅ Multi-tenant isolation

**Authentication:** Required (JWT)

---

## 📡 Endpoints

### Overview Stats

```http
GET /api/v1/dashboard/overview
```

**Query Parameters:**
- `date_from` (date, optional): Start date
- `date_to` (date, optional): End date

**Response:** `200 OK`
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

**Description:** High-level overview across all clinic operations

<!-- AI: All metrics automatically scoped to tenant from JWT -->

---

### Financial Analytics

```http
GET /api/v1/dashboard/financial
```

**Query Parameters:**
- `date_from` (date, optional): Start date
- `date_to` (date, optional): End date

**Response:** `200 OK`
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
    {
      "trend_date": "2026-04-01",
      "value": 3500.0
    },
    {
      "trend_date": "2026-04-02",
      "value": 4200.0
    }
  ]
}
```

**Description:** Revenue metrics and payment breakdowns with daily trends

---

### Patient Analytics

```http
GET /api/v1/dashboard/patients
```

**Query Parameters:**
- `date_from` (date, optional): Start date for new patients filter
- `date_to` (date, optional): End date for new patients filter

**Response:** `200 OK`
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
    {
      "diagnosis": "Headache",
      "count": 35
    },
    {
      "diagnosis": "Fever",
      "count": 28
    }
  ],
  "patient_growth": [
    {
      "trend_date": "2026-04-01",
      "value": 2
    },
    {
      "trend_date": "2026-04-02",
      "value": 1
    }
  ]
}
```

**Description:** Patient demographics, age distribution, and growth trends

**Age Groups:**
- `age_0_18`: 0-18 years
- `age_19_35`: 19-35 years
- `age_36_50`: 36-50 years
- `age_51_65`: 51-65 years
- `age_66_plus`: 66+ years

---

### Appointment Analytics

```http
GET /api/v1/dashboard/appointments
```

**Query Parameters:**
- `date_from` (date, optional): Start date
- `date_to` (date, optional): End date

**Response:** `200 OK`
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
  "booking_trend": [
    {
      "trend_date": "2026-04-01",
      "value": 8
    }
  ],
  "peak_hours": [
    {
      "hour": 10,
      "count": 45,
      "label": "10:00"
    },
    {
      "hour": 14,
      "count": 38,
      "label": "14:00"
    }
  ]
}
```

**Description:** Appointment metrics, status breakdown, and peak hours

**Cancellation Rate:** Percentage of appointments cancelled/no-show

<!-- AI: peak_hours helps optimize scheduling by showing busiest times -->

---

### Visit Analytics

```http
GET /api/v1/dashboard/visits
```

**Query Parameters:**
- `date_from` (date, optional): Start date
- `date_to` (date, optional): End date

**Response:** `200 OK`
```json
{
  "total_visits": 280,
  "average_visits_per_patient": 1.87,
  "by_type": {
    "consultation": 160,
    "follow_up": 110,
    "emergency": 10
  },
  "by_status": {
    "scheduled": 15,
    "in_progress": 5,
    "completed": 260
  },
  "top_complaints": [
    {
      "complaint": "Headache",
      "count": 45
    },
    {
      "complaint": "Fever",
      "count": 38
    },
    {
      "complaint": "Cough",
      "count": 32
    }
  ],
  "visit_trend": [
    {
      "trend_date": "2026-04-01",
      "value": 6
    }
  ]
}
```

**Description:** Visit metrics, type breakdown, and top chief complaints

---

### Prescription Analytics

```http
GET /api/v1/dashboard/prescriptions
```

**Query Parameters:**
- `date_from` (date, optional): Start date
- `date_to` (date, optional): End date

**Response:** `200 OK`
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
    {
      "medicine_name": "Arnica Montana 30C",
      "count": 85
    },
    {
      "medicine_name": "Belladonna 200C",
      "count": 72
    },
    {
      "medicine_name": "Bryonia 200C",
      "count": 58
    }
  ],
  "prescription_trend": [
    {
      "trend_date": "2026-04-01",
      "value": 5
    }
  ]
}
```

**Description:** Prescription metrics, status breakdown, and most prescribed medicines

---

## 💡 Examples

### Get Overview Stats (cURL)

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/overview" \
  -H "Authorization: Bearer $TOKEN"
```

### Monthly Financial Report (Python)

```python
import requests
from datetime import date
from calendar import monthrange

year, month = 2026, 4
date_from = date(year, month, 1)
_, last_day = monthrange(year, month)
date_to = date(year, month, last_day)

response = requests.get(
    "http://localhost:8000/api/v1/dashboard/financial",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "date_from": str(date_from),
        "date_to": str(date_to)
    }
)
analytics = response.json()

print(f"Financial Report - {year}-{month:02d}")
print(f"Total Revenue: ৳{analytics['total_revenue']:,.2f}")
print(f"Cash: ৳{analytics['revenue_by_method']['cash']:,.2f}")
print(f"bKash: ৳{analytics['revenue_by_method']['bkash']:,.2f}")
print(f"Average Payment: ৳{analytics['average_payment']:.2f}")
```

### Patient Demographics (JavaScript)

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/dashboard/patients',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
)
const analytics = await response.json()

console.log('Patient Demographics:')
console.log(`Male: ${analytics.demographics.male}`)
console.log(`Female: ${analytics.demographics.female}`)
console.log(`Other: ${analytics.demographics.other}`)

console.log('\nAge Distribution:')
Object.entries(analytics.age_distribution).forEach(([group, count]) => {
  console.log(`${group}: ${count}`)
})

console.log('\nTop Diagnoses:')
analytics.top_diagnoses.slice(0, 5).forEach(diag => {
  console.log(`${diag.diagnosis}: ${diag.count} patients`)
})
```

### Appointment Peak Hours (Python)

```python
response = requests.get(
    "http://localhost:8000/api/v1/dashboard/appointments",
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()

print("Peak Appointment Hours:")
for peak in data['peak_hours'][:5]:
    print(f"{peak['label']}: {peak['count']} appointments")
```

### Top Prescribed Medicines (Python)

```python
response = requests.get(
    "http://localhost:8000/api/v1/dashboard/prescriptions",
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()

print("Top 10 Prescribed Medicines:")
for i, med in enumerate(data['top_medicines'][:10], 1):
    print(f"{i}. {med['medicine_name']}: {med['count']} times")
```

---

## 📊 Performance Considerations

**Efficient Queries:**
- Uses database aggregation (COUNT, SUM, GROUP BY)
- Selective loading of required data only
- Date filtering reduces query scope

**Caching Recommendations:**
- Consider Redis caching for high-traffic dashboards
- Cache TTL: 5-15 minutes
- Cache key: `dashboard:{tenant_id}:{endpoint}:{date_from}:{date_to}`

**Real-Time Stats:**
- All metrics calculated in real-time from live data
- No pre-aggregation or stale data
- Instant updates when underlying data changes

---

## 🤖 AI Quick Reference

**Q: How do I get clinic overview stats?**
→ GET /dashboard/overview (includes patients, appointments, revenue)

**Q: How do I filter analytics by date range?**
→ Add date_from and date_to query parameters

**Q: What's the difference between total_revenue and paid_amount?**
→ total_revenue includes pending payments, paid_amount is confirmed only

**Q: How are age groups calculated?**
→ Based on current age from date_of_birth (0-18, 19-35, 36-50, 51-65, 66+)

**Q: Are analytics tenant-scoped?**
→ Yes, automatically filtered by tenant_id from JWT

**Q: How do I get peak appointment hours?**
→ GET /dashboard/appointments returns peak_hours array

**Q: What are trend data formats?**
→ Array of {trend_date: "YYYY-MM-DD", value: number} objects

---

**See Also:**
- [Patients API](patients.md) - Patient data source
- [Appointments API](appointments.md) - Appointment data source
- [Payments API](payments.md) - Financial data source
- [Prescriptions API](prescriptions.md) - Prescription data source

---

**Last Updated:** May 1, 2026  
**Endpoints:** 6 ✅
