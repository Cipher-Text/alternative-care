# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AltCare** is a multi-tenant SaaS platform for alternative medicine practitioners (Homeopathy, Ayurveda, Unani, Herbal) built with FastAPI backend and Next.js frontend (coming in Phase 1, Week 5-6). The system uses row-level multi-tenancy with complete data isolation per clinic.

**Current Status:** Backend foundation complete (30 database models). **Phase 1 Week 1-12 COMPLETE** ✅ (Auth, Doctor, Patient, Appointments, Prescriptions, Payments, Dashboard). Next: Week 13 - Integration Framework.

## Essential Commands

### Development Workflow

```bash
# Start infrastructure (PostgreSQL 16 + pgvector, Redis 7, MinIO)
docker compose up -d

# Backend setup (first time)
cd backend && ./quick_start.sh

# Activate Python environment
cd backend && source venv/bin/activate

# Start development server (auto-reload enabled)
uvicorn app.main:app --reload

# Run database migrations after model changes
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Seed database with geographic data and integration providers
cd backend && ./scripts/run_seed.sh
```

### Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code (Black)
black backend/app

# Lint (Ruff)
ruff check backend/app

# Type checking (MyPy)
mypy backend/app
```

## Architecture

### Multi-Tenant Design (Critical)

**Row-Level Isolation:** Every tenant-scoped table has a `tenant_id` column. All queries are automatically scoped using SQLAlchemy filters and a ContextVar set from JWT tokens.

**Tenant Context Flow:**
1. JWT token decoded in `app/core/dependencies.py:get_current_user()`
2. `tenant_id` extracted from JWT and set in ContextVar: `tenant_id_ctx.set(tenant_id)`
3. All queries automatically filter by this context variable (no cross-tenant data leakage possible)

**Platform vs Tenant Users:**
- Platform users (admin, operator): `tenant_id = NULL` in JWT
- Tenant users (doctor, receptionist): `tenant_id = <uuid>` in JWT
- Check with `CurrentUser.is_platform_user` property

### Module Structure

```
backend/app/
├── main.py                 # FastAPI app, CORS, router registration
├── core/                   # Core infrastructure
│   ├── config.py          # Pydantic Settings (env vars)
│   ├── database.py        # SQLAlchemy async engine + session factory
│   ├── security.py        # JWT, bcrypt, TOTP 2FA, Fernet encryption
│   └── dependencies.py    # Auth dependencies, CurrentUser, role/plan checks
├── modules/                # Feature modules (each has router, schemas, service)
│   ├── auth/              # ✅ JWT login, refresh, 2FA (9 endpoints)
│   ├── doctor/            # ✅ Profile, degrees, trainings (12 endpoints)
│   ├── patient/           # ✅ Patient CRUD, search, tags, diagnoses (14 endpoints)
│   ├── appointments/      # ✅ Appointments & visits (10 endpoints)
│   ├── prescription/      # ✅ Prescription builder, PDF generation (8 endpoints)
│   ├── payment/           # 🔄 Payment processing, invoices (NEXT)
│   ├── medicine/          # 📋 Medicine database (filtered by specialization)
│   ├── library/           # 📋 EPUB reader, embeddings, RAG
│   └── integration/       # 📋 SMS/Email/Payment provider configs
└── shared/
    ├── models/            # SQLAlchemy models (30 tables)
    └── schemas/           # Pydantic request/response schemas
```

### Database Schema (30 Tables)

**Core (3):** `tenants`, `users`, `user_sessions`
**Doctor (2):** `doctor_degrees`, `doctor_trainings` (with verification)
**Geographic (3):** `divisions`, `districts`, `upazilas` (Bangladesh hierarchy)
**Patient (3):** `patients`, `patient_tags`, `patient_diagnoses`
**Prescription (2):** `prescriptions`, `prescription_items` (supports custom medicines)
**Payment (2):** `payments`, `invoices`
**Medicine (2):** `medicines`, `medicine_symptoms` (bilingual)
**Library (7):** `books`, `chapters`, `sections`, `embeddings` (pgvector), `reading_progress`, `bookmarks`, `highlights`
**Integration (3):** `integration_providers`, `tenant_integrations`, `integration_logs`
**System (2):** `translations`, `usage_tracking`

**Key Patterns:**
- All tenant-scoped tables have: `tenant_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`
- Soft deletes: Use `deleted_at IS NULL` filters, never hard delete clinical data
- Immutable records: Prescriptions and payments are append-only
- Global vs Tenant data: Medicines/books can be `is_global=true` (admin-curated) or tenant-specific

### Authentication & Security

**JWT Implementation:**
- Access tokens: 30-minute expiry, type="access"
- Refresh tokens: 7-day expiry, type="refresh"
- Claims: `sub` (user_id), `tenant_id`, `role`, `email`, `plan`
- Sign/verify in `app/core/security.py` using `python-jose`

**2FA (TOTP):**
- Setup: Generate secret → QR code → verify code → mark enabled
- Login flow: If 2FA enabled, require TOTP code after password verification
- Libraries: `pyotp` for TOTP, `qrcode` for QR generation

**Password Hashing:** Bcrypt via `passlib` (12 rounds)

**Credential Encryption:** Integration credentials (API keys) encrypted with Fernet (symmetric encryption) before storing in `tenant_integrations.credentials` JSONB field.

**Role-Based Access Control:**
```python
# In route handlers, use dependency injection:
from app.core.dependencies import RequireDoctor, RequireAdmin, require_role

