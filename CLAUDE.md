# AltCare - Multi-Tenant Alternative Medicine Platform

FastAPI + Next.js 16 SaaS for alternative medicine practitioners (Homeopathy, Ayurveda, Unani, Herbal) with row-level multi-tenancy.

---

## 1. PROJECT STATUS

**MVP v1.0 - PRODUCTION READY** 🚀

**Implemented:**
- Authentication (Login, 2FA, JWT, Sessions, Password Security) - Backend + Frontend ✅
- Patient Management (CRUD, Search, Tags, Diagnoses) - Backend + Frontend ✅
- Dashboard Analytics (Stats, Revenue, Demographics) - Backend + Frontend ✅
- Appointments (Scheduling, Visits) - Backend + Frontend ✅
- Multi-tenant isolation (100% secure, 16/16 tests passing) ✅
- Security hardening (Rate limiting, HTTP headers, Password complexity) ✅

**Backend:** 11 routed modules, 87 endpoints (+ `/`, `/health`, `/metrics`), 34 table models
**Frontend:** 110+ source files (auth, dashboard, patients, appointments, prescriptions, doctor profile, payments, integrations, medicines, symptoms)
**Security:** A (95/100), comprehensive auth security tests

**Last Verified:** 2026-05-22

**Security Features:**
- ✅ Password complexity enforcement (8+ chars, mixed case, numbers)
- ✅ Session invalidation on password change
- ✅ HTTP security headers (CSP, X-Frame-Options, HSTS)
- ✅ Redis-backed rate limiting (login, API, AI-specific tiers)
- ✅ JWT token validation (expiry, type checking, claim validation)
- ✅ 2FA/TOTP support with QR code generation

**Post-MVP (Backend Ready, Frontend Status):**
- Prescriptions (backend complete, **frontend complete** ✅ - list/detail/builder all done)
- Doctor Profile (backend complete, **frontend complete** ✅ - profile/degrees/trainings all done)
- Payments (backend complete, **frontend complete** ✅ - dashboard/transactions/invoices/toasts all done)
- Integrations (backend complete, **frontend complete** ✅ - provider marketplace/config wizard/logs all done)
- **Medicines** (backend complete ✅, **frontend complete** ✅ - CRUD/search/aliases/autocomplete all done)
- **Symptoms** (backend complete ✅, **frontend complete** ✅ - CRUD/search/aliases all done)
- AI Query Module (stub endpoint, plan-gated)

---

## 2. QUICK START

### First Time Setup

```bash
# 1. Start infrastructure
docker compose up -d

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
- Docker Compose (PostgreSQL, Redis, MinIO)
- Docker containers: `altcare_postgres`, `altcare_redis`, `altcare_minio`

---

## 4. ARCHITECTURE

### 4.1 Multi-Tenant Security (CRITICAL)

**Row-Level Isolation:**
```python
# Every tenant-scoped table has tenant_id
# Automatic scoping via ContextVar from JWT

# Flow:
# 1. JWT decoded → app/core/dependencies.py:get_current_user()
# 2. tenant_id extracted → tenant_id_ctx.set(tenant_id)
# 3. All queries auto-filter by tenant_id

# Platform users: tenant_id = NULL (admin, operator)
# Tenant users: tenant_id = <uuid> (doctor, receptionist)
```

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
- Claims: `sub` (user_id), `tenant_id`, `role`, `email`, `plan`
- Location: `app/core/security.py` (python-jose)

**2FA (TOTP):**
- Setup: Generate secret → QR code → verify code → enable
- Login: Password → TOTP code (if enabled)
- Libraries: `pyotp`, `qrcode`

**Password:** Bcrypt (12 rounds, passlib)
**Credentials:** Fernet encrypted (JSONB field: `tenant_integrations.credentials`)

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

**Rate Limiting:**
```python
# Redis-backed rate limiting middleware (app/main.py)
# Applied to:
# - /api/v1/auth/login: 10 req/min per IP
# - /api/v1/ai/query: 100 req/hour per user (configurable)
# - /api/v1/*: 100 req/min per IP (general API)

# Headers returned:
# X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After (on 429)

# Config (app/core/config.py):
RATE_LIMIT_PER_MINUTE = 100
RATE_LIMIT_LOGIN_PER_MINUTE = 10
RATE_LIMIT_AI_PER_HOUR = 100
RATE_LIMIT_WINDOW_SECONDS = 60
```

**Security Headers:**
```python
# HTTP security headers middleware (app/main.py)
# Applied to all responses:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Content-Security-Policy: (configurable)
# - Strict-Transport-Security: (production only, HSTS)

# Config:
SECURITY_HEADERS_ENABLED = True
SECURITY_HSTS_ENABLED = True
SECURITY_HSTS_MAX_AGE = 31536000
```

**Password Security:**
```python
# Password complexity validation (app/modules/auth/schemas.py)
def _validate_password_strength(password: str):
    # Requirements:
    # - Minimum 8 characters
    # - At least 1 uppercase letter
    # - At least 1 lowercase letter
    # - At least 1 number
    # Applied to: registration, password change, password reset
