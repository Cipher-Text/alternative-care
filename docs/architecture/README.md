---
title: "AltCare Architecture Overview"
type: "architecture"
version: "1.0.0"
last_updated: "2026-09-21"
ai_summary: "Multi-tenant SaaS architecture with FastAPI backend, Next.js frontend, and PostgreSQL with pgvector"
---

> **Revision note — 2026-09-23.** Target architecture (two model bases, RLS as a second isolation
> layer, service-layer normalisation, public/clinical path separation, storage adapter, deployment
> topology) is defined in
> [Plan, Architecture & Technology Revision §3–§4](../planning/revision-2026-09.md#3-architecture-decisions).
> This overview describes the architecture as built; the revision describes where it is going and why.


# AltCare Architecture Overview

AltCare is evolving as the **Alternative Medicine Knowledge & Practice Platform**. The current deployment is a modular monolith: one Next.js frontend, one FastAPI backend, one PostgreSQL database, Redis, and the existing Celery worker code. Knowledge, library, directory, publishing, search, and RAG capabilities remain roadmap work unless explicitly described as implemented. See the [verified architecture inventory](architecture-inventory.md).

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Architecture Patterns](#architecture-patterns)
- [Module Structure](#module-structure)
- [Data Flow](#data-flow)

---

## 🌐 System Overview

**AltCare** is a clinic management platform for Homeopathy, Ayurveda, Unani, and Herbal practitioners.

**Core Features:**
- ✅ Multi-tenant SaaS (application-level explicit tenant filtering; not PostgreSQL RLS)
- ✅ Patient management with tags and diagnoses
- ✅ Appointment scheduling with conflict detection
- ✅ Prescription builder with custom medicines
- ✅ Payment processing (cash + bKash)
- ✅ Dashboard analytics
- ✅ Doctor credentials management
- ✅ JWT authentication with 2FA

**User Roles:**
- Platform Admin/Operator (platform-wide)
- Doctor/Practitioner (tenant-scoped)
- Receptionist/Assistant (tenant-scoped)

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16
- **Extensions:** pgvector, uuid-ossp
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose), bcrypt, TOTP 2FA
- **Cache:** Redis 7
- **Storage:** MinIO (S3-compatible)

### Frontend
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **State:** Zustand
- **Data Fetching:** React Query
- **Forms:** react-hook-form + zod

### Infrastructure
- **Containers:** Docker & Docker Compose (Redis + MinIO only)
- **Database:** PostgreSQL 16 — runs natively, not containerized
- **Cache:** Redis 7 (Docker)
- **Object Storage:** MinIO (Docker)

---

## 🏗️ Architecture Patterns

### 1. Multi-Tenancy

**Strategy:** Shared database, application-level row isolation through explicit `tenant_id` predicates. PostgreSQL RLS is not configured.

**How it works:**
```
JWT Token → tenant_id extracted → passed into service constructor →
BaseTenantService helpers add .where(tenant_id == ...) explicitly
```
A `tenant_id_ctx` ContextVar exists in `app/core/dependencies.py` but is never read anywhere — it is not what enforces isolation. See [Multi-Tenancy](multi-tenancy.md) for the real mechanism and its gap (hand-written queries that skip the base-class helpers must add the filter themselves).

**Benefits:**
- Easier migrations (one schema change for all)
- Lower operational overhead
- Better resource utilization
- Cross-tenant isolation depends on every tenant-scoped query including its tenant predicate.

**See:** [Multi-Tenancy](multi-tenancy.md)

---

### 2. Authentication & Authorization

**Authentication:** JWT tokens
- Access token: 30 minutes
- Refresh token: 7 days
- TOTP 2FA optional

**Current onboarding implementation:**
- Doctor onboarding is self-registration via `POST /api/v1/auth/register`
- Registration creates both `users` (role=`doctor`) and `tenants` (clinic context)
- New tenants are blocked from login until `tenant.is_approved = true`
- Admin provisioning endpoint exists: `POST /api/v1/auth/admin/provision-client`
- Admin tenant approval endpoints exist:
  - `GET /api/v1/auth/admin/tenants/pending`
  - `POST /api/v1/auth/admin/tenants/{tenant_id}/approve`

**Authorization:** Role-based access control
- Platform users: `tenant_id = NULL`
- Tenant users: `tenant_id = <uuid>`
- Role checks via dependency injection
- Only `admin` (platform) and `doctor` (tenant) have enforced RBAC today. `operator` has a guard (`RequireAdminOrOperator`) but no endpoint uses it, and `receptionist` has no distinct enforcement from `doctor` — see [Roles & Access](roles-access.md).

**See:** [Authentication](authentication.md)

---

### 3. Database Design

**34 Tables grouped by:**
- Core (3): tenants, users, user_sessions
- Doctor (2): degrees, trainings
- Geographic (3): divisions, districts, upazilas
- Patient (3): patients, tags, diagnoses
- Clinical (6): appointments, visits, prescriptions, items, payments, invoices
- Medicine & Symptom (5): medicines, medicine_aliases, symptoms, symptom_aliases, medicine_symptom_mappings
- Library (7): books, chapters, sections, embeddings, progress, bookmarks, highlights
- Integration (3): providers, tenant_integrations, logs
- System (2): translations, usage_tracking

**Key Patterns:**
- Tenant isolation via `tenant_id`
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`
- Soft deletes: no shared `deleted_at` column — each table uses an `is_active` boolean or a `status` field instead (see [Database Schema](database-schema.md))
- Immutable records: prescriptions, payments

**See:** [Database Schema](database-schema.md)

---

### 4. Module Structure

```
backend/app/
├── main.py              # FastAPI app
├── core/                # Infrastructure
│   ├── config.py       # Settings
│   ├── database.py     # DB connection
│   ├── security.py     # JWT, bcrypt, TOTP
│   ├── rate_limit.py    # Redis-backed rate limiting
│   └── dependencies.py # Auth, CurrentUser, RBAC
├── modules/             # 14 routed modules, 129 endpoints total
│   ├── auth/            # Login, refresh (incl. login-2fa), 2FA, admin provisioning (15 endpoints)
│   ├── admin/            # Platform admin — tenants, users, KPI dashboard, doctor provisioning (10 endpoints)
│   ├── doctor/           # Profile, degrees, trainings (12 endpoints)
│   ├── patient/          # CRUD, search, tags, diagnoses (14 endpoints)
│   ├── appointments/     # Scheduling + nested visits router (10 endpoints)
│   ├── prescription/     # CRUD, items, issue, void, PDF (8 endpoints)
│   ├── payment/          # Processing, bKash (12 endpoints)
│   ├── integration/      # SMS/Email providers (12 endpoints)
│   ├── dashboard/        # Analytics, stats (6 endpoints)
│   ├── medicine/         # CRUD, search, aliases, symptom mappings (15 endpoints)
│   ├── symptom/          # CRUD, search, aliases (9 endpoints)
│   ├── geographic/       # Divisions, districts, upazilas (3 endpoints)
│   ├── tenant/           # Clinic profile (2 endpoints)
│   ├── ai/               # Stub endpoint, pro-plan gated (1 endpoint)
│   ├── library/          # Models only, no routes yet (Phase C)
│   └── notification/     # Placeholder, no routes
└── shared/
    ├── models/         # SQLAlchemy models (34 tables)
    └── schemas/        # Pydantic schemas
```

**Each module has:**
- `routes.py`: FastAPI endpoints
- `service.py`: Business logic
- `schemas.py`: Request/response models (in shared/)

---

## 🔄 Data Flow

### 1. Request Flow

```
Client Request
    ↓
[Next.js Frontend]
    ↓ HTTP/JSON
[FastAPI Backend]
    ↓ JWT Validation
[Auth Dependency] → Decode JWT → CurrentUser (incl. tenant_id)
    ↓
[Route Handler] → Dependency injection constructs Service(db, tenant_id)
    ↓
[Service Layer] → Business logic; BaseTenantService helpers filter by tenant_id
    ↓
[SQLAlchemy ORM] → Execute the tenant-filtered query
    ↓
[PostgreSQL] → Execute query
    ↓
[Response] → JSON → Client
```

---

### 2. Authentication Flow

```
1. Login
   POST /auth/login → {email, password}
   ↓
   Verify credentials
   ↓
   If 2FA enabled → require TOTP code
   ↓
   Generate JWT tokens
   ↓
   Return {access_token, refresh_token, user}

2. Authenticated Request
   GET /patients → Authorization: Bearer <token>
   ↓
   Decode JWT → extract user_id, tenant_id, role → CurrentUser
   ↓
   Service factory dependency builds PatientService(db, tenant_id)
   ↓
   Service method filters `.where(Patient.tenant_id == self.tenant_id)`
   ↓
   Return filtered results

3. Token Refresh
   POST /auth/refresh → {refresh_token}
   ↓
   Verify refresh token
   ↓
   Generate new access_token
   ↓
   Return {access_token}
```

---

### 3. Multi-Tenant Query

```python
# Service layer
class PatientService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def list_patients(self):
        # Explicit tenant filter — not automatic; every method needs this
        query = select(Patient).where(
            Patient.tenant_id == self.tenant_id,
            Patient.is_active.is_(True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

---

## 📊 System Statistics

**Current Status (feature-complete, NOT production-ready — see root `CLAUDE.md` and `docs/planning/revision-2026-09.md`):**
- **Backend modules:** 14 routed modules
- **API Endpoints:** 129 (+ `/`, `/health`, `/metrics`)
- **Database Tables:** 34
- **Frontend:** 132 source files, 11 top-level route groups
- **Test suite:** `pytest -q`: 397 passed / 2 xfailed / 0 failed (2026-09-23)
- **Security:** unscored (previous "A (95/100)" had no cited source)

**Complete:**
- ✅ Authentication (JWT, 2FA, rate limiting, password complexity)
- ✅ Doctor profile & credentials
- ✅ Patient management
- ✅ Appointments & visits
- ✅ Prescriptions
- ✅ Payments & invoices, integrations (SMS/Email/Payment)
- ✅ Dashboard analytics
- ✅ Medicines & symptoms library
- ✅ Platform admin module

**Partially built / planned:**
- Symptom → medicine lookup UI (backend endpoint exists, no dedicated page)
- `operator`/`receptionist` role enforcement (Phase B)
- Book library reader (models only, no routes/UI — Phase C)
- AI/RAG assistant (stub 501 endpoint — Phase D)
- Public doctor directory, landing page (Phase E)

---

## 🔐 Security Features

**Authentication:**
- JWT with short-lived access tokens
- Refresh token rotation
- TOTP 2FA support
- Password hashing with bcrypt

**Authorization:**
- Role-based access control
- Plan-based feature gating
- Tenant scoping via explicit per-service filtering (not automatic — see [Multi-Tenancy](multi-tenancy.md))

**Data Protection:**
- Row-level multi-tenancy
- Soft deactivation (`is_active` flag) for most tenant-scoped records — no universal `deleted_at` column
- Integration credentials encrypted (Fernet)
- HTTPS-only in production

---

## 🤖 AI Quick Reference

**Q: What's the tech stack?**
→ FastAPI + PostgreSQL + Redis + Next.js + TypeScript

**Q: How does multi-tenancy work?**
→ Row-level isolation: `tenant_id` from the JWT is passed into each service, and each service method explicitly filters by it (see [Multi-Tenancy](multi-tenancy.md) for why this isn't an automatic/global filter)

**Q: How many API endpoints?**
→ 129 endpoints across 14 backend modules

**Q: What database tables exist?**
→ 34 tables (see database-schema.md)

**Q: How is authentication handled?**
→ JWT with 30-min access tokens, 7-day refresh tokens, optional 2FA, Redis-backed rate limiting

---

**See Also:**
- [Multi-Tenancy](multi-tenancy.md) - Tenant isolation details
- [Authentication](authentication.md) - JWT + 2FA implementation
- [Database Schema](database-schema.md) - All 34 tables
- [API Reference](../api/README.md) - Endpoint reference

---

**Last Updated:** 2026-09-21  
**Version:** 1.0.0 ✅
