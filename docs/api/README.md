---
title: "AltCare API Overview"
type: "api-reference"
version: "1.0.0"
last_updated: "2026-05-14"
ai_summary: "87 REST endpoints across 9 modules (including AI stub) with JWT authentication"
base_url: "http://localhost:8000/api/v1"
---

# AltCare API Documentation

**Base URL:** `http://localhost:8000/api/v1`  
**Total Endpoints:** 87 (module routes) + 3 system endpoints (`/`, `/health`, `/metrics`)  
**Authentication:** JWT Bearer Token  
**Format:** JSON

## Overview

**9 API Modules:**

| Module | Endpoints | Purpose | Docs |
|--------|-----------|---------|------|
| **Authentication** | 16 | Login, 2FA, registration, admin provisioning/approval | [authentication.md](authentication.md) |
| **AI** | 1 | Query stub (`501`) | N/A (stub) |
| **Patients** | 14 | Patient CRUD, search | [patients.md](patients.md) |
| **Appointments** | 6 | Scheduling | [appointments.md](appointments.md) |
| **Prescriptions** | 8 | Prescription builder | [prescriptions.md](prescriptions.md) |
| **Payments** | 12 | Payments, invoices | [payments.md](payments.md) |
| **Dashboard** | 6 | Analytics, charts | [dashboard.md](dashboard.md) |
| **Doctor** | 12 | Profile, credentials | [doctor.md](doctor.md) |
| **Integrations** | 12 | Provider config, send SMS/email, logs | [integrations.md](integrations.md) |

**Total:** 87 module endpoints

## Authentication

All endpoints except registration/login require bearer auth.

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

Endpoint totals above are derived from route decorators in `backend/app/modules/*/routes.py` and router registration in `backend/app/main.py`.
