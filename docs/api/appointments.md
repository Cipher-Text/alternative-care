---
title: "Appointments & Visits API"
type: "api-reference"
module: "appointments"
version: "1.0.0"
last_updated: "2026-05-08"
ai_summary: "10 endpoints total: 6 appointment endpoints + 4 visit endpoints"
endpoints: 10
authentication: "required"
---

# Appointments & Visits API

**Module:** Appointments  
**Endpoints:** 10 total (6 appointments + 4 visits)  
**Base Path:** `/api/v1/appointments`

## Overview

This module exposes two grouped routers:
- Appointment routes under `/api/v1/appointments`
- Visit routes under `/api/v1/appointments/visits`

## Appointment Endpoints (6)

1. `POST /api/v1/appointments`
- Create appointment
- Validates time slot availability

2. `GET /api/v1/appointments`
- List appointments
- Filters: `appointment_date`, `patient_id`, `doctor_id`, `status`
- Pagination: `limit`, `offset`

3. `GET /api/v1/appointments/{appointment_id}`
- Get single appointment

4. `PATCH /api/v1/appointments/{appointment_id}`
- Update appointment fields
- Re-validates schedule on date/time change

5. `POST /api/v1/appointments/{appointment_id}/cancel`
- Cancel appointment
- Accepts optional cancellation reason

6. `DELETE /api/v1/appointments/{appointment_id}`
- Hard-delete appointment

## Visit Endpoints (4)

1. `POST /api/v1/appointments/visits`
- Create visit record
- Can link to appointment via `appointment_id`

2. `GET /api/v1/appointments/visits`
- List visits
- Filters: `patient_id`, `doctor_id`, `visit_date`
- Pagination: `limit`, `offset`

3. `GET /api/v1/appointments/visits/{visit_id}`
- Get single visit

4. `PATCH /api/v1/appointments/visits/{visit_id}`
- Update visit clinical details and status

## Key Request Models

### AppointmentCreate
- `patient_id: str`
- `doctor_id: str`
- `appointment_date: date`
- `appointment_time: time`
- `duration_minutes: int` (15-240, default `30`)
- `reason?: str`
- `notes?: str`

### VisitCreate
- `patient_id: str`
- `doctor_id: str`
- `visit_date: date`
- `visit_type: consultation|follow_up|emergency|routine_checkup`
- `appointment_id?: str`
- Clinical/vitals fields optional

## Notes

- Authentication is required for all endpoints.
- All reads/writes are tenant-scoped through backend auth dependencies.
