# Current Project Status

Last Updated: 2026-05-20

## Summary

AltCare currently has a working FastAPI backend with 9 registered API modules and a working Next.js frontend with auth, dashboard, profile, patients, appointments, prescriptions, and payments flows implemented.

Recent launch-readiness work completed on 2026-05-08:
- P0 auth fixes completed: password complexity enforcement and session invalidation on password change
- Baseline HTTP security headers middleware enabled for all responses (CSP, X-Frame-Options, X-Content-Type-Options; HSTS in production)
- Redis-backed baseline rate limiting enabled (strict login scope + per-IP/per-user API scope)
- AI query endpoint now has dedicated hourly quota scope (`/api/v1/ai/query`)

## Code-Verified State

### Backend
- Registered routers in `backend/app/main.py`:
  - `auth`
  - `ai`
  - `appointments`
  - `dashboard`
  - `doctor`
  - `patient`
  - `prescription`
  - `payment`
  - `integration`
- Endpoint count from route decorators: 83 module endpoints
- System endpoints: `/`, `/health`, `/metrics`
- Data model scope: 34 table models (+ 3 base classes, multi-tenant pattern)
- Onboarding/auth reality:
  - `POST /api/v1/auth/register` creates both doctor user and tenant (clinic) in one flow
  - New doctor tenants are created with `is_approved = false`
  - Admin provisioning endpoint available: `POST /api/v1/auth/admin/provision-client` (creates tenant + primary doctor)
  - Admin approval endpoints available:
    - `GET /api/v1/auth/admin/tenants/pending`
    - `POST /api/v1/auth/admin/tenants/{tenant_id}/approve`

### Frontend
- Stack: Next.js 16, React 19, TypeScript
- Implemented app routes:
  - `/` (landing page)
  - `/login`
  - `/dashboard`
  - `/profile`
  - `/patients`, `/patients/new`, `/patients/[id]`, `/patients/[id]/edit`
  - `/appointments`, `/appointments/new`, `/appointments/[id]`, `/appointments/[id]/edit`
  - `/prescriptions`, `/prescriptions/new`, `/prescriptions/[id]`, `/prescriptions/[id]/edit`
- Dashboard layout/auth shell is in place
- UI Components: shadcn/ui (button, card, input, select, badge, table, dialog)

### AI / QAI-Related Features
- `/api/v1/ai/query` is now exposed as a plan-gated stub endpoint
- Current behavior returns `501 Not Implemented`
- AI/RAG remains planned work beyond this contract endpoint

## What Is Implemented End-to-End
- Authentication flows (including 2FA support) across backend and frontend login flow
- Patient management APIs and corresponding frontend patient screens (CRUD complete)
- Appointment scheduling APIs and corresponding frontend calendar/list views
- Dashboard analytics APIs and dashboard UI
- Prescription list/create/detail/edit views
- Multi-tenant enforcement patterns in backend architecture and tests
- Baseline API security response headers middleware
- Doctor self-registration with pending-approval gate before first login

## What Is Backend-Ready but Frontend-Partial
- Integrations have backend routes but no frontend route coverage in `frontend/src/app`

## Documentation Source-of-Truth Rules

For factual checks:
1. `backend/app/main.py` for active modules
2. `backend/app/modules/*/routes.py` for endpoint truth
3. `frontend/src/app/**` for implemented UI routes
4. planning docs for future scope
