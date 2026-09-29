---
title: "AltCare API Overview"
type: "api-reference"
version: "1.0.0"
last_updated: "2026-09-30"
ai_summary: "144 API route methods across 16 routers, including authenticated practice APIs and public read-only catalogs"
base_url: "http://localhost:8000/api/v1"
---

# AltCare API Documentation

**Base URL:** `http://localhost:8000/api/v1`
**Total API methods:** 144 under `/api/v1` (verified by `backend/tests/unit/test_route_registration.py`) + 3 system endpoints (`/`, `/health`, `/metrics`)
**Authentication:** JWT Bearer Token
**Format:** JSON

## Overview

**16 API routers:**

| Module | Endpoints | Purpose | Docs |
|--------|-----------|---------|------|
| **Admin** | 11 | Platform dashboard, tenants, users, tenant usage | N/A |
| **Authentication** | 16 | Login (incl. login-2fa), registration (password or Google), password reset, email verification, session lifecycle | [authentication.md](authentication.md) |
| **AI** | 1 | Query stub (`501`) | N/A (stub) |
| **Patients** | 14 | Patient CRUD, search | [patients.md](patients.md) |
| **Appointments** | 10 | Scheduling and visits | [appointments.md](appointments.md) |
| **Prescriptions** | 8 | Prescription builder | [prescriptions.md](prescriptions.md) |
| **Payments** | 12 | Payments, invoices | [payments.md](payments.md) |
| **Dashboard** | 6 | Analytics, charts | [dashboard.md](dashboard.md) |
| **Doctor** | 12 | Profile, credentials | [doctor.md](doctor.md) |
| **Geographic** | 3 | Bangladesh divisions, districts, upazilas | N/A |
| **Integrations** | 12 | Provider config, send SMS/email, logs | [integrations.md](integrations.md) |
| **Medicine** | 15 | Global and tenant medicines, aliases, symptom mappings | N/A |
| **Symptom** | 9 | Global and tenant symptoms, aliases | N/A |
| **Tenant** | 2 | Clinic profile | N/A |
| **Public** | 8 | Unauthenticated read-only global medicine, symptom, and institution catalogs | N/A |
| **Institutions** | 5 | Authenticated institution catalog; admin-only mutations | N/A |

The public router exposes 8 methods: list/search/detail for global medicines and symptoms, plus list/detail for institutions. The institution router exposes 5 methods. Counts include each HTTP method registered on `/api/v1`; the regression assertion is authoritative when routes change.

## Authentication

Authenticated endpoints require bearer auth, except public read-only catalog endpoints under `/public`. Authentication endpoints document their own requirements.

```http
Authorization: Bearer <access_token>
```

## AI Module Status

`POST /api/v1/ai/query` is intentionally a placeholder route that returns:
- `501 Not Implemented`
- `{"detail": "AI module is planned but not implemented yet.", "status": "not_implemented"}`

This route is plan-gated (`pro`) and exists as a stable contract for future AI/RAG implementation.

## Common Status Codes

- `200` success
- `201` created
- `400` bad request
- `401` unauthorized
- `403` forbidden
- `404` not found
- `409` conflict
- `422` validation error
- `501` not implemented (AI stub)

## Notes

Endpoint totals above are derived from the FastAPI route table in `backend/app/main.py`.
