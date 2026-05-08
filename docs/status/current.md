# Current Project Status

Last Updated: 2026-05-08

## Summary

AltCare currently has a working FastAPI backend with 9 registered API modules and a partial Next.js frontend focused on auth, dashboard, and patient workflows.

Recent launch-readiness work completed on 2026-05-08:
- P0 auth fixes completed: password complexity enforcement and session invalidation on password change
- Baseline HTTP security headers middleware enabled for all responses (CSP, X-Frame-Options, X-Content-Type-Options; HSTS in production)
- Redis-backed baseline rate limiting enabled (strict login scope + general API scope)

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
- Endpoint count from route decorators: 80 module endpoints
- System endpoints: `/` and `/health`
- Data model scope: 30 SQLAlchemy models (multi-tenant pattern)

### Frontend
- Stack: Next.js 16, React 19, TypeScript
- Implemented app routes:
  - `/login`
  - `/dashboard`
  - `/patients`
  - `/patients/new`
  - `/patients/[id]`
- Dashboard layout/auth shell is in place

### AI / QAI-Related Features
- `/api/v1/ai/query` is now exposed as a plan-gated stub endpoint
- Current behavior returns `501 Not Implemented`
- AI/RAG remains planned work beyond this contract endpoint

## What Is Implemented End-to-End
- Authentication flows (including 2FA support) across backend and frontend login flow
- Patient management APIs and corresponding frontend patient screens
- Dashboard analytics APIs and dashboard UI
- Multi-tenant enforcement patterns in backend architecture and tests
- Baseline API security response headers middleware

## What Is Backend-Ready but Frontend-Partial
- Doctor profile, appointments, prescriptions, payments, and integrations have backend routes but limited or no full UI coverage in `frontend/src/app`

## Documentation Source-of-Truth Rules

For factual checks:
1. `backend/app/main.py` for active modules
2. `backend/app/modules/*/routes.py` for endpoint truth
3. `frontend/src/app/**` for implemented UI routes
4. planning docs for future scope
