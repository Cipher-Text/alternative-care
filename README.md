# AltCare — Alternative Medicine Knowledge & Practice Platform

An integrated alternative medicine practice platform, expanding in stages into public knowledge, books, directories, publishing, search, and knowledge retrieval. Existing clinic workflows remain a core capability.

## Current State (Code-Verified: 2026-09-23)

- Backend: FastAPI + SQLAlchemy async, 34 table models
- Active API modules: `admin`, `auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`, `medicine`, `symptom`, `tenant`, `geographic`
- Module endpoints: 133 total (admin: 10, auth: 19, ai: 1, appointments: 10, dashboard: 6, doctor: 12, geographic: 3, integration: 12, medicine: 15, patient: 14, payment: 12, prescription: 8, symptom: 9, tenant: 2)
- System endpoints: `/`, `/health`, `/metrics`
- Frontend: Next.js 16 + React 19 (132 source files)
  - ✅ Complete: `/login`, `/dashboard`, `/patients/*`, `/appointments/*`, `/prescriptions/*`, `/profile`, `/payments/*`, `/settings/integrations`, `/medicines/*`, `/symptoms/*`, `/admin/clients`, `/admin/dashboard`, `/admin/users`
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

```bash
# 1) Infrastructure (Redis + MinIO only — PostgreSQL 16 must already be running locally)
docker compose up -d

# 2) Backend
cd backend
./quick_start.sh
source venv/bin/activate
alembic upgrade head
./scripts/run_seed.sh
uvicorn app.main:app --reload

# 3) Frontend (new terminal)
cd frontend
npm install
npm run dev
```

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
- Move dated progress reports to `docs/archive/` once they stop guiding active work