@router.post("/medicines")
async def create_medicine(user: RequireDoctor):  # Only doctors
    ...

@router.delete("/users/{id}")
async def delete_user(user: RequireAdmin):  # Only admins
    ...

@router.get("/analytics")
async def analytics(user: CurrentUser = Depends(require_role("doctor", "admin"))):
    ...
```

**Plan-Based Gating:**
```python
from app.core.dependencies import require_plan, RequireProPlan

@router.post("/ai/query")
async def ai_query(user: RequireProPlan):  # Only 'pro' plan users
    ...
```

### Critical Patterns

**Async Database Sessions:**
```python
from sqlalchemy import select
from app.core.database import get_db

@router.get("/patients")
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Patient).where(Patient.tenant_id == user.tenant_id)
    )
    return result.scalars().all()
```

**Model Base Classes:**
- `BaseModel` (in `app/shared/models/base.py`): Common fields like `created_at`, `updated_at`
- `BaseAuditModel`: Adds `created_by`, `updated_by`, `deleted_at` for auditable entities
- All models inherit from one of these

**Bilingual Content:**
- Models with `_en` and `_bn` suffix fields (e.g., `name_en`, `name_bn`)
- Use `translations` table for UI strings (key-value pairs)
- User language preference in `users.language` (default: "en")

**Doctor Specialization Filtering:**
- Doctors can practice 1-4 systems: `tenant.specializations = ['homeopathy', 'ayurveda']`
- Medicines and books are filtered by: `WHERE system IN tenant.specializations OR is_global = true`
- This ensures doctors only see content relevant to their practice

**Integration Framework:**
- Providers defined in `integration_providers` (global catalog)
- Tenant configs in `tenant_integrations` (credentials encrypted)
- All API calls logged in `integration_logs` with request/response payloads
- Provider types: `sms`, `email`, `payment`

**Prescription System (NEW - Week 9-10):**
- Immutable workflow: `draft` → `issued` → `voided` (status field)
- Only drafts can be edited/have items added or removed
- Prescription items support both database medicines (medicine_id) and free-text (medicine_name)
- PDF generation ready (placeholder implementation, use ReportLab/WeasyPrint)
- Service layer enforces immutability and role-based access
- 8 endpoints: CRUD + void + PDF + add/delete items
- 98% service coverage, 89% route coverage, 36 tests (all passing)

## Development Guidelines

### Adding New Endpoints

1. **Create Pydantic schemas** in `app/modules/<module>/schemas.py`:
   - Request: `<Entity>Create`, `<Entity>Update`
   - Response: `<Entity>Response` (use `from_attributes=True` config)

2. **Create service layer** (optional but recommended for complex logic)

3. **Add router** in `app/modules/<module>/router.py`:
   ```python
   from fastapi import APIRouter, Depends
   from app.core.dependencies import RequireDoctor
   
   router = APIRouter()
   
   @router.post("/", response_model=PatientResponse)
   async def create_patient(
       data: PatientCreate,
       user: RequireDoctor,
       db: AsyncSession = Depends(get_db)
   ):
       # Automatically scope to user's tenant
       patient = Patient(**data.dict(), tenant_id=user.tenant_id)
       db.add(patient)
       await db.commit()
       return patient
   ```

4. **Register router** in `app/main.py`:
   ```python
   from app.modules.patient import router as patient_router
   app.include_router(patient_router, prefix="/api/v1/patients", tags=["Patients"])
   ```

### Database Migrations

**After adding/modifying models:**
```bash
# 1. Auto-generate migration (review before applying!)
alembic revision --autogenerate -m "Add appointments table"

# 2. Review the generated migration in backend/alembic/versions/
# 3. Edit if needed (autogenerate isn't perfect)

# 4. Apply migration
alembic upgrade head

