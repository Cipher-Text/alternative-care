# AltCare — Alternative Medicine Practice Management System

> A multi-tenant SaaS platform for Homeopathy, Ayurveda, Unani, and Herbal practitioners to manage patients, prescriptions, payments, clinical knowledge, and AI-assisted reference — all in one place.

---

## Table of Contents

- [Overview](#overview)
- [Screenshots & Prototypes](#screenshots--prototypes)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Core Modules](#core-modules)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Authentication & Security](#authentication--security)
- [Multi-Tenancy](#multi-tenancy)
- [AI / RAG Pipeline](#ai--rag-pipeline)
- [Pricing Plans](#pricing-plans)
- [Development Phases](#development-phases)
- [User Roles](#user-roles)
- [Deployment](#deployment)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Folder Structure](#folder-structure)

---

## Overview

AltCare is a full-featured **clinic operating system** built specifically for alternative medicine practitioners. It goes beyond simple record-keeping — it combines patient management, prescription generation, a curated medicine knowledge base, a medical book reader, symptom-based search, and a RAG-powered AI assistant grounded in classical texts.

**Key differentiators:**
- **Multi-specialization support** — practitioners can work with 1-4 systems (Homeopathy, Ayurveda, Unani, Herbal), with resources auto-filtered based on their active specializations
- **Bilingual interface (English/Bengali)** — complete UI in both languages with seamless switching, Bengali medicine names, and localized content for Bangladesh market
- **Bangladesh-focused location system** — structured Division → District → Upazila hierarchy with Bengali names and geospatial data for precise clinic and patient location tracking
- **Integrated communications & payments** — built-in SMS/Email providers (Twilio, Banglalink, Robi, SendGrid) and payment gateways (bKash, Nagad, Rocket, Stripe)
- **Complete audit trail** — every SMS, email, and payment transaction logged with full request/response details

The platform is designed as a **multi-tenant SaaS** — each doctor or clinic operates in a fully isolated data space under a shared infrastructure. It is built to evolve incrementally: from an MVP clinic tool in Phase 1 through to a comprehensive knowledge and AI intelligence platform by Phase 4.

---

## Screenshots & Prototypes

> UI prototypes located in [`/mock/`](./mock/) folder
> Open any HTML file in a browser — no build step, no dependencies required.

**Available mockups:**
- **[Admin View](./mock/admin-view.html)** — Platform administration interface for admins and operators
- **[Doctor View](./mock/doctor-view.html)** — Complete clinic management system for practitioners

The prototypes are complete single-file HTML/CSS/JS mocks covering all major screens. They are used for stakeholder review, client feedback, and as front-end specifications for the production build.

**Screens included:**

| Screen         | What it shows                                                                                                                                                                                                  |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dashboard      | KPI cards, monthly patient calendar with load heatmap, booked appointments, patient growth chart, most common diagnoses, most prescribed medicines, recent patients with diagnosis column, upcoming follow-ups |
| Patients       | Searchable/filterable table with diagnosis column, special case / chronic / treatment / allergy tags, slide-out patient detail panel with full visit timeline                                                  |
| Prescriptions  | Prescription builder with medicine selection, dosage/duration, doctor's notes, live PDF preview                                                                                                                |
| Payments       | Revenue KPIs, transaction table, invoice tracking, bKash/Nagad/Rocket/cash/card support                                                                                                                        |
| Medicines      | Searchable medicine database across all traditions with symptom tags                                                                                                                                           |
| Symptom search | Multi-tradition symptom-to-remedy matching with match percentage                                                                                                                                               |
| Library        | Medical book browser with reading progress bars                                                                                                                                                                |
| AI Assistant   | RAG-based clinical reference chat with quick prompts and disclaimer                                                                                                                                            |
| Pricing & Plan | Free / Plus / Pro with monthly/annual billing toggle and full feature comparison table                                                                                                                         |
| Settings       | Doctor profile with academic degrees and training/certifications, clinic info, specializations, subscription management, integration setup (SMS/Email/Payment)                                                  |

---

## Tech Stack

### Backend

| Technology           | Purpose                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------- |
| **Python 3.12**      | Primary backend language                                                                |
| **FastAPI**          | Async REST API framework — auto OpenAPI docs, Pydantic validation, dependency injection |
| **SQLAlchemy 2.0**   | Async ORM                                                                               |
| **Alembic**          | Database migrations                                                                     |
| **Pydantic v2**      | Request/response validation and settings management                                     |
| **passlib (bcrypt)** | Password hashing                                                                        |
| **python-jose**      | JWT creation and verification                                                           |
| **pyotp**            | Two-factor authentication (2FA) with TOTP                                               |
| **Celery**           | Background task queue — PDF generation, emails, SMS, AI embedding jobs                  |
| **WeasyPrint**       | Prescription and invoice PDF generation                                                 |
| **ebooklib**         | EPUB parsing for the book library                                                       |
| **cryptography**     | Fernet encryption for integration credentials (API keys, merchant secrets)              |
| **structlog**        | Structured JSON logging for production observability                                    |
| **slowapi**          | Rate limiting middleware with Redis backend                                             |
| **Babel**            | Internationalization (i18n) for English/Bengali API responses                           |

### Frontend

| Technology                 | Purpose                                               |
| -------------------------- | ----------------------------------------------------- |
| **Next.js 14**             | React framework with App Router and Server Components |
| **Tailwind CSS**           | Utility-first styling                                 |
| **shadcn/ui**              | Accessible, unstyled component library                |
| **React Query (TanStack)** | Server state management, caching, background refetch  |
| **next-intl**              | Internationalization (i18n) for English/Bengali       |

### Infrastructure

| Technology                  | Purpose                                                                   |
| --------------------------- | ------------------------------------------------------------------------- |
| **PostgreSQL 16**           | Primary relational database                                               |
| **pgvector**                | Vector embeddings stored inside PostgreSQL — no separate vector DB needed |
| **Redis**                   | Cache, session store, Celery task broker                                  |
| **MinIO**                   | S3-compatible file storage for EPUBs, PDFs, and attachments               |
| **Docker + Docker Compose** | Containerised local and production deployment                             |
| **Caddy**                   | Reverse proxy with automatic HTTPS                                        |

### AI Layer

| Technology     | Purpose                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| **LangChain**  | RAG pipeline — document loading, chunking, retrieval chain orchestration |
| **OpenAI API** | Embeddings (`text-embedding-3-small`) and completions (`gpt-4o-mini`, `gpt-4o`) |
| **pgvector**   | Cosine similarity search over embedded book sections                     |

**Cost optimization:**
- Use `gpt-4o-mini` for simple queries and embeddings (80% cheaper)
- Reserve `gpt-4o` for complex clinical reasoning
- Cache embeddings aggressively (books are static)
- Set monthly budget limits via OpenAI dashboard

### Security & Monitoring

| Technology                      | Purpose                                                    |
| ------------------------------- | ---------------------------------------------------------- |
| **Sentry**                      | Error tracking, performance monitoring, release tracking   |
| **Grafana + Prometheus**        | Metrics dashboards — API latency, DB queries, queue depth  |
| **slowapi + Redis**             | Distributed rate limiting (per-user, per-endpoint)         |
| **structlog**                   | Structured logging with correlation IDs                    |
| **pg_stat_statements**          | PostgreSQL query performance analysis                      |
| **OWASP security headers**      | CSP, HSTS, X-Frame-Options via FastAPI middleware         |

### Testing

| Technology              | Purpose                                              |
| ----------------------- | ---------------------------------------------------- |
| **pytest**              | Unit and integration testing framework               |
| **pytest-asyncio**      | Async test support for FastAPI routes               |
| **pytest-cov**          | Code coverage reporting                              |
| **httpx**               | FastAPI test client (async)                          |
| **faker**               | Generate realistic test data (patients, medicines)   |
| **Vitest**              | Frontend unit testing (faster than Jest)             |
| **React Testing Library** | Component testing with user-centric queries        |
| **Playwright**          | End-to-end testing for critical flows                |

**Critical test coverage:**
- Multi-tenant data isolation (tenants cannot access each other's data)
- Auth flows (login, token refresh, password reset)
- Payment webhook handling
- Prescription PDF generation
- AI query sanitization and rate limiting

### Payment Integration

| Provider         | Markets      | Purpose                                      |
| ---------------- | ------------ | -------------------------------------------- |
| **SSLCommerz**   | Bangladesh   | Payment aggregator (bKash, Nagad, Rocket, cards) |
| **Stripe**       | International| Credit/debit cards, subscriptions worldwide  |

**Implementation notes:**
- SSLCommerz handles PCI compliance for Bangladesh
- Never store raw card numbers — use tokenization
- All transactions logged in `integration_logs` table with full audit trail
- Webhook signature verification required (prevent fraud)

### Communication Services

| Provider      | Type  | Purpose                                           |
| ------------- | ----- | ------------------------------------------------- |
| **Twilio**    | SMS   | Primary SMS provider (99%+ delivery, works in BD) |
| **Banglalink** | SMS   | Secondary provider (local rates, backup)          |
| **SendGrid**  | Email | Transactional emails with DMARC/SPF/DKIM         |
| **AWS SES**   | Email | Backup email provider (cost-effective scaling)    |

**Fallback strategy:**
- Primary provider fails → automatic retry with secondary
- Exponential backoff via Celery (1s, 5s, 30s, 5m)
- Dead letter queue for permanent failures

---

## Architecture

AltCare is structured as a **modular monolith** — one FastAPI application with cleanly separated feature packages. This gives the development speed of a monolith with the internal boundaries needed to extract individual services later if scale demands it.

```
┌──────────────────────────────────────────────────────────┐
│                        CLIENTS                           │
│            Next.js 14 (App Router) + Tailwind            │
│            shadcn/ui components + React Query            │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTPS / REST + JSON
┌───────────────────────────▼──────────────────────────────┐
│                       API LAYER                          │
│                 FastAPI (Python 3.12)                    │
│             Uvicorn + Gunicorn (async workers)           │
│                                                          │
│  auth │ doctor │ patient │ prescription │ payment        │
│  medicine │ library │ ai │ notification                  │
└──────┬──────────┬──────────┬─────────────┬───────────────┘
       │          │          │             │
 ┌─────▼──┐ ┌────▼────┐ ┌───▼───┐ ┌──────▼────────────┐
 │Postgres│ │  Redis  │ │ MinIO │ │  Celery Workers   │
 │+pgvect.│ │Cache +  │ │ Files │ │  PDF, Email,      │
 │        │ │  Queue  │ │ EPUBs │ │  Embeddings       │
 └────────┘ └─────────┘ └───────┘ └───────────────────┘
```

### Backend module structure

```
app/
  main.py                    ← FastAPI app init, router registration, CORS, middleware
  core/
    config.py                ← Settings via pydantic-settings (.env)
    database.py              ← Async SQLAlchemy engine + session factory
    security.py              ← JWT encode/decode, bcrypt hashing, 2FA (pyotp)
    dependencies.py          ← get_db, get_current_user, require_role, tenant scope
    logging.py               ← structlog configuration
    monitoring.py            ← Sentry init, Prometheus metrics
    rate_limit.py            ← slowapi rate limiter with Redis backend
  modules/
    auth/                    ← Login, register, token refresh
    doctor/                  ← Profile, clinic setup, subscription
    patient/                 ← Patient CRUD, tags, diagnoses, attachments
    prescription/            ← Builder, medicine items, PDF export
    payment/                 ← Fees, invoices, revenue reports
    medicine/                ← Medicine DB, symptom mapping, search
    library/                 ← EPUB upload, chapter parsing, reading progress
    ai/                      ← RAG pipeline, embedding, retrieval, chat
    notification/            ← Email and SMS dispatch (async via Celery)
  shared/
    models/
      base.py                ← BaseAuditModel with tenant_id, timestamps, created_by
    schemas/                 ← Shared Pydantic response/request models
    exceptions.py            ← Custom HTTP exception handlers
    pagination.py            ← Reusable paginated response wrapper
alembic/                     ← Database migration scripts
tests/
  unit/
  integration/
pyproject.toml
docker-compose.yml
.env.example
```

---

## Core Modules

### Auth

JWT-based authentication using `passlib` (bcrypt) for password hashing and `python-jose` for token management. Self-issued JWTs embed `user_id`, `tenant_id`, `role`, and `plan` — no external auth service required. Role guards are reusable FastAPI dependencies injected per route.

### Doctor & Clinic Management

Registration with admin approval flow. Doctor profile stores specialisation (Homeopathy / Ayurveda / Unani / Herbal), license number, and clinic details. Doctors can add multiple academic degrees (from universities/colleges) and professional training/certifications with verification support. Subscription plan is stored on the tenant record and enforced at the service layer on every write operation.

### Patient Management

Full patient profiles with visit history, chief complaints, examination notes, follow-up scheduling, and file attachments. Flexible tag system: special case flags, chronic condition markers, treatment protocol tags (Panchakarma, Rasayana, Constitutional Rx), and allergy/sensitivity notes. Diagnosis records store free-text description and optional ICD code.

### Prescription System

Structured prescription builder with medicine selection from the database or free-text entry (for medicines not yet in the DB — `medicine_id` is nullable). Stores dosage, frequency, duration, and doctor's notes per item. Asynchronous PDF generation via Celery + WeasyPrint. Full prescription history per patient per visit.

### Payment System

Consultation fee recording with support for bKash, Nagad, cash, and card. Invoice generation with PDF export. Payment status tracking (paid / pending / overdue). Monthly revenue reports with per-day breakdown.

### Medicine Database

Curated medicine records across all four traditions. Each entry stores name, system, category, description, symptom tags, and dosage guidance. Supports both global admin-curated records (`is_global = true`) and tenant-specific additions (`is_global = false`).

### Symptom-Based Search

Input one or more symptoms, get ranked medicine matches grouped by tradition with match score and modality notes. Full-text search via PostgreSQL `tsvector` on symptom tags and descriptions. Assists during consultation — never replaces clinical judgment.

### Book Library & Reader

EPUB upload stored in MinIO. Server-side chapter and section extraction via `ebooklib`. Parsed content stored in PostgreSQL for fast retrieval. In-browser reader with per-user reading progress, bookmarks, and highlights.

### AI Assistant (RAG)

Books are chunked into overlapping sections, embedded via OpenAI, and stored in pgvector. At query time, the top-k most relevant sections are retrieved by cosine similarity and assembled into a grounded prompt. Every response includes the source section reference. The AI never makes prescriptive medical decisions.

### Notifications & Integrations

**Integration framework** with pluggable SMS, Email, and Payment providers. Doctors configure their preferred providers (Banglalink SMS, SendGrid Email, bKash Payment) with encrypted credentials. All transactions are logged with full audit trail.

**Notification triggers:** Follow-up reminders, prescription PDF ready, payment receipt, admin approval.

**Supported providers:**
- **SMS:** Twilio, Banglalink, Robi, Grameenphone
- **Email:** SMTP, SendGrid, AWS SES
- **Payment:** bKash, Nagad, Rocket, Upay (Bangladesh), Stripe, Razorpay (International)

---

## Database Schema

> **Full schema documentation:** [DATABASE.md](./DATABASE.md)

### Entity relationships

```
TENANTS (clinics / doctors)
  ├─ specializations[]                    — 1-4 medical systems
  ├─ USERS (doctors, receptionists)
  ├─ TENANT_INTEGRATIONS                  — encrypted SMS/Email/Payment credentials
  │    └─ INTEGRATION_LOGS                — transaction audit trail
  └─ PATIENTS
       ├─ PATIENT_TAGS                    (special_case, chronic, treatment, allergy)
       ├─ PATIENT_DIAGNOSES               (description, ICD code, visit reference)
       └─ VISITS
            ├─ PRESCRIPTIONS
            │    └─ PRESCRIPTION_ITEMS → MEDICINES (filtered by specializations)
            └─ PAYMENTS                   (links to integration_logs for digital payments)
                 └─ INVOICES

MEDICINES (global + tenant-specific, filtered by doctor's specializations)
  └─ MEDICINE_SYMPTOMS                    (symptom mapping, many-to-many)

BOOKS (filtered by doctor's specializations)
  └─ CHAPTERS
       └─ SECTIONS
            └─ EMBEDDINGS                 (pgvector — 1536 dimensions)

READING_PROGRESS, BOOKMARKS, HIGHLIGHTS

PLATFORM LEVEL (no tenant_id):
  USERS (admins, operators)
  INTEGRATION_PROVIDERS                   (SMS/Email/Payment catalog)
```

### Key design decisions

- **29 tables total** — core clinic (14) + doctor credentials (2) + geographic data (3) + knowledge base (6) + integrations (3) + usage tracking (1)
- Every entity carries `tenant_id` — all queries are scoped, cross-tenant data access is architecturally impossible
- **Multi-specialization filtering** — medicines, books, and AI responses auto-filter by doctor's `specializations[]`
- **Platform vs tenant users** — admins/operators have `tenant_id = NULL`, doctors/receptionists are tenant-scoped
- `prescription_items.medicine_id` is nullable — allows free-text medicine entry
- `medicines.is_global` and `books.is_global` — distinguishes admin-curated content from tenant additions
- All entities extend `BaseAuditModel` — `created_at`, `updated_at`, `created_by`, `updated_by` populated automatically
- **Integration credentials encrypted** at application level using Fernet before storage
- Embeddings stored in PostgreSQL via pgvector — no separate vector database needed

---

## API Design

REST, resource-oriented, versioned under `/api/v1/`. FastAPI auto-generates interactive Swagger docs at `/docs` and ReDoc at `/redoc`.

### Response envelope

All responses follow a consistent structure:

```json
{
  "data": {},
  "meta": {
    "page": 1,
    "size": 20,
    "total": 284
  },
  "errors": []
}
```

### Key endpoints

| Method | Endpoint                          | Description                           |
| ------ | --------------------------------- | ------------------------------------- |
| POST   | `/api/v1/auth/register`           | Doctor registration                   |
| POST   | `/api/v1/auth/login`              | Login → returns JWT                   |
| POST   | `/api/v1/auth/refresh`            | Refresh access token                  |
| GET    | `/api/v1/patients`                | List patients (paginated, filterable) |
| POST   | `/api/v1/patients`                | Create patient                        |
| GET    | `/api/v1/patients/{id}`           | Patient detail with visit history     |
| PATCH  | `/api/v1/patients/{id}/tags`      | Add / remove patient tags             |
| POST   | `/api/v1/visits`                  | Create visit                          |
| POST   | `/api/v1/prescriptions`           | Create prescription                   |
| GET    | `/api/v1/prescriptions/{id}/pdf`  | Download PDF (binary stream)          |
| GET    | `/api/v1/medicines`               | Search medicines                      |
| GET    | `/api/v1/medicines/symptoms`      | Symptom-based remedy search           |
| POST   | `/api/v1/payments`                | Record payment                        |
| GET    | `/api/v1/invoices/{id}/pdf`       | Download invoice PDF                  |
| POST   | `/api/v1/books`                   | Upload EPUB                           |
| GET    | `/api/v1/books/{id}/chapters`     | List parsed chapters                  |
| PATCH  | `/api/v1/books/{id}/progress`     | Update reading progress               |
| POST   | `/api/v1/ai/query`                | RAG query with citations              |
| GET    | `/api/v1/dashboard/summary`       | KPI cards data                        |
| GET    | `/api/v1/dashboard/calendar`      | Monthly patient calendar data         |
| GET    | `/api/v1/dashboard/top-diagnoses` | Most common diagnoses chart           |
| GET    | `/api/v1/dashboard/top-medicines` | Most prescribed medicines chart       |
| GET    | `/api/v1/integrations/providers`  | List available integration providers  |
| POST   | `/api/v1/integrations`            | Configure tenant integration          |
| POST   | `/api/v1/integrations/{id}/test`  | Test integration credentials          |
| GET    | `/api/v1/integrations/logs`       | Integration transaction history       |

Tenant resolution happens from the JWT `tenant_id` claim — never from the URL. All list endpoints accept `?page=`, `?size=`, and `?q=` query params.

---

## Authentication & Security

AltCare uses a **self-contained JWT authentication system** built with FastAPI-native libraries. No external auth service is required — keeping infrastructure lean and the team's operational burden minimal.

### Libraries

```
passlib[bcrypt]              — secure password hashing
python-jose[cryptography]    — JWT signing (HS256) and verification
```

### JWT payload

```json
{
  "sub": "user-uuid",
  "tenant_id": "clinic-uuid",
  "role": "doctor",
  "email": "dr.rahman@altcare.health",
  "plan": "pro",
  "exp": 1744000000
}
```

Role and tenant context are embedded in every token. No database lookup is needed per request for authorization — the middleware extracts everything from the JWT.

### Route protection pattern

```python
# Open route — any authenticated user
@router.get("/patients")
async def list_patients(user = Depends(get_current_user)):
    ...

# Role-restricted route
@router.post("/medicines")
async def create_medicine(user = Depends(require_role("doctor", "admin"))):
    ...

# Plan-restricted route
@router.post("/ai/query")
async def ai_query(user = Depends(require_plan("pro"))):
    ...
```

### When to adopt Keycloak

Migrate to Keycloak only when a concrete need arises: an enterprise client requires SSO (Google/Microsoft login), SAML federation, or a compliance audit demands centralised IAM. The JWT structure is identical — migration is a configuration change, not a code rewrite.

---

## Multi-Tenancy

AltCare uses a **shared database, tenant-per-row** model. Every table carries a `tenant_id` column. A FastAPI middleware extracts `tenant_id` from the JWT on every request and sets it on a Python `ContextVar`. All repository queries filter by this context automatically.

```python
# Every service layer query is automatically scoped
async def list_patients(db: AsyncSession) -> list[Patient]:
    result = await db.execute(
        select(Patient)
        .where(Patient.tenant_id == tenant_id_ctx.get())
        .order_by(Patient.created_at.desc())
    )
    return result.scalars().all()
```

Cross-tenant data access is architecturally impossible — a missing tenant filter returns zero rows, not another clinic's data.

**Future migration path:** If a large enterprise client requires full data isolation, the schema can be migrated to PostgreSQL schema-per-tenant with minimal application changes.

---

## AI / RAG Pipeline

```
INGEST  (background Celery job — runs once per book upload)

  EPUB upload
    └─ ebooklib → extract chapters and sections
    └─ LangChain RecursiveCharacterTextSplitter
         chunk_size = 800 tokens, chunk_overlap = 100 tokens
    └─ OpenAI text-embedding-3-small (1536 dimensions)
    └─ Store chunks in pgvector
         columns: book_id, section_id, embedding, text, metadata


QUERY  (synchronous — runs per AI assistant message)

  User question
    └─ Embed question → OpenAI text-embedding-3-small
    └─ pgvector cosine similarity search → top 5 sections
    └─ Assemble grounded prompt:
         System: "You are a clinical reference assistant for alternative
                  medicine. Answer only from the provided source sections.
                  Always cite the book title and section.
                  Never make prescriptive medical decisions."
         Context: [5 retrieved sections with citations]
         User question: [...]
    └─ OpenAI gpt-4o → structured response
    └─ Return: { answer, sources: [ { book, chapter, section } ] }
```

### Guardrails

- Responses are always grounded in retrieved source text — no hallucination
- Every response cites the source section (book + chapter)
- The system prompt explicitly prohibits prescriptive advice
- A clinical disclaimer is displayed on every AI response in the UI
- AI query count is tracked per tenant per month and enforced per subscription plan (Pro: 200 / month)

---

## Pricing Plans

| Feature                       | Free       | Plus         | Pro                 |
| ----------------------------- | ---------- | ------------ | ------------------- |
| Patients                      | 30         | 500          | Unlimited           |
| Prescriptions                 | 10 / month | Unlimited    | Unlimited           |
| PDF prescription export       | —          | ✓            | ✓                   |
| Invoice generation            | —          | ✓            | ✓                   |
| Revenue reports & analytics   | —          | —            | ✓                   |
| Medicine database             | Read-only  | ✓            | ✓                   |
| Symptom search                | —          | ✓            | ✓                   |
| Book library                  | —          | 5 books      | Unlimited + upload  |
| AI assistant                  | —          | —            | 200 queries / month |
| Assistant / receptionist seat | —          | —            | 1 included          |
| Support                       | Email      | Email + chat | Priority            |
| **Monthly price**             | ৳0         | ৳799         | ৳1,799              |
| **Annual price**              | ৳0         | ৳639 / mo    | ৳1,439 / mo         |

All paid plans include a **14-day free trial**, no credit card required. On downgrade, existing records are never deleted — they become read-only until the account is within plan limits.

---

## Development Phases

### Phase 1 — Core clinic MVP `current focus`

Doctor registration with multi-specialization selection (1-4 systems), patient CRUD with visit history and tags, prescription builder with PDF export, payment tracking and invoice generation, dashboard with KPI cards, patient calendar, and analytics charts. Integration framework setup (SMS/Email/Payment provider configuration).

**Deliverable:** A working clinic management tool a real practitioner can use every day, with integrated communications and payment processing.

### Phase 2 — Knowledge base

Medicine database with tradition categorisation and symptom tags (filtered by doctor's specializations), symptom-to-medicine mapping, symptom search endpoint, search integrated directly into the prescription builder. A Homeopathy-only doctor sees only homeopathic medicines; a multi-system practitioner sees all their chosen traditions.

**Deliverable:** A doctor can search by symptom during consultation and add matched medicines to a prescription in one click, with results automatically filtered to their practice areas.

### Phase 3 — Book library

EPUB upload and MinIO storage, server-side chapter/section parsing via `ebooklib`, in-browser reader with progress tracking, per-user bookmarks and highlights, reading progress widget on dashboard.

**Deliverable:** A doctor can read Organon of Medicine or Charaka Samhita inside the platform with progress saved across sessions.

### Phase 4 — AI / RAG

Embedding pipeline (Celery job triggered on book upload), pgvector storage, cosine similarity retrieval, grounded prompt assembly with citations, AI assistant UI, per-tenant query count tracking, plan enforcement.

**Deliverable:** A doctor can ask "What are the Ayurvedic remedies for Vata-induced fatigue?" and receive a grounded answer citing the exact section of Charaka Samhita.

---

## User Roles

| Role                             | Scope         | Capabilities                                                                                                                   |
| -------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Platform Admin**               | Platform-wide | Approve doctor registrations, manage global medicines/books, platform analytics, integration provider catalog                  |
| **Platform Operator**            | Platform-wide | Admin's assistant — support doctor approvals, content moderation, handle support tickets                                       |
| **Doctor / Practitioner**        | Tenant-scoped | Full patient & prescription management, payments, symptom search, library, AI assistant (resources filtered by specializations) |
| **Receptionist / Assistant**     | Tenant-scoped | Doctor's assistant — patient management, appointment scheduling, payment recording, invoice generation                         |
| **Patient** _(future — Phase 5)_ | Self-only     | View own prescriptions and visit history, access educational content                                                           |

**Role hierarchy:**
- **Platform users** (Admin, Operator): No `tenant_id`, can see all clinics
- **Tenant users** (Doctor, Receptionist): Scoped to their clinic via `tenant_id`
- Doctor creates the tenant and can add receptionist seats (Pro plan: 1 included)

---

## Deployment

### Local development

```bash
# Clone and configure
git clone https://github.com/your-org/altcare.git
cd altcare
cp .env.example .env        # fill in SECRET_KEY, OPENAI_API_KEY, INTEGRATION_ENCRYPTION_KEY, DB passwords

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Access points:
#   API + Swagger docs  →  http://localhost:8000/docs
#   Frontend            →  http://localhost:3000
#   MinIO console       →  http://localhost:9001
```

### Production (single VPS — recommended starting point)

```
Services (Docker Compose):
  caddy       — reverse proxy + automatic HTTPS (ports 80 / 443)
  api         — FastAPI, Uvicorn, 4 async workers
  worker      — Celery worker for PDF, email, and embedding jobs
  frontend    — Next.js standalone build
  postgres    — PostgreSQL 16 with pgvector extension
  redis       — cache + Celery broker + rate limiting
  minio       — file storage
  prometheus  — metrics collection
  grafana     — monitoring dashboards

Recommended minimum VPS:
  4 vCPU / 8 GB RAM / 100 GB SSD
  Estimated cost: $25–40 / month (DigitalOcean, Hetzner, Contabo)
  Comfortable capacity: 50–200 concurrent clinic users

Environment variables (.env):
  DATABASE_URL, REDIS_URL, MINIO_URL
  SECRET_KEY (JWT signing)
  OPENAI_API_KEY
  SENTRY_DSN
  INTEGRATION_ENCRYPTION_KEY (Fernet)
  SSLCOMMERZ_STORE_ID, SSLCOMMERZ_STORE_PASS
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
  SENDGRID_API_KEY
```

### Scaling path (when needed)

**Phase 1 (500+ users):**
1. Move PostgreSQL to a managed database (DigitalOcean Managed PG, Neon, Supabase)
2. Move Redis to a managed instance (Redis Cloud, AWS ElastiCache)
3. Add CDN (Cloudflare) for static assets and Next.js pages
4. Horizontal scaling: 2-3 API containers behind Caddy load balancer

**Phase 2 (2,000+ users):**
1. Move MinIO to Cloudflare R2 or AWS S3 — one config line change, same boto3 SDK
2. Separate Celery workers by task type:
   - `worker-pdf` — prescription/invoice generation
   - `worker-email` — email sending
   - `worker-ai` — embedding and RAG queries
3. Add read replicas for PostgreSQL (reporting queries)
4. Implement query caching layer (Redis + TTL)

**Phase 3 (10,000+ users):**
1. Migrate to Kubernetes (GKE, EKS, or DigitalOcean Kubernetes)
2. Implement microservices extraction:
   - Auth service (if switching to Keycloak)
   - AI service (separate deployment with GPU for fine-tuning)
   - Payment service (PCI compliance isolation)
3. Add message queue (RabbitMQ or Kafka) for event-driven architecture
4. Multi-region deployment (Bangladesh + India)

### Production Checklist

**Before launch:**
- [ ] Enable Sentry error tracking
- [ ] Set up Grafana dashboards (API latency, DB queries, Celery queue depth)
- [ ] Configure rate limiting (per-user, per-endpoint)
- [ ] Set up automated backups (PostgreSQL daily, MinIO weekly)
- [ ] Enable HTTPS with Caddy automatic certificates
- [ ] Configure CORS (only allow your domain)
- [ ] Set up monitoring alerts (Prometheus Alertmanager)
- [ ] Run security audit (`pip-audit`, OWASP headers check)
- [ ] Load testing (k6 or Locust — target 100 concurrent users)
- [ ] Test multi-tenant data isolation (critical!)
- [ ] Configure log aggregation (Papertrail or Loki)
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Document incident response plan
- [ ] Set OpenAI API budget limits ($500/month initially)
- [ ] Configure database connection pooling (20 connections)
- [ ] Enable PostgreSQL slow query logging (> 100ms)

**Security hardening:**
- [ ] Change default PostgreSQL/Redis passwords
- [ ] Enable UFW firewall (only ports 80, 443, 22 open)
- [ ] Configure fail2ban (SSH brute force protection)
- [ ] Set up SSH key-only authentication (disable password login)
- [ ] Enable automatic security updates (unattended-upgrades)
- [ ] Configure DMARC/SPF/DKIM for email domain
- [ ] Implement webhook signature verification (SSLCommerz, Stripe)
- [ ] Enable PostgreSQL SSL connections
- [ ] Rotate encryption keys quarterly (INTEGRATION_ENCRYPTION_KEY)
- [ ] Set up WAF rules (Cloudflare if using CDN)

---

## Roadmap

> **Full roadmap:** [ROADMAP.md](./ROADMAP.md)

**Timeline:** 12 months from MVP to Full Platform

| Phase | Timeline | Status |
|-------|----------|--------|
| **Phase 1: Core Clinic MVP** | 12 weeks (Apr-Jun 2026) | 🔄 In Progress |
| **Phase 2: Knowledge Base** | 8 weeks (Jul-Aug 2026) | 📋 Planned |
| **Phase 3: Book Library** | 10 weeks (Sep-Nov 2026) | 📋 Planned |
| **Phase 4: AI/RAG Intelligence** | 12 weeks (Dec 2026-Feb 2027) | 📋 Planned |
| **Phase 5: Patient Portal** | 8 weeks (Q3 2027) | 💡 Future |

**Key Milestones:**
- ✅ UI mockups completed
- ✅ Database schema designed
- 🔄 Backend foundation (FastAPI + SQLAlchemy)
- 📋 Beta doctor recruitment (target: 10 doctors)
- 📋 MVP launch: July 1, 2026

**Success Metrics (Year 1):**
- 50+ active paying clinics
- ৳2.5L+ MRR (Monthly Recurring Revenue)
- 70% retention rate
- <5% monthly churn

See [ROADMAP.md](./ROADMAP.md) for detailed week-by-week breakdown, team scaling, infrastructure evolution, and go-to-market strategy.

---

## Project Status

| Component                     | Status                                            |
| ----------------------------- | ------------------------------------------------- |
| UI prototypes                 | ✅ Complete — Admin + Doctor views in `/mock/`    |
| System architecture           | ✅ Defined                                        |
| Database schema               | ✅ Designed — 30 tables (see DATABASE.md)         |
| API structure                 | ✅ Defined                                        |
| Backend — FastAPI             | 🔄 In progress (Phase 1)                          |
| Frontend — Next.js            | 🔄 In progress (Phase 1)                          |
| Medicine database             | 📋 Planned (Phase 2)                              |
| Book library                  | 📋 Planned (Phase 3)                              |
| AI / RAG pipeline             | 📋 Planned (Phase 4)                              |
| Integration framework (bonus) | ✅ Designed — 10+ providers ready                 |

---

## Folder Structure

```
altcare/
  mock/
    index.html                    ← Mockup index page
    admin-view.html               ← Platform admin interface
    doctor-view.html              ← Doctor/practitioner interface
  backend/
    app/
      main.py
      core/
        config.py
        database.py
        security.py
        dependencies.py
      modules/
        auth/
        doctor/
        patient/
        prescription/
        payment/
        medicine/
        library/
        ai/
        notification/
        integration/        ← SMS/Email/Payment integration framework
      shared/
        models/
        schemas/
        exceptions.py
        pagination.py
    alembic/
    tests/
    pyproject.toml
    Dockerfile
  frontend/
    app/                          ← Next.js App Router pages
    components/
    lib/
    tailwind.config.ts
    Dockerfile
  docker-compose.yml
  docker-compose.prod.yml
  Caddyfile
  .env.example
  README.md                         ← You are here
  DATABASE.md                       ← Full database schema documentation (30 tables)
  ROADMAP.md                        ← Product roadmap: MVP to full platform (12 months)
```

---

## Cost Estimates

### MVP Phase (10-50 active clinics)

| Service | Provider | Monthly Cost |
|---------|----------|--------------|
| VPS (4 vCPU, 8GB RAM, 100GB SSD) | Hetzner/DigitalOcean | $25-40 |
| Domain + DNS | Namecheap/Cloudflare | $1-2 |
| SSL Certificates | Caddy (automatic) | $0 |
| OpenAI API (200 queries/month) | OpenAI | $15-30 |
| Error Tracking | Sentry | $29 |
| Email (40k emails/month) | SendGrid | $15 |
| SMS (1,000 SMS/month) | Twilio | $50 |
| Payment Gateway | SSLCommerz | 2-3% per transaction |
| Backups | Automated snapshots | $5 |
| **Total** | | **~$140-170/month** |

### Growth Phase (200-500 active clinics)

| Service | Provider | Monthly Cost |
|---------|----------|--------------|
| Managed PostgreSQL | DigitalOcean/Neon | $100-150 |
| Managed Redis | Redis Cloud | $40-60 |
| CDN + DDoS protection | Cloudflare Pro | $20 |
| Increased OpenAI API | OpenAI | $100-200 |
| Sentry (more events) | Sentry | $99 |
| Email (200k emails/month) | SendGrid | $50 |
| SMS (5,000 SMS/month) | Twilio | $250 |
| File storage | Cloudflare R2 | $15 |
| Monitoring | Grafana Cloud | $29 |
| **Total** | | **~$700-900/month** |

### Enterprise Phase (1,000+ clinics)

Costs scale to **$2,000-3,000/month** with:
- Kubernetes cluster ($500-800)
- Multi-region deployment
- Dedicated AI inference servers
- Enhanced security (WAF, advanced DDoS)
- Priority support contracts

**Revenue targets:**
- 50 clinics @ ৳1,200 avg = ৳60,000/month ($600) → **Break-even at MVP**
- 500 clinics @ ৳1,200 avg = ৳6,00,000/month ($6,000) → **Profitable at Growth**
- 1,000 clinics @ ৳1,200 avg = ৳12,00,000/month ($12,000) → **Sustainable at Enterprise**

---

## Contributing

Work against feature branches named `feature/module-name` or `fix/short-description`. Open a pull request with a clear description of what changed, which module it belongs to, and whether a database migration is included. All PRs require at least one review before merge to `main`.

**Development guidelines:**
- Write tests for all new features (target: 80% coverage)
- Follow PEP 8 for Python (use `black` formatter)
- Use Conventional Commits format: `feat:`, `fix:`, `docs:`, `test:`
- Update API documentation (`/docs`) when adding endpoints
- Run security checks before PR: `pip-audit`, `bandit`
- Test multi-tenant isolation for all new queries

---

## License

Private — all rights reserved. Contact the project owner for licensing inquiries.

---

## Support & Contact

- **Documentation:** [docs.altcare.health](https://docs.altcare.health) (future)
- **Issues:** GitHub Issues for bug reports and feature requests
- **Email:** support@altcare.health
- **Emergency:** For production outages, contact via incident.io (once set up)
