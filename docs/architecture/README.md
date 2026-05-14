---
title: "AltCare Architecture Overview"
type: "architecture"
version: "0.9.0"
last_updated: "2026-05-14"
ai_summary: "Multi-tenant SaaS architecture with FastAPI backend, Next.js frontend, and PostgreSQL with pgvector"
---

# AltCare Architecture Overview

Multi-tenant SaaS platform for alternative medicine practitioners with row-level data isolation.

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
- ✅ Multi-tenant SaaS (row-level isolation)
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
- **Containers:** Docker & Docker Compose
- **Database:** PostgreSQL 16 (Docker)
- **Cache:** Redis 7 (Docker)
- **Object Storage:** MinIO (Docker)

---

## 🏗️ Architecture Patterns

### 1. Multi-Tenancy

**Strategy:** Shared database, row-level isolation

**How it works:**
```
JWT Token → tenant_id extracted → Set in ContextVar → All queries auto-filter
```

**Benefits:**
- Easier migrations (one schema change for all)
- Lower operational overhead
- Better resource utilization
- Impossible cross-tenant data leakage

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

**See:** [Authentication](authentication.md)

---

### 3. Database Design

**30 Tables grouped by:**
- Core (3): tenants, users, user_sessions
- Doctor (2): degrees, trainings
- Geographic (3): divisions, districts, upazilas
- Patient (3): patients, tags, diagnoses
- Clinical (6): appointments, visits, prescriptions, items, payments, invoices
- Medicine (2): medicines, symptoms
- Library (7): books, chapters, sections, embeddings, progress, bookmarks, highlights
- Integration (3): providers, tenant_integrations, logs
- System (2): translations, usage_tracking

**Key Patterns:**
- Tenant isolation via `tenant_id`
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`
- Soft deletes: `deleted_at`
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
│   └── dependencies.py # Auth, CurrentUser
├── modules/             # Feature modules
│   ├── auth/           # 16 endpoints
│   ├── patient/        # 14 endpoints
│   ├── appointments/   # 6 endpoints
│   ├── prescription/   # 8 endpoints
│   ├── payment/        # 12 endpoints
│   ├── dashboard/      # 6 endpoints
│   ├── doctor/         # 12 endpoints
│   ├── integration/    # 12 endpoints
│   └── ai/             # 1 endpoint
└── shared/
    ├── models/         # SQLAlchemy models
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
[Auth Middleware] → Extract tenant_id
    ↓
[Route Handler] → Dependency injection (CurrentUser)
    ↓
[Service Layer] → Business logic
    ↓
[SQLAlchemy ORM] → Auto-filter by tenant_id
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
   Decode JWT → extract user_id, tenant_id, role
   ↓
   Set ContextVar → tenant_id_ctx.set(tenant_id)
   ↓
   Execute query with auto-filter
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
        # Auto-filter by tenant
        query = select(Patient).where(
            Patient.tenant_id == self.tenant_id,
            Patient.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

---

## 📊 System Statistics

**Current Status (v0.9.0):**
- **Modules:** 7 complete
- **API Endpoints:** 71
- **Database Tables:** 30
- **Test Coverage:** 100+ tests
- **Lines of Code:** ~15,000 (backend)

**Phase 1 Complete:**
- ✅ Authentication (JWT, 2FA)
- ✅ Doctor profile & credentials
- ✅ Patient management
- ✅ Appointments & visits
- ✅ Prescriptions
- ✅ Payments & invoices
- ✅ Dashboard analytics

**Next Phase:**
- Integration framework (SMS/Email/Payment)
- Medicine database
- Book library
- AI/RAG assistant

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
- Automatic tenant scoping

**Data Protection:**
- Row-level multi-tenancy
- Soft deletes for clinical data
- Integration credentials encrypted (Fernet)
- HTTPS-only in production

---

## 🤖 AI Quick Reference

**Q: What's the tech stack?**
→ FastAPI + PostgreSQL + Redis + Next.js + TypeScript

**Q: How does multi-tenancy work?**
→ Row-level isolation with tenant_id in JWT → auto-filtered queries

**Q: How many API endpoints?**
→ 71 endpoints across 7 modules

**Q: What database tables exist?**
→ 30 tables (see database-schema.md)

**Q: How is authentication handled?**
→ JWT with 30-min access tokens, 7-day refresh tokens, optional 2FA

---

**See Also:**
- [Multi-Tenancy](multi-tenancy.md) - Tenant isolation details
- [Authentication](authentication.md) - JWT + 2FA implementation
- [Database Schema](database-schema.md) - All 30 tables
- [API Reference](../api/README.md) - 71 endpoints

---

**Last Updated:** May 1, 2026  
**Version:** 0.9.0 ✅