# 5. Rollback if needed
alembic downgrade -1
```

**Important:** Always review autogenerated migrations. They may miss:
- Data migrations
- Index changes
- Constraint modifications
- Enum type changes

### Testing Multi-Tenant Isolation

**Critical test pattern:**
```python
@pytest.mark.asyncio
async def test_tenant_isolation(db_session):
    # Create two tenants
    tenant1 = Tenant(id=uuid4(), name="Clinic A")
    tenant2 = Tenant(id=uuid4(), name="Clinic B")
    db_session.add_all([tenant1, tenant2])
    
    # Create patient for tenant1
    patient = Patient(tenant_id=tenant1.id, name="John Doe")
    db_session.add(patient)
    await db_session.commit()
    
    # Query with tenant2 context - should return empty
    result = await db_session.execute(
        select(Patient).where(Patient.tenant_id == tenant2.id)
    )
    assert result.scalars().all() == []
```

**Test all tenant-scoped endpoints for isolation!** Target: 100% coverage for multi-tenant queries.

### Seed Data

After running migrations, populate initial data:
```bash
cd backend && ./scripts/run_seed.sh
```

This seeds:
- Bangladesh geographic data (8 divisions, 64 districts, sample upazilas)
- Integration providers (11 providers: SMS, Email, Payment)
- UI translations (80+ English/Bengali strings)
- Sample tenants and users for development

## Common Issues

**pgvector not installed:**
```bash
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Port 8000 in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Migration conflicts:**
```bash
# Check current state
alembic current
alembic history

# If stuck, reset (DEV ONLY - destroys data):
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

**Test database setup:**
Tests use `altcare_test` database (auto-created by conftest.py). If tests fail with DB errors, ensure PostgreSQL is running and test database exists.

## Important Conventions

- **Never bypass tenant isolation** - all queries MUST filter by `tenant_id` (except platform admin queries)
- **Use async/await** - all database operations are async (`AsyncSession`, `await db.execute()`)
- **Soft delete clinical data** - set `deleted_at` timestamp, never hard delete prescriptions/payments/patients
- **Validate plan limits** - check `usage_tracking` before creating new records (patient limits, etc.)
- **Encrypt sensitive data** - use Fernet encryption for API keys, credentials
- **Log integrations** - all SMS/email/payment API calls logged with full request/response
- **Bilingual by default** - always provide `_en` and `_bn` fields for user-facing content
- **Immutable clinical records** - prescriptions and payments are append-only (create new versions, don't edit)

## Project Roadmap Context

**Phase 1 (Current, May-July 2026):** Core Clinic MVP
- Week 1-2: ✅ Backend foundation (complete - 30 models, infra, auth)
- Week 3-4: ✅ Authentication & User Management (complete - JWT, 2FA, 9 endpoints, 45 tests)
- Week 5-6: ✅ Doctor Profile & Credentials (complete - 12 endpoints, profile/degrees/trainings)
- Week 7-8: ✅ Patient Management (complete - 14 endpoints, tags, diagnoses)
- Bonus: ✅ Appointments & Visits (complete - 10 endpoints, conflict detection)
- Week 9-10: ✅ **Prescription System (COMPLETE - 8 endpoints, 36 tests, 98% coverage)** 🎉
- Week 11: ✅ **Payment & Invoicing (COMPLETE - 12 endpoints, bKash integration, 70+ tests)** 💰
- Week 12: ✅ **Dashboard & Analytics (COMPLETE - 6 endpoints, 18 schemas, real-time stats)** 📊
- Week 13: 🔄 **Integration Framework (NEXT)**
- Week 14: Testing & Launch

**Future Phases:**
- Phase 2 (Aug-Oct 2026): Knowledge Base (medicine database, symptom search)
- Phase 3 (Nov 2026-Jan 2027): Book Library (EPUB reader, progress tracking)
- Phase 4 (Feb-Mar 2027): AI/RAG (clinical reference assistant with pgvector)

## Quick Reference

**FastAPI Docs:** http://localhost:8000/docs (when running)
**Database:** PostgreSQL 16 on localhost:5432 (docker: altcare_postgres)
**Redis:** localhost:6379 (docker: altcare_redis)
**MinIO:** http://localhost:9001 (minioadmin/minioadmin)

**Key Files:**
- `backend/app/main.py` - Application entry point
- `backend/app/core/dependencies.py` - Auth dependencies and CurrentUser
- `backend/app/core/security.py` - JWT, bcrypt, TOTP, Fernet
- `backend/alembic/versions/` - Database migrations
- `backend/tests/conftest.py` - Test fixtures and database setup