```

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
- Tenant-scoped: `tenant_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`
- Soft deletes: `deleted_at IS NULL` (never hard delete clinical data)
- Immutable: Prescriptions/payments are append-only (draft → issued → voided)
- Global vs Tenant: `is_global=true` (admin-curated) or tenant-specific

**Model Base Classes:**
```python
# app/shared/models/base.py
BaseModel → created_at, updated_at
BaseAuditModel → + created_by, updated_by, deleted_at
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
├── modules/               # Feature modules (87 total endpoints)
│   ├── auth/             # ✅ Login, refresh, 2FA, password change (12 endpoints)
│   ├── doctor/           # ✅ Profile, degrees, trainings (12 endpoints)
│   ├── patient/          # ✅ CRUD, search, tags, diagnoses (14 endpoints)
│   ├── appointments/     # ✅ Scheduling, visits (6 endpoints)
│   ├── prescription/     # ✅ CRUD, items, issue, void, PDF (8 endpoints)
│   ├── payment/          # ✅ Processing, bKash (12 endpoints)
│   ├── integration/      # ✅ SMS/Email providers (12 endpoints)
│   ├── dashboard/        # ✅ Analytics, stats (6 endpoints)
│   ├── ai/               # ✅ Stub endpoint, pro-plan gated (1 endpoint)
│   ├── medicine/         # ✅ CRUD, search, aliases, mappings (8 endpoints)
│   ├── symptom/          # ✅ CRUD, search, aliases (8 endpoints)
│   ├── library/          # 📋 Models exist, no routes
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
│   │   ├── medicines/    # ✅ Medicine library CRUD with autocomplete
│   │   ├── symptoms/     # ✅ Symptom library CRUD
│   │   └── settings/     # ✅ Integrations management
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
│   ├── medicine.ts       # ✅ NEW
│   └── symptom.ts        # ✅ NEW
└── stores/
    └── authStore.ts      # ✅ Zustand auth state
```

### 4.6 Prescription Builder (Frontend)

**Components:**
```typescript
// PrescriptionBuilder - Main form component
// - Patient selection (searchable)
// - Clinical info (diagnosis, notes, advice)
// - Medicine items builder (with autocomplete)
// - Draft/Issue workflow
// - Validation and error handling

// MedicineItemsBuilder - Dynamic medicine list
// - Medicine autocomplete with smart search
// - Auto-fill dosage guidance from database
// - Toggle between autocomplete and free-text
// - Add/Edit/Delete medicines
// - Required: name, dosage, frequency
// - Shows selected medicine details (indications, contraindications)

// MedicineAutocomplete - Smart search component
// - Type-ahead search with 300ms debouncing
// - Searches medicine names and aliases
// - Keyboard navigation (arrow keys, enter, escape)
// - Match rank scoring (name: 100%, alias: 80%)
// - Shows medicine details (system, potency, category)
// - Mobile-friendly dropdown
// - Optional: duration, quantity, instructions
// - Table view with modal dialog

// PatientSelector - Smart patient search
// - Real-time search (name, phone, code)
// - Autocomplete dropdown
// - Selected patient card with details
// - Clear selection
```

**Routes:**
- `/prescriptions` - List all prescriptions (filter by status)
- `/prescriptions/new` - Create new prescription
- `/prescriptions/[id]` - View prescription details
- `/prescriptions/[id]/edit` - Edit draft prescription

**Workflow:**
```typescript
// 1. Create Draft
const draft = await createPrescription({
  patient_id,
  diagnosis,
  doctors_notes,
  advice,
  items: [/* medicines */],
  status: 'draft'
})

// 2. Edit Draft (only drafts editable)
await updatePrescription(id, { diagnosis: '...' })
await addPrescriptionItem(id, { medicine_name: '...' })

// 3. Issue Prescription (becomes immutable)
await updatePrescription(id, { status: 'issued' })

// 4. Immutability enforced
// - Cannot update issued/voided prescriptions
// - Cannot add/delete items
// - Can only void
```

**Key Features:**
- Patient search with autocomplete
- Free-text medicine names (no DB dependency yet)
- Form validation (patient + ≥1 medicine required)
- Draft/Issue status workflow
- Immutability enforcement
- Responsive design
- TypeScript type safety

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

**Doctor Specialization:**
```python
# tenant.specializations = ['homeopathy', 'ayurveda']
# Medicines/books filtered:
WHERE system IN tenant.specializations OR is_global = true
```

**Integration Framework:**
- Providers: `integration_providers` (global catalog)
- Configs: `tenant_integrations` (credentials encrypted)
- Audit: `integration_logs` (request/response)
- Types: `sms`, `email`, `payment`
- Factory: BaseProviderService → BkashIntegrationService, BulkSMSBDService, SMTPService

**Prescription Workflow:**
```python
# Immutable: draft → issued → voided
# Only drafts editable
# Items: medicine_id (DB) OR medicine_name (free-text)
# PDF: ReportLab/WeasyPrint
```

**Frontend Auth Flow:**
```typescript
// 1. Login
const response = await authApi.login({ email, password });

