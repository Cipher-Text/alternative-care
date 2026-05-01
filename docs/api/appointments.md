---
title: "Appointments & Visits API"
type: "api-reference"
module: "appointments"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "10 endpoints for appointment scheduling, visit management, and reminders"
endpoints: 10
authentication: "required"
---

# Appointments & Visits API

**Module:** Appointments  
**Endpoints:** 10  
**Base Path:** `/api/v1/appointments`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [Create Appointment](#create-appointment)
  - [List Appointments](#list-appointments)
  - [Get Appointment](#get-appointment)
  - [Update Appointment](#update-appointment)
  - [Cancel Appointment](#cancel-appointment)
  - [Delete Appointment](#delete-appointment)
  - [Create Visit](#create-visit)
  - [List Visits](#list-visits)
  - [Get Visit](#get-visit)
  - [Update Visit](#update-visit)
- [Business Logic](#business-logic)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## 🌐 Overview

Appointment scheduling and visit management with conflict detection and automatic status updates.

**Key Features:**
- ✅ Appointment CRUD operations
- ✅ Time slot conflict detection
- ✅ Multiple statuses: scheduled, confirmed, in_progress, completed, cancelled, no_show
- ✅ Visit records with clinical data
- ✅ Automatic appointment-visit linking
- ✅ Reminder system support
- ✅ Multi-tenant isolation

**Authentication:** Required (JWT)

---

## 📡 Endpoints

### Create Appointment

```http
POST /api/v1/appointments
```

**Request Body:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_date": "2026-05-01",
  "appointment_time": "10:00:00",
  "duration_minutes": 30,
  "reason": "Routine checkup",
  "notes": "First visit"
}
```

**Required Fields:**
- `patient_id` (uuid)
- `doctor_id` (uuid)
- `appointment_date` (date)
- `appointment_time` (time)
- `duration_minutes` (int, default: 30)

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_date": "2026-05-01",
  "appointment_time": "10:00:00",
  "duration_minutes": 30,
  "status": "scheduled",
  "reason": "Routine checkup",
  "notes": "First visit",
  "reminder_sent": false,
  "created_at": "2026-05-01T09:00:00Z",
  "updated_at": "2026-05-01T09:00:00Z"
}
```

**Errors:**
- `400 Bad Request`: Validation error
- `409 Conflict`: Time slot already booked

<!-- AI: Service layer automatically validates doctor availability -->

---

### List Appointments

```http
GET /api/v1/appointments
```

**Query Parameters:**
- `appointment_date` (date, optional): Filter by date
- `status` (string, optional): Filter by status
- `patient_id` (uuid, optional): Filter by patient
- `doctor_id` (uuid, optional): Filter by doctor
- `skip` (int, optional): Offset for pagination (default: 0)
- `limit` (int, optional): Max results (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "appointment_date": "2026-05-01",
    "appointment_time": "10:00:00",
    "status": "scheduled",
    ...
  }
]
```

---

### Get Appointment

```http
GET /api/v1/appointments/{id}
```

**Path Parameters:**
- `id` (uuid, required): Appointment ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "appointment_date": "2026-05-01",
  "status": "scheduled",
  ...
}
```

**Errors:**
- `404 Not Found`: Appointment doesn't exist

---

### Update Appointment

```http
PATCH /api/v1/appointments/{id}
```

**Path Parameters:**
- `id` (uuid, required): Appointment ID

**Request Body:** (partial update supported)
```json
{
  "appointment_date": "2026-05-02",
  "appointment_time": "14:00:00",
  "status": "confirmed",
  "notes": "Updated notes"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Appointment doesn't exist
- `409 Conflict`: New time slot conflicts with existing appointment

<!-- AI: Conflict detection automatically excludes current appointment -->

---

### Cancel Appointment

```http
POST /api/v1/appointments/{id}/cancel
```

**Path Parameters:**
- `id` (uuid, required): Appointment ID

**Request Body:**
```json
{
  "cancellation_reason": "Patient requested rescheduling"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "cancelled",
  "cancellation_reason": "Patient requested rescheduling",
  ...
}
```

**Errors:**
- `404 Not Found`: Appointment doesn't exist

---

### Delete Appointment

```http
DELETE /api/v1/appointments/{id}
```

**Path Parameters:**
- `id` (uuid, required): Appointment ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Appointment doesn't exist

<!-- AI: This is a hard delete, use cancel for soft delete -->

---

### Create Visit

```http
POST /api/v1/appointments/visits
```

**Request Body:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "visit_date": "2026-05-01",
  "visit_type": "consultation",
  "appointment_id": "uuid",
  "chief_complaint": "Headache",
  "history_of_present_illness": "Started 3 days ago",
  "examination_findings": "Normal vitals",
  "temperature": "98.6°F",
  "blood_pressure": "120/80",
  "pulse": "72 bpm",
  "weight": "70 kg",
  "provisional_diagnosis": "Tension headache",
  "treatment_plan": "Rest, hydration, follow up in 1 week",
  "follow_up_date": "2026-05-08",
  "status": "completed"
}
```

**Required Fields:**
- `patient_id` (uuid)
- `doctor_id` (uuid)
- `visit_date` (date)
- `visit_type` (enum: consultation|follow_up|emergency)

**Optional:**
- `appointment_id` (uuid): Links visit to appointment

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "visit_type": "consultation",
  "status": "completed",
  ...
}
```

**Errors:**
- `400 Bad Request`: Validation error

<!-- AI: When appointment_id is provided, linked appointment status changes to "in_progress" -->

---

### List Visits

```http
GET /api/v1/appointments/visits
```

**Query Parameters:**
- `patient_id` (uuid, optional): Filter by patient
- `doctor_id` (uuid, optional): Filter by doctor
- `visit_type` (string, optional): Filter by type
- `status` (string, optional): Filter by status
- `skip` (int, optional): Offset (default: 0)
- `limit` (int, optional): Max results (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "visit_date": "2026-05-01",
    "visit_type": "consultation",
    "status": "completed",
    ...
  }
]
```

---

### Get Visit

```http
GET /api/v1/appointments/visits/{id}
```

**Path Parameters:**
- `id` (uuid, required): Visit ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "chief_complaint": "Headache",
  "provisional_diagnosis": "Tension headache",
  ...
}
```

**Errors:**
- `404 Not Found`: Visit doesn't exist

---

### Update Visit

```http
PATCH /api/v1/appointments/visits/{id}
```

**Path Parameters:**
- `id` (uuid, required): Visit ID

**Request Body:** (partial update supported)
```json
{
  "treatment_plan": "Updated treatment plan",
  "follow_up_date": "2026-05-15",
  "status": "completed"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Visit doesn't exist

<!-- AI: When visit status changes to "completed", linked appointment is also completed -->

---

## 🔄 Business Logic

### Time Slot Validation

The service layer automatically validates:
- Doctor is not double-booked
- Time slots don't overlap with existing appointments
- Only active appointments (scheduled/confirmed/in_progress) are considered
- When updating, current appointment is excluded from conflict checks

**Example:**
```
Appointment 1: 10:00 - 10:30 (scheduled)
Appointment 2: 10:15 - 10:45 (trying to create)
Result: 409 Conflict - overlaps with Appointment 1
```

### Appointment-Visit Linking

**When visit is created with `appointment_id`:**
- Linked appointment status changes to "in_progress"

**When visit is marked as "completed":**
- Linked appointment is also marked as "completed"

**Walk-in visits:**
- Create visit without `appointment_id` (set to null)
- No appointment record created

### Appointment Statuses

- `scheduled`: Default status when created
- `confirmed`: Patient confirmed attendance
- `in_progress`: Visit started (auto-set when visit created)
- `completed`: Visit finished (auto-set when visit completed)
- `cancelled`: Cancelled with reason
- `no_show`: Patient didn't show up

### Reminder System

Query appointments needing reminders:
```python
# Get appointments 24 hours before
appointments = await service.list_appointments(
    appointment_date=tomorrow,
    reminder_sent=False
)
# Send reminders via SMS/Email (integration framework)
# Mark as sent
```

---

## 💡 Examples

### Create Appointment (cURL)

```bash
curl -X POST http://localhost:8000/api/v1/appointments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "doctor_id": "650e8400-e29b-41d4-a716-446655440000",
    "appointment_date": "2026-05-01",
    "appointment_time": "10:00:00",
    "duration_minutes": 30,
    "reason": "Routine checkup"
  }'
```

### List Today's Appointments (Python)

```python
import requests
from datetime import date

response = requests.get(
    "http://localhost:8000/api/v1/appointments",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "appointment_date": str(date.today()),
        "status": "scheduled"
    }
)
appointments = response.json()
```

### Create Walk-in Visit (JavaScript)

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/appointments/visits',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      patient_id: 'uuid',
      doctor_id: 'uuid',
      visit_date: '2026-05-01',
      visit_type: 'consultation',
      // No appointment_id = walk-in
      chief_complaint: 'Fever',
      provisional_diagnosis: 'Viral fever'
    })
  }
)
const visit = await response.json()
```

### Cancel Appointment (Python)

```python
response = requests.post(
    f"http://localhost:8000/api/v1/appointments/{appointment_id}/cancel",
    headers={"Authorization": f"Bearer {token}"},
    json={"cancellation_reason": "Patient requested rescheduling"}
)
```

---

## ❌ Error Handling

### Conflict Error (409)

```json
{
  "detail": "Time slot conflict: Doctor already has an appointment at this time"
}
```

### Validation Error (400)

```json
{
  "detail": [
    {
      "loc": ["body", "appointment_time"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Not Found (404)

```json
{
  "detail": "Appointment not found"
}
```

---

## 🤖 AI Quick Reference

**Q: How do I prevent double-booking?**
→ Service layer automatically validates time slots on create/update

**Q: What's the difference between appointment and visit?**
→ Appointment = scheduled future event, Visit = actual clinical encounter

**Q: Can I create a visit without an appointment?**
→ Yes, set appointment_id to null for walk-in patients

**Q: How do I mark a patient as no-show?**
→ PATCH /appointments/{id} with {"status": "no_show"}

**Q: Are appointments tenant-scoped?**
→ Yes, automatically filtered by tenant_id from JWT

**Q: How do I send appointment reminders?**
→ Query appointments by date with reminder_sent=false, then use integration framework

---

**See Also:**
- [Patients API](patients.md) - Patient records
- [Prescriptions API](prescriptions.md) - Issue prescriptions during visit
- [Authentication](authentication.md) - Get JWT token

---

**Last Updated:** May 1, 2026  
**Endpoints:** 10 ✅
