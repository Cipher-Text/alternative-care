# AltCare — Alternative Medicine Knowledge & Practice Platform

An integrated alternative medicine practice platform, expanding in stages into public knowledge, books, directories, publishing, search, and knowledge retrieval. Existing clinic workflows remain a core capability.

## Current State (Code-Verified: 2026-09-30)

- Backend: FastAPI + SQLAlchemy async, 34 table models
- Active API modules: 16 routers: `admin`, `auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`, `medicine`, `symptom`, `tenant`, `geographic`, `public`, `institution`
- API route methods: 144 across `/api/v1` (route-registration assertion); plus `/`, `/health`, `/metrics`
- System endpoints: `/`, `/health`, `/metrics`
- Frontend: Next.js 16 + React 19 (167 files under `frontend/src`)
  - ✅ Implemented: authentication/recovery, public landing and knowledge pages, institutions directory, dashboard, patients, appointments, prescriptions, profile, payments, medicines, symptoms, integrations, and platform admin
  - 📋 Pending: AI/RAG assistant UI

## Feature Snapshot

### ✅ Implemented End-to-End (Backend + Frontend)
- **Authentication** - JWT, refresh tokens, 2FA/TOTP, session management
- **Patient Management** - CRUD, search, tags, diagnoses, demographics
- **Appointments** - Calendar view, scheduling, visits, status tracking
- **Dashboard Analytics** - Stats, revenue charts, patient demographics
- **Prescriptions** - Complete CRUD, builder, medicine items, draft/issue/void workflow, PDF generation
- **Doctor Profile** - Personal/clinic info, academic degrees, certifications/trainings
- **Payments & Billing** - Dashboard, transactions, invoices, payment recording, CSV export, toast notifications
- **Integrations** - SMS/Email/Payment provider setup and monitoring with stable local provider logos
- **Medicine & Symptom Libraries** - Global and tenant-aware clinical lookup data
- **Platform Admin Client Management** - Provision tenant + primary doctor, approve tenants, view doctor/clinic directory and details
- **Multi-tenant isolation** - application-level explicit row filtering (not PostgreSQL RLS); existing tests cover core isolation paths

### 📋 Backend-Ready, Frontend Pending
- **AI Query** - Stable backend contract exists as a `501` stub; full AI/RAG remains planned

### AI / QAI Status
- `/api/v1/ai/query` exists as stub endpoint (returns `501 Not Implemented`)
- Pro plan-gated with rate limiting (20 req/hour — `RATE_LIMIT_AI_PER_HOUR`)
- Full AI/RAG assistant with vector search remains planned work

### Security Features
- ✅ Password complexity enforcement (8+ chars, mixed case, numbers)
- ✅ Session invalidation on password/role change
- ✅ HTTP security headers (CSP, X-Frame-Options, HSTS)
- ✅ Redis-backed rate limiting (login: 5/min, API: 60/min, AI: 20/hour)
- ✅ JWT token validation (expiry, type, claims)
- ✅ 2FA/TOTP with QR code generation
- ✅ Fernet encryption for integration credentials

## Quick Start

Prerequisites: a local PostgreSQL 16 (+ pgvector) and Redis already running.

```bash
cp .env.example .env            # then set DATABASE_URL, REDIS_URL, SECRET_KEY, INTEGRATION_ENCRYPTION_KEY
cd backend && python3 -m venv venv && venv/bin/pip install -e . && venv/bin/alembic upgrade head && cd ..
cd frontend && npm install && cd ..
./run.sh
```

`run.sh` loads the root `.env` and starts the backend (uvicorn, port 8000) and frontend (Next.js, port 3000) directly, without Docker. Seed data: `backend/scripts/run_seed.sh`.

**Database roles:** run the app as a non-superuser role so row-level security applies. Grant it access with `psql -d <db> -v app_role=<app> -v owner_role=<owner> -f backend/scripts/grant_app_role.sql`, set `DATABASE_URL` to the app role and `MIGRATION_DATABASE_URL` to the owner (used only by Alembic).

**Docker alternative:** `docker compose up --build` runs Redis, MinIO, the API, Celery and the frontend from `backend/Dockerfile` and `frontend/Dockerfile`. PostgreSQL is still expected on the host (`host.docker.internal:5432`).

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Project Structure

- Backend app entry: `backend/app/main.py`
- Backend modules: `backend/app/modules/*`
- Shared models/schemas: `backend/app/shared/*`
- Frontend app routes: `frontend/src/app/*`
- Documentation hub: `docs/README.md`

## Documentation

- [Getting Started](GETTING_STARTED.md)
- [Docs Index](docs/INDEX.md)
- [Current Status](docs/status/current.md)
- [API Overview](docs/api/README.md)
- [Architecture](docs/architecture/README.md)

## Source-of-Truth Rules

When docs disagree with behavior, verify in this order:
1. `backend/app/main.py` (active routers)
2. `backend/app/modules/*/routes.py` (actual endpoints)
3. `frontend/src/app/**` (implemented UI coverage)

## Documentation Maintenance

- Long-form docs live under `docs/` — keep root to onboarding, release notes, security, and agent guidance
- Update `docs/status/current.md` after any feature-state change
- Remove completed progress reports when they no longer guide active work; keep current decisions in the changelog and status docs