// 2. If 2FA enabled
if (response.requires_2fa) {
  const tokens = await authApi.verify2FA({ user_id, code });
}

// 3. Store tokens
authStore.setTokens(tokens.access_token, tokens.refresh_token);

// 4. API interceptor: auto-refresh on 401
```

---

## 5. IMPLEMENTATION GUIDE

### 5.1 Add Backend Endpoint

```python
# 1. Schema (app/modules/<module>/schemas.py)
class PatientCreate(BaseModel):
    name: str
    phone: str
    
class PatientResponse(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    model_config = ConfigDict(from_attributes=True)

# 2. Router (app/modules/<module>/router.py)
from app.core.dependencies import RequireDoctor

@router.post("/", response_model=PatientResponse)
async def create_patient(
    data: PatientCreate,
    user: RequireDoctor,
    db: AsyncSession = Depends(get_db)
):
    patient = Patient(**data.dict(), tenant_id=user.tenant_id)
    db.add(patient)
    await db.commit()
    return patient

# 3. Register (app/main.py)
from app.modules.patient import router as patient_router
app.include_router(patient_router, prefix="/api/v1/patients", tags=["Patients"])
```

### 5.2 Database Migration

```bash
# 1. Auto-generate (REVIEW BEFORE APPLYING!)
alembic revision --autogenerate -m "Add table"

# 2. Review backend/alembic/versions/<hash>.py
# Check: data migrations, indexes, constraints, enum changes

# 3. Apply
alembic upgrade head

# 4. Rollback if needed
alembic downgrade -1
```

### 5.3 Add Frontend Feature

```typescript
// 1. API client (lib/api/patients.ts)
export const patientsApi = {
  list: async (params?: { search?: string }) => {
    const { data } = await apiClient.get('/api/v1/patients', { params });
    return data;
  },
  create: async (patient: PatientCreate) => {
    const { data } = await apiClient.post('/api/v1/patients', patient);
    return data;
  },
};

// 2. React Query hook (lib/hooks/usePatients.ts)
export function usePatients(search?: string) {
  return useQuery(['patients', search], () => patientsApi.list({ search }));
}

export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation(patientsApi.create, {
    onSuccess: () => queryClient.invalidateQueries(['patients']),
  });
}

// 3. Page component (app/(dashboard)/patients/page.tsx)
"use client";

export default function PatientsPage() {
  const { data, isLoading, error } = usePatients();
  
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage />;
  
  return <PatientList patients={data} />;
}

// 4. TypeScript types (match backend schemas EXACTLY)
export interface PatientResponse {
  id: string;
  name: string;
  phone: string;
  tenant_id: string;
  created_at: string;
}

export interface PatientCreate {
  name: string;
  phone: string;
}
```

### 5.4 Seed Data

```bash
cd backend && ./scripts/run_seed.sh
```

Seeds:
- Bangladesh geographic data (8 divisions, 64 districts, upazilas)
- Integration providers (11: SMS, Email, Payment)
- UI translations (80+ English/Bengali)
- Sample tenants/users (dev only)

---

## 6. TROUBLESHOOTING

### Backend

**pgvector missing:**
```bash
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
# Or: uvicorn app.main:app --reload --port 8001
```

**Migration stuck:**
```bash
alembic current && alembic history

# Reset (DEV ONLY - destroys data):
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

**Test DB errors:**
Tests use `altcare_test` database (auto-created by conftest.py). Ensure PostgreSQL running.

### Frontend

**CORS errors:**
Check `backend/.env`: `CORS_ORIGINS=["http://localhost:3000"]`

**API connection refused:**
Check `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Port 3000 in use:**
```bash
lsof -ti:3000 | xargs kill -9
# Or: PORT=3001 npm run dev
```

**Module not found:**
```bash
cd frontend
rm -rf .next node_modules
npm install && npm run dev
```

**TypeScript errors:**
Update `frontend/src/types/` to match backend schemas. Run `npm run build`.

---

## 7. CONVENTIONS

### Backend Rules

1. **NEVER bypass tenant isolation** - all queries MUST filter by `tenant_id`
2. **Use async/await** - all DB ops are async (`AsyncSession`)
3. **Soft delete clinical data** - set `deleted_at`, never hard delete
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

## 8. REFERENCE

### URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger), http://localhost:8000/redoc
- **Database:** localhost:5432 (docker: `altcare_postgres`)
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
