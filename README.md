# AltCare — Alternative Medicine Practice Management System

Multi-tenant clinic SaaS for Homeopathy, Ayurveda, Unani, and Herbal practices.

## Current State (Code-Verified: 2026-05-20)

- Backend: FastAPI + SQLAlchemy async, 34 table models
- Active API modules: `auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`
- Module endpoints: 83 total (auth: 12, ai: 1, appointments: 6, dashboard: 6, doctor: 12, integration: 12, patient: 14, payment: 12, prescription: 8)
- System endpoints: `/`, `/health`, `/metrics`
- Frontend: Next.js 16 + React 19 (90+ source files)
  - ✅ Complete: `/login`, `/dashboard`, `/patients/*`, `/appointments/*`, `/prescriptions/*`, `/profile`, `/payments/*`
  - 📋 Pending: Integrations UI

## Feature Snapshot

### ✅ Implemented End-to-End (Backend + Frontend)
- **Authentication** - JWT, refresh tokens, 2FA/TOTP, session management
- **Patient Management** - CRUD, search, tags, diagnoses, demographics
- **Appointments** - Calendar view, scheduling, visits, status tracking
- **Dashboard Analytics** - Stats, revenue charts, patient demographics
- **Prescriptions** - Complete CRUD, builder, medicine items, draft/issue/void workflow, PDF generation
- **Doctor Profile** - Personal/clinic info, academic degrees, certifications/trainings
- **Payments & Billing** - Dashboard, transactions, invoices, payment recording, CSV export, toast notifications
- **Multi-tenant Isolation** - 100% secure row-level security (16/16 tests passing)

### 📋 Backend-Ready, Frontend Pending
- **Integration Management** - SMS/Email provider setup, credential encryption, usage logs

### AI / QAI Status
- `/api/v1/ai/query` exists as stub endpoint (returns `501 Not Implemented`)
- Pro plan-gated with rate limiting (100 req/hour)
- Full AI/RAG assistant with vector search remains planned work

### Security Features
- ✅ Password complexity enforcement (8+ chars, mixed case, numbers)
- ✅ Session invalidation on password/role change
- ✅ HTTP security headers (CSP, X-Frame-Options, HSTS)
- ✅ Redis-backed rate limiting (login: 10/min, API: 100/min, AI: 100/hour)
- ✅ JWT token validation (expiry, type, claims)
- ✅ 2FA/TOTP with QR code generation
- ✅ Fernet encryption for integration credentials

## Quick Start

```bash
# 1) Infrastructure
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
