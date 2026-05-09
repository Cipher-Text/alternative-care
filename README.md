# AltCare — Alternative Medicine Practice Management System

Multi-tenant clinic SaaS for Homeopathy, Ayurveda, Unani, and Herbal practices.

## Current State (Code-Verified: 2026-05-09)

- Backend: FastAPI + SQLAlchemy async, 30 models
- Active API modules: `auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`
- Module endpoints: 82+ (`81+` implemented business endpoints + `1` AI stub)
- System endpoints: `/`, `/health`, `/metrics`
- Frontend: Next.js 16 + React 19
  - Implemented: `/login`, `/dashboard`, `/patients/*`, `/appointments/*`, `/prescriptions` (list/detail)
  - In Progress: `/prescriptions/new` (builder pending)

## Feature Snapshot

### Implemented End-to-End
- Authentication (JWT, refresh, 2FA, session management)
- Patient management (CRUD, search, tags, diagnoses)
- Appointments (calendar, scheduling, visits)
- Dashboard analytics (stats, charts, filters)
- Prescriptions (list, detail, status management) - **builder pending**
- Multi-tenant isolation (100% secure, row-level)

### Backend-Ready, Frontend Pending
- Doctor profile management
- Prescription builder (create/edit form)
- Payments processing
- Integration management

### AI / QAI Status
- `/api/v1/ai/query` exists as a stub endpoint and returns `501 Not Implemented`
- Full AI/RAG assistant remains planned work

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
