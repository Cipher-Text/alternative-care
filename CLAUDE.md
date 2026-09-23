# AltCare - Multi-Tenant Alternative Medicine Platform

FastAPI + Next.js 16 SaaS for alternative medicine practitioners (Homeopathy, Ayurveda, Unani, Herbal) with row-level multi-tenancy.

---

## 1. PROJECT STATUS

**MVP v1.0 feature-complete — NOT production ready** ⚠️

**Last Verified:** 2026-09-23 (code-verified, see `docs/planning/revision-2026-09.md`)

> The "Production Ready" claim previously here did not hold. Stage 0 ("Truth & Green") is now
> mostly done — code-verified on 2026-09-23: `pytest -q` runs **397 passed / 2 xfailed / 0 failed**
> locally (was 322 passed / 76 failed earlier the same day; the gap was mostly test-harness bugs —
> a shared-Redis rate limiter poisoning unrelated tests, and a fixture bug where
> `authenticated_client`/`authenticated_client_2` were silently the same object — plus several real
> bugs the harness noise had been masking, including a refresh-token rotation bug and two shadowed
> routes; see Stage 0 in `docs/planning/revision-2026-09.md` for the full list). Sentry and structlog
> are now initialised (`app/core/observability.py`). Still true: **no Dockerfile, no IaC, no deploy
> path**; password reset and email verification exist only as commented-out code
> (`app/modules/auth/routes.py:285-322`); global medicine/symptom creation writes `tenant_id=None`
> into a `NOT NULL` column and fails at the database (`medicine/routes.py:102`,
> `symptom/routes.py:93`) — this is Stage 2's keystone fix, not yet done; `usage_tracking` has no
> writers so plans are unenforced (2 tests pinned as `xfail` document this and the receptionist-RBAC
> gap so they can't silently regress further).
>
> **Read `docs/planning/revision-2026-09.md` before planning work.** It carries the current
> stage plan (Stage 0 Truth & Green → Stage 4 Retrieval Assistant), the architecture decisions
> (D1-D10), and the technology decisions (T1-T10) that supersede the phase list in `docs/ROADMAP.md`.

**Core modules (backend + frontend complete):**
- Authentication (Login, 2FA, JWT, Sessions, Password Security) ✅
- Patient Management (CRUD, Tags, Diagnoses, Geographic dropdowns) ✅
- Dashboard Analytics (Stats, Revenue, Demographics) ✅
- Appointments (Scheduling, Calendar, Visits) ✅
- Prescriptions (Builder, Items, Issue/Void workflow) ✅
- Doctor Profile (Degrees, Trainings) ✅
- Payments & Invoicing ✅
- Integrations (SMS/Email/Payment providers) ✅
- Medicines library (CRUD, Aliases, Search API, Symptom mappings) ✅
- Symptoms library (CRUD, Aliases, Search API) ✅
- Geographic data API (Divisions, Districts, Upazilas — Bangladesh) ✅
- Multi-tenant isolation (16/16 tests passing) ✅
- Security hardening (Rate limiting, HTTP headers, Password complexity) ✅
- Platform Admin — dedicated module, KPI dashboard, tenant lifecycle, role management ✅

**Backend:** 14 routed modules, 129 endpoints (+ `/`, `/health`, `/metrics`), 34 table models
**Frontend:** 132 source files, 11 top-level route groups (35 pages incl. dynamic routes)
**Security:** A (95/100)

**Partially built (backend done, frontend missing):**
- Symptom → Medicine lookup UI — `GET /medicines/symptoms/{id}/medicines` exists, no dedicated page
- Medicine search page uses client-side filter on 100 rows instead of calling `GET /medicines/search`

**Planned (future phases):**
- Book library reader — DB models exist (`books`, `chapters`, `sections`, `reading_progress`, `bookmarks`, `highlights`, `embeddings`), no routes or UI yet — see `docs/ROADMAP.md` Phase C
- AI chat assistant (RAG) — stub 501 endpoint exists at `POST /api/v1/ai/query` — see `docs/ROADMAP.md` Phase D
  - Knowledge sources: book library (vector search via pgvector) + medicine DB + symptom DB (structured lookup)
  - Responses filtered by doctor's specializations; every answer cites its source
  - Pro plan only; 200 queries/month quota tracked in `usage_tracking`
- `operator` / `receptionist` role enforcement — Phase B
- Public doctor directory — mock designed at `mock/doctors.html` — Phase E
- Public landing page

---

## 2. QUICK START

### First Time Setup

```bash
# 1. Start infrastructure (Redis + MinIO; PostgreSQL runs natively, not in Docker)
docker compose up -d
# Ensure a local PostgreSQL 16 (+ pgvector) instance is running and DATABASE_URL in backend/.env points to it

# 2. Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add to backend/.env: INTEGRATION_ENCRYPTION_KEY=<key>

# 3. Backend setup
cd backend && ./quick_start.sh
source venv/bin/activate
alembic upgrade head
./scripts/run_seed.sh

# 4. Frontend setup
cd frontend && npm install
```

### Daily Development

```bash
# Backend (port 8000)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev

# Celery (background tasks)
celery -A app.core.celery:celery_app worker --loglevel=info
```

### Testing

```bash
# Backend
pytest --cov=app --cov-report=html
pytest tests/integration/test_mvp_tenant_isolation.py -v

# Frontend
cd frontend && npx playwright test --ui
```

### More Guides

- [Implementation patterns (endpoints, migrations, hooks)](docs/development/implementation-guide.md)
- [Troubleshooting common issues](docs/development/troubleshooting.md)
- [Bilingual (i18n) guide](docs/development/i18n.md)

---

## 3. TECH STACK

**Backend:**
- FastAPI (async/await), SQLAlchemy 2.0 (AsyncSession)
- PostgreSQL 16 + pgvector, Redis 7, MinIO
- JWT (python-jose), Bcrypt (passlib), TOTP 2FA (pyotp)
- Fernet encryption (cryptography), Celery (background tasks)
- pytest, Alembic, Pydantic

**Frontend:**
- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4, shadcn/ui (Radix UI)
- Zustand (client state), React Query (server state)
- React Hook Form, Zod validation, Axios
- next-intl (English/Bengali), Playwright (E2E)

**Infrastructure:**
- Docker Compose (Redis, MinIO) — PostgreSQL runs natively, not containerized
- Docker containers: `altcare_redis`, `altcare_minio`

---

## 4. ARCHITECTURE

### 4.1 Multi-Tenant Security (CRITICAL)

**Row-Level Isolation:**
```python
# Every tenant-scoped table has tenant_id

# Flow:
# 1. JWT decoded → app/core/dependencies.py:get_current_user() → CurrentUser.tenant_id
# 2. Route's service-factory dependency (e.g. get_patient_service) constructs
#    the service with tenant_id passed explicitly: PatientService(db, tenant_id)
# 3. app/core/base_service.py:BaseTenantService stores self.tenant_id and adds
#    `.where(model.tenant_id == self.tenant_id)` inside its shared helpers
#    (_get_base_query, get_by_id, count, list_with_pagination)

# Platform users: tenant_id = NULL (admin, operator)
# Tenant users: tenant_id = <uuid> (doctor, receptionist)
```

> **Not automatic at the query layer:** `app/core/dependencies.py` also defines a `tenant_id_ctx` ContextVar that gets `.set()` once during auth, but nothing in the codebase ever calls `.get()` on it — it's unused/dead code, not a session-level auto-filter. Real isolation only holds for code that goes through `BaseTenantService`'s helpers or that manually adds the `tenant_id` filter itself; a hand-written query that skips both is a tenant-isolation bug the type system won't catch.

**Testing Pattern:**
```python
@pytest.mark.asyncio
async def test_tenant_isolation(db_session):
    tenant1, tenant2 = Tenant(), Tenant()
    patient = Patient(tenant_id=tenant1.id, name="John")
    
    # Query with tenant2 context → empty
    result = await db_session.execute(
        select(Patient).where(Patient.tenant_id == tenant2.id)
    )
    assert result.scalars().all() == []
```

### 4.2 Authentication & Authorization

**JWT Tokens:**
- Access: 30min expiry, type="access"
- Refresh: 7d expiry, type="refresh"
- Claims: `sub` (user_id), `tenant_id`, `role`, `email`, `plan`, `token_version` (bumped on password/email/role change to invalidate old tokens; refresh tokens carry only `sub` + `token_version` + a `jti`)
- Refresh tokens are hashed with SHA-256 for storage/lookup (`hash_refresh_token`/`verify_refresh_token`), not bcrypt — bcrypt truncates at 72 bytes, which made two refresh tokens for the same user hash identically and silently broke rotation
- Location: `app/core/security.py` (python-jose)

**2FA (TOTP):**
- Setup: Generate secret → QR code → verify code → enable
- Login: Password → TOTP code (if enabled)
- Libraries: `pyotp`, `qrcode`

**Password:** Bcrypt (12 rounds, passlib)
**Credentials:** Fernet encrypted (JSONB field: `tenant_integrations.credentials`)

**Roles** (see `docs/architecture/roles-access.md` for full reference):

| Role | Level | `tenant_id` | Status |
|---|---|---|---|
| `admin` | Platform | `null` | ✅ Full |
| `operator` | Platform | `null` | ⚠️ RBAC stub, no endpoints |
| `doctor` | Tenant | `<uuid>` | ✅ Full |
| `receptionist` | Tenant | `<uuid>` | ⚠️ No enforcement |

Platform users (`tenant_id = null`) are rejected with **403** from all tenant-scoped service factories.

**Role-Based Access:**
```python
from app.core.dependencies import RequireDoctor, RequireAdmin, require_role

@router.post("/medicines")
async def create_medicine(user: RequireDoctor):  # Doctors only
    ...

@router.get("/analytics")
async def analytics(user: CurrentUser = Depends(require_role("doctor", "admin"))):
    ...
```

**Plan-Based Access:**
```python
from app.core.dependencies import RequireProPlan

# AI query endpoint (registered, requires 'pro' plan)
@router.post("/ai/query")
async def ai_query(user: RequireProPlan):  # 'pro' plan only
    ...  # Returns 501 Not Implemented (stub)
```

**Rate Limiting** (`app/core/rate_limit.py`, Redis-backed):
- Login: 5 req/min per IP — General API: 60 req/min per IP — AI: 20 req/hour per user
- Returns `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` on 429
- Config keys: `RATE_LIMIT_ENABLED` (default `true` — a global kill switch; the test suite sets this `false` by default per test via an autouse `conftest.py` fixture, since a shared Redis rate limiter otherwise poisons unrelated tests), `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_LOGIN_PER_MINUTE`, `RATE_LIMIT_AI_PER_HOUR`

**Security Headers** (`app/main.py` middleware): `X-Content-Type-Options`, `X-Frame-Options: DENY`, CSP, HSTS (production). Config: `SECURITY_HEADERS_ENABLED`, `SECURITY_HSTS_ENABLED`.

**Password Security** (`app/modules/auth/schemas.py:_validate_password_strength`): 8+ chars, upper + lower + number. Applied to registration, password change, password reset.

### 4.3 Database Schema (34 Tables)

**Core:** `tenants`, `users`, `user_sessions`
**Doctor:** `doctor_degrees`, `doctor_trainings`
**Geographic:** `divisions`, `districts`, `upazilas` (Bangladesh)
**Patient:** `patients`, `patient_tags`, `patient_diagnoses`
**Appointments:** `appointments`, `visits`
**Prescription:** `prescriptions`, `prescription_items`
**Payment:** `payments`, `invoices`
**Medicine:** `medicines`, `medicine_aliases`
**Symptom:** `symptoms`, `symptom_aliases`, `medicine_symptom_mappings`
**Library:** `books`, `chapters`, `sections`, `embeddings`, `reading_progress`, `bookmarks`, `highlights`
**Integration:** `integration_providers`, `tenant_integrations`, `integration_logs`
**System:** `translations`, `usage_tracking`

**Table Patterns:**
- Tenant-scoped: `tenant_id`, `created_at`, `updated_at`, `created_by`, `updated_by`
- Soft deactivation: per-table `is_active: bool` flag (patients, medicines, symptoms, tenants, users, integrations, translations, library) — there is no `deleted_at` column anywhere in the schema. Some child records (e.g. patient tags) are hard-deleted instead — check the specific route/service before assuming soft delete.
- Immutable: Prescriptions/payments are append-only (draft → issued → voided)
- Global vs Tenant: `is_global=true` (admin-curated) or tenant-specific

**Model Base Classes:**
```python
# app/shared/models/base.py
BaseAuditModel → created_at, updated_at, created_by, updated_by
TenantScopedModel(BaseAuditModel) → + tenant_id
```

### 4.4 Backend Module Structure

```
backend/app/
├── main.py                 # FastAPI app, CORS, router registration
├── core/                   # Infrastructure
│   ├── config.py          # Settings (env vars)
│   ├── database.py        # SQLAlchemy async engine
│   ├── security.py        # JWT, bcrypt, TOTP, Fernet
│   ├── rate_limit.py      # Redis-backed rate limiting
│   ├── celery.py          # Background tasks
│   └── dependencies.py    # Auth, RBAC, plan checks
├── modules/               # Feature modules (129 total endpoints)
│   ├── auth/             # ✅ Login, refresh (incl. login-2fa), 2FA, admin provisioning (15 endpoints)
│   ├── admin/            # ✅ Platform admin — tenants, users, KPI dashboard, doctor provisioning (10 endpoints)
│   ├── doctor/           # ✅ Profile, degrees, trainings (12 endpoints)
│   ├── patient/          # ✅ CRUD, search, tags, diagnoses (14 endpoints)
│   ├── appointments/     # ✅ Scheduling, visits (10 endpoints)
│   ├── prescription/     # ✅ CRUD, items, issue, void, PDF (8 endpoints)
│   ├── payment/          # ✅ Processing, bKash (12 endpoints)
│   ├── integration/      # ✅ SMS/Email providers (12 endpoints)
│   ├── dashboard/        # ✅ Analytics, stats (6 endpoints)
│   ├── ai/               # ✅ Stub endpoint, pro-plan gated (1 endpoint)
│   ├── medicine/         # ✅ CRUD, search, aliases, symptom mappings (15 endpoints)
│   ├── symptom/          # ✅ CRUD, search, aliases (9 endpoints)
│   ├── geographic/       # ✅ Divisions, districts, upazilas (3 endpoints)
│   ├── tenant/           # ✅ Clinic profile (2 endpoints)
│   ├── library/          # 📋 Models exist (books/chapters/sections/embeddings/progress/bookmarks/highlights), no routes — Phase C
│   └── notification/     # 📋 Placeholder
└── shared/
    ├── models/           # SQLAlchemy models
    └── schemas/          # Pydantic schemas
```

### 4.5 Frontend Structure

```
frontend/src/
├── app/                   # Next.js App Router
│   ├── (auth)/login/     # ✅ Login + 2FA
│   ├── (dashboard)/      # ✅ Protected routes
│   │   ├── dashboard/    # ✅ Analytics charts
│   │   ├── patients/     # ✅ Patient CRUD
│   │   ├── appointments/ # ✅ Appointment scheduling & views
│   │   ├── prescriptions/# ✅ List, detail, create/edit builder
│   │   ├── profile/      # ✅ Doctor profile with degrees & trainings
│   │   ├── payments/     # ✅ Payment dashboard, transactions, invoices
│   │   ├── medicines/    # ✅ Medicine library CRUD with autocomplete (⚠️ list uses client-side filter, not /search API)
│   │   ├── symptoms/     # ✅ Symptom library CRUD (⚠️ no symptom→medicine lookup page yet)
│   │   ├── settings/     # ✅ Integrations management
│   │   └── admin/        # ✅ Dashboard, clients (directory/provision/pending), users (role management)
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Landing
├── components/
│   ├── auth/             # ✅ LoginForm, TwoFactorForm
│   ├── dashboard/        # ✅ Charts, Stats
│   ├── patients/         # ✅ PatientCard, PatientForm
│   ├── prescriptions/    # ✅ PrescriptionBuilder, MedicineItemsBuilder (with autocomplete), PatientSelector
│   ├── doctor/           # ✅ ProfileForm, DegreesSection, TrainingsSection
│   ├── payments/         # ✅ PaymentDashboard, TransactionList, InvoiceForm
│   ├── integrations/     # ✅ ProviderList, ConfigWizard, IntegrationLogs
│   ├── medicines/        # ✅ MedicineAutocomplete (smart search with keyboard nav)
│   ├── layout/           # ✅ Header, Sidebar
│   ├── shared/           # ✅ Shared utilities
│   └── ui/               # ✅ shadcn/ui (button, card, table, badge, textarea, etc.)
│   # Note: Appointments and symptoms use route-level components
├── lib/
│   ├── api/              # ✅ API clients (auth, patients, dashboard, appointments, prescriptions, payments, integrations, medicines, symptoms)
│   ├── hooks/            # ✅ React Query hooks (use* for all modules)
│   └── utils/            # ✅ Helpers
├── types/                # ✅ TypeScript interfaces
│   ├── patient.ts
│   ├── appointment.ts
│   ├── prescription.ts
│   ├── doctor.ts
│   ├── dashboard.ts
│   ├── payment.ts
│   ├── integration.ts
│   ├── medicine.ts
│   └── symptom.ts
└── stores/
    └── authStore.ts      # ✅ Zustand auth state
```

### 4.6 Prescription Builder (Frontend)

**Components:** `PrescriptionBuilder` (main form) → `MedicineItemsBuilder` (dynamic list with autocomplete, auto-fill dosage) → `MedicineAutocomplete` (300ms debounce, keyboard nav, alias search, match-rank scoring) + `PatientSelector` (real-time search by name/phone/code).

**Routes:** `/prescriptions`, `/prescriptions/new`, `/prescriptions/[id]`, `/prescriptions/[id]/edit`

**Workflow (immutable):**
```
draft → issued → voided
```
- Only drafts are editable; issued/voided cannot be modified or have items added/deleted
- Medicine items: `medicine_id` (DB) OR `medicine_name` (free-text)

### 4.7 Critical Patterns

**Async Database:**
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

**Bilingual Content:**
- Fields: `name_en`, `name_bn`
- Table: `translations` (key-value pairs)
- User: `users.language` (default: "en")

**Doctor Specialization (not yet implemented):**
```python
# tenant.specializations = ['homeopathy', 'ayurveda'] exists on the Tenant model,
# and medicines/library models are documented as "filtered by specialization" —
# but no route or service currently filters by it. Medicine list/search only
# filter by is_global / tenant_id (see app/modules/medicine/routes.py).
# Intended behavior once built: WHERE system IN tenant.specializations OR is_global = true
```

**Integration Framework:**
- Providers: `integration_providers` (global catalog)
- Configs: `tenant_integrations` (credentials encrypted)
- Audit: `integration_logs` (request/response)
- Types: `sms`, `email`, `payment`
- Factory: BaseProviderService → BkashIntegrationService, BulkSMSBDService, SMTPService
- Logos: provider `logo_url` values use local `/integrations/*` frontend assets, with `frontend/src/lib/integration-logos.ts` as a fallback for existing seeded DB rows

**Prescription Workflow:**
```python
# Immutable: draft → issued → voided
# Only drafts editable
# Items: medicine_id (DB) OR medicine_name (free-text)
# PDF: ReportLab/WeasyPrint
```

**Frontend Auth Flow:**
```typescript
// 1. Login — POST /api/v1/auth/login
const response = await authApi.login({ email, password });

// 2. If 2FA enabled, backend returns { requires_2fa: true } with tokens/user
//    omitted (not just falsy) — resubmit with the TOTP code to complete login
if (response.requires_2fa) {
  const result = await authApi.loginWith2FA({ email, password, totp_code });
  authStore.setTokens(result.tokens.access_token, result.tokens.refresh_token);
} else {
  authStore.setTokens(response.tokens.access_token, response.tokens.refresh_token);
}

// 3. API interceptor: auto-refresh on 401
```

---

## 5. CONVENTIONS

### Backend Rules

1. **NEVER bypass tenant isolation** - all queries MUST filter by `tenant_id`
2. **Use async/await** - all DB ops are async (`AsyncSession`)
3. **Soft-deactivate clinical data** - set the table's `is_active=False`, don't hard delete (some child records are intentionally hard-deleted — check the service method)
4. **Validate plan limits** - check `usage_tracking` before creating records
5. **Encrypt sensitive data** - Fernet for API keys/credentials
6. **Log integrations** - all SMS/email/payment logged with full payload
7. **Bilingual by default** - provide `_en` and `_bn` fields
8. **Immutable clinical records** - prescriptions/payments are append-only
9. **Enforce password security** - use `_validate_password_strength()` for all password inputs
10. **Invalidate sessions on security changes** - password change, email change, role change

### Frontend Rules

1. **TypeScript everywhere** - no implicit `any`
2. **Match backend schemas** - TypeScript interfaces = Pydantic models
3. **Client/Server components** - mark interactive with `"use client"`
4. **Error boundaries** - wrap features, show user-friendly errors
5. **Loading states** - always show skeletons/spinners
6. **Optimistic updates** - React Query mutations
7. **Responsive design** - test 375px (mobile), 768px (tablet), 1440px (desktop)
8. **Bilingual UI** - English/Bengali via next-intl
9. **Form validation** - Zod schemas matching backend
10. **Accessibility** - semantic HTML, ARIA, keyboard nav

---

## 6. REFERENCE

### URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger), http://localhost:8000/redoc
- **Database:** localhost:5432 (native PostgreSQL 16 + pgvector, not Dockerized)
- **Redis:** localhost:6379 (docker: `altcare_redis`)
- **MinIO:** http://localhost:9001 (minioadmin/minioadmin)

### Key Files

**Backend:**
- `app/main.py` - FastAPI app, middleware, router registration
- `app/core/dependencies.py` - Auth, CurrentUser, RBAC
- `app/core/security.py` - JWT, bcrypt, TOTP, Fernet
- `app/core/rate_limit.py` - Redis rate limiting
- `app/core/config.py` - Environment variables
- `alembic/versions/` - Migrations
- `tests/conftest.py` - Test fixtures
- `tests/integration/test_auth_security.py` - Security tests
- `tests/integration/test_rate_limiting.py` - Rate limit tests

**Frontend:**
- `app/layout.tsx` - Root layout
- `lib/api/client.ts` - Axios client, auth interceptors
- `stores/authStore.ts` - Zustand auth state
- `components/ui/` - shadcn/ui library
- `.env.local` - Environment variables

### Commands Cheatsheet

```bash
# Backend
uvicorn app.main:app --reload
alembic upgrade head
pytest --cov=app
black backend/app
ruff check backend/app

# Frontend
npm run dev
npm run build
npx playwright test

# Database
docker compose up -d
./scripts/run_seed.sh

# Celery
celery -A app.core.celery:celery_app worker --loglevel=info
```
