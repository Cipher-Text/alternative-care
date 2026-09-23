# AltCare — Product Roadmap & Task Tracker

> **⚠️ Superseded in part — 2026-09-23, updated 2026-09-23.** Sequencing, phase scope, and success
> metrics below are superseded by [Plan, Architecture & Technology
> Revision](planning/revision-2026-09.md), which is written against code verified on 2026-09-23 and
> carries the current test/status numbers under its Stage 0 section — check there rather than here,
> this table is not kept live. "MVP v1.0 — Production Ready" still does not hold: nothing is
> deployable (no Dockerfile), password reset/email verification are still commented-out code, and
> global-catalog writes are still broken at the schema level (now the Stage 2 keystone task). Phases
> F (mobile) and G (enterprise) and the public directory are cut. Read the revision first; treat the
> phase detail below as background.

Product direction (2026-09-23): AltCare is the **Alternative Medicine Knowledge & Practice Platform**. Keep the modular monolith and existing practice domains. Follow the staged sequence in [architecture inventory](architecture/architecture-inventory.md): foundation, knowledge catalog, library ingestion/access policy, public web, directory/content, PostgreSQL search, then knowledge-only RAG. Roadmap capabilities must not be reported as implemented.

**Last Updated:** 2026-09-23
**Current Version:** MVP v1.0 — feature-complete, not production ready (see banner above)
**Source of truth:** `docs/status/current.md` · `backend/app/main.py` · `frontend/src/app/**`

---

## Project At a Glance

| Metric | Value |
|---|---|
| Backend modules | 14 registered routers |
| API endpoints | 129 (+ `/`, `/health`, `/metrics`) |
| Database tables | 34 models |
| Frontend routes | 11 route groups (132 source files) |
| Security score | Unscored — the previous "A (95/100)" had no cited source, date, or method (see revision §1) |
| Test coverage | `pytest -q`: 397 passed / 2 xfailed / 0 failed (2026-09-23, see revision Stage 0) |
| Status | Feature-complete, not deployed, not production ready |

---

## Priority Legend

```
🔴 P1 — Critical        Blocks production stability or security
🟠 P2 — High            Needed for the platform to operate as designed
🟡 P3 — Medium          Feature completeness, improves UX
🔵 P4 — Low / Future    Planned but not immediately scheduled
```

---

## What's Done (Complete as of 2026-07-12)

### Core Platform (Phase 1) ✅

| Module | Backend | Frontend | Notes |
|---|---|---|---|
| Authentication & 2FA | ✅ | ✅ | JWT, refresh rotation, TOTP, sessions |
| Patient Management | ✅ | ✅ | CRUD, tags, diagnoses, geographic dropdowns |
| Appointments | ✅ | ✅ | Calendar, scheduling, visits, statuses |
| Prescriptions | ✅ | ✅ | Builder, items, draft→issued→voided, PDF |
| Dashboard Analytics | ✅ | ✅ | KPIs, revenue charts, demographics |
| Doctor Profile | ✅ | ✅ | Profile, degrees, trainings, expiry tracking |
| Payments & Invoicing | ✅ | ✅ | bKash, Nagad, Rocket, SSLCommerz, Stripe |
| Integrations (SMS/Email) | ✅ | ✅ | 12 providers, encrypted credentials, logs |
| Medicines Library | ✅ | ✅ | CRUD, aliases, autocomplete, mappings |
| Symptoms Library | ✅ | ✅ | CRUD, aliases, symptom-medicine mappings |
| Geographic API | ✅ | ✅ | Divisions, districts, upazilas (Bangladesh) |
| Tenant/Clinic Profile | ✅ | ✅ | Clinic info, specializations, fees |
| Security Hardening | ✅ | — | Rate limiting, HTTP headers, password rules |
| Multi-tenant Isolation | ✅ | — | Row-level isolation; historical "16/16" claim was never sourced — current isolation-suite result is part of the 397-passed total in revision-2026-09.md Stage 0 |

### P1 Fixes ✅ — completed 2026-07-12

| Item | Status |
|---|---|
| Tenant isolation 403 guard on `appointments`, `prescriptions`, `payments`, `dashboard` | ✅ |
| TypeScript: 38 errors → 0 across `medicines/`, `symptoms/`, `integrations/`, `doctor/` | ✅ |

### Platform Admin (Phase A) ✅ — completed 2026-07-11

| Item | Status |
|---|---|
| `app/modules/admin/` dedicated module at `/api/v1/admin` | ✅ |
| `GET /admin/dashboard` — platform KPI cards | ✅ |
| `GET /admin/tenants` + `GET /admin/tenants/{id}` + `GET /admin/tenants/pending` | ✅ |
| `POST /admin/tenants` — provision tenant + doctor | ✅ |
| `POST /admin/tenants/{id}/approve` — approve pending tenant | ✅ |
| `PATCH /admin/tenants/{id}` — suspend / reactivate / change plan | ✅ |
| `GET /admin/users` — view users by role | ✅ |
| `PATCH /admin/users/{id}` — change role, activate/deactivate | ✅ |
| `POST /admin/tenants/{id}/doctors` — add a doctor under an existing tenant | ✅ — completed 2026-07-12 |
| Admin-only sidebar (no doctor nav for platform users) | ✅ |
| `/admin/dashboard` — KPI cards page | ✅ |
| `/admin/clients` — 3-tab directory (all / provision / pending) | ✅ |
| `/admin/clients/[tenantId]` — detail view with lifecycle actions + add-doctor form | ✅ |
| `/admin/users` — role distribution + user management | ✅ |

---

## 🔴 P1 — Critical (Fix Now)

These directly affect production stability or security. Address before any new features.

### 1. Tenant Isolation Guard ✅ — Done 2026-07-12

**Problem:** Platform users (`tenant_id = null`) hitting these endpoints get `500` instead of `403`.  
**Fixed in:**

- [x] `appointments/routes.py`
- [x] `prescriptions/routes.py`
- [x] `payments/routes.py`
- [x] `dashboard/routes.py`

All tenant-scoped service factories now return **403** for platform users.

---

### 2. TypeScript Errors ✅ — Done 2026-07-12

**Problem:** 38 type errors silently accumulated across 4 modules.  
**Fixed:** `npx tsc --noEmit` exits 0. Root cause was `useCrudFactory.ts` importing from `@tanstack/react-query` (not installed) instead of `react-query` v3. Additional fixes: alias form fields, geographic ID types, `MedicineSearchResult` extended, `ConfigurationWizard` casts, `RevenueByMethodChart` null guard.

---

### 3. Old Admin Endpoints — Cleanup

**Problem:** Legacy endpoints remain in `auth/routes.py` under `/auth/admin/*` alongside the new `/api/v1/admin/*` canonical ones. Creates maintenance confusion and a dual API surface.

- [ ] Confirm frontend has migrated to `/api/v1/admin/*` (already done per `current.md`)
- [ ] Remove the 5 legacy endpoints from `auth/routes.py`:
  - `POST /auth/admin/provision-client`
  - `GET /auth/admin/clients`
  - `GET /auth/admin/clients/{id}`
  - `GET /auth/admin/tenants/pending`
  - `POST /auth/admin/tenants/{id}/approve`

---

### 4. Password Reset Flow

**Problem:** No way for a user to recover access if they forget their password. Blocks production onboarding.

- [ ] Backend: `POST /auth/forgot-password` — send reset email with expiring token
- [ ] Backend: `POST /auth/reset-password` — validate token, set new password with strength check
- [ ] Frontend: Forgot password page at `/(auth)/forgot-password`
- [ ] Frontend: Reset password page at `/(auth)/reset-password?token=...`
- [ ] Celery task: send password reset email via configured SMTP/SendGrid provider

---

### 5. Email Verification Flow

**Problem:** Users can use unverified email addresses. No confirmation step on registration.

- [ ] Backend: send verification email on registration (`is_email_verified = false`)
- [ ] Backend: `POST /auth/verify-email?token=...` — mark email verified
- [ ] Frontend: post-registration "check your email" screen
- [ ] Frontend: email verified confirmation screen
- [ ] Restrict certain actions until email is verified (optional, can be soft-block)

---

## 🟠 P2 — High Priority

Core platform functionality that is designed but not yet enforced or built.

### 6. Operator Role Enforcement (Admin Phase B)

**Problem:** `operator` role exists in the DB and RBAC guard is stubbed, but no endpoints actually use it. An `operator` user currently has no access surface.

- [ ] Backend: Wire `RequireAdminOrOperator` to all admin `GET` endpoints (read-only access for operators)
- [ ] Backend: Protect admin `POST`/`PATCH`/`DELETE` endpoints as `RequireAdmin` only (admin-only write)
- [ ] Frontend: Operator sees the same admin sidebar but write actions (provision, approve, change plan, suspend) are hidden
- [ ] Frontend: Role badge visible in topbar for operator users
- [ ] Test: confirm operator cannot POST/PATCH, can GET all admin data

---

### 7. Receptionist Role Enforcement

**Problem:** `receptionist` role is stored but entirely unenforced. Any receptionist can currently do anything a doctor can.

- [ ] Backend: Apply `require_role("doctor", "receptionist")` to appointment and patient read endpoints
- [ ] Backend: Restrict prescription creation/editing to `doctor` only (`RequireDoctor`)
- [ ] Backend: Restrict payment write actions to `doctor` only
- [ ] Frontend: Hide prescription "Create" / "Edit" buttons for receptionist users
- [ ] Frontend: Hide payment write actions for receptionist users

---

### 8. Admin — Degree & Training Verification Interface

**Problem:** `DoctorDegree.is_verified` and `DoctorTraining.is_verified` fields exist and are tracked but there is no admin UI or endpoint to verify them.

- [ ] Backend: `PATCH /admin/tenants/{tenant_id}/degrees/{degree_id}/verify`
- [ ] Backend: `PATCH /admin/tenants/{tenant_id}/trainings/{training_id}/verify`
- [ ] Frontend: Add degree/training list to `/admin/clients/[tenantId]` with verify toggle

---

### 9. Planning/README.md — Baseline Snapshot Update ✅ — Done 2026-09-21

**Problem:** `docs/planning/README.md` baseline snapshot was stale (previously "11 modules, 89 endpoints").

- [x] Update baseline: 14 modules, 128 endpoints, 11 frontend route groups (132 source files)
- [x] Update date to 2026-09-21

---

## 🟡 P3 — Medium Priority

Feature completeness. These improve the product materially but don't block current use.

### 10. Bengali Translations — Complete Coverage

- [ ] Audit all UI strings that are still English-only
- [ ] Add missing Bengali translation keys to `translations` table
- [ ] Test language switcher across all pages
- [ ] Verify bilingual form labels (patients, prescriptions, profile)

---

### 11. Medicine Seed Data — 1,000+ Curated Medicines

**Current state:** Medicine CRUD, aliases, and symptom mappings are fully implemented. The library is empty in production — doctors must add medicines manually.

- [ ] Curate and import 200+ Homeopathy medicines
- [ ] Curate and import 150+ Ayurveda medicines
- [ ] Curate and import 100+ Unani medicines
- [ ] Curate and import 50+ Herbal medicines
- [ ] Validate with practitioners (at least 2 reviewers per system)
- [ ] Bilingual entries (name_en + name_bn) for all medicines
- [ ] Create seed script: `scripts/seed_medicines.sh`

---

### 12. Symptom Mapping Seed Data — 1,000+ Mappings

**Current state:** `medicine_symptom_mappings` table exists with full CRUD. No data seeded.

- [ ] Map 200+ symptoms to Homeopathy medicines
- [ ] Map 150+ symptoms to Ayurveda medicines
- [ ] Map 100+ symptoms to Unani medicines
- [ ] Create weighted match scores per mapping
- [ ] Create seed script: `scripts/seed_symptoms.sh`

---

### 13. Prescription Builder — Medicine DB Autocomplete

**Current state:** Free-text medicine name is used (MVP workaround). `MedicineAutocomplete` component exists with 300ms debounce and keyboard nav but works off live API search, not a seeded DB.

- [ ] Once medicine seed data (Task 11) is in: enable full autocomplete from DB
- [ ] Show dosage suggestions from `medicines.dosage_guidelines`
- [ ] Show recently used medicines per doctor (track in `usage_tracking`)
- [ ] Contraindication warnings (red badge) when a medicine has mapped contraindications

---

### 14. Notification & Email Template Management

**Current state:** SMS/Email providers are configured and can send. Templates are hardcoded strings in backend service code.

- [ ] Backend: `translations` table can store email/SMS templates — use it
- [ ] Backend: `GET /admin/notifications/templates` — list all templates
- [ ] Backend: `PATCH /admin/notifications/templates/{key}` — update template
- [ ] Frontend: Notification settings page at `/settings/notifications`
- [ ] Frontend: Template editor (subject + body, with variable hints)

---

### 15. Tenant Onboarding Wizard

**Current state:** Admin manually provisions tenants. New tenants land on the dashboard with no guidance.

- [ ] Frontend: Post-provisioning onboarding checklist for new doctors:
  - Step 1: Complete profile & clinic info
  - Step 2: Add degrees/trainings
  - Step 3: Configure at least one SMS/email integration
  - Step 4: Add first patient
- [ ] Mark each step complete via localStorage or a `usage_tracking` flag
- [ ] Show wizard on first login only (dismiss once all steps done)

---

### 16. Dashboard — Calendar Heatmap & Top Diagnoses

**Current state:** Dashboard KPI cards, revenue charts, and demographics are complete. Heatmap and "top diagnoses/medicines" widgets are stubbed.

- [ ] Backend: `GET /dashboard/heatmap` — appointment counts per day for calendar heatmap
- [ ] Backend: `GET /dashboard/top-diagnoses` — top 10 diagnoses by patient count
- [ ] Backend: `GET /dashboard/top-medicines` — top 10 prescribed medicines
- [ ] Frontend: Calendar heatmap widget (green dot intensity = patient load)
- [ ] Frontend: Horizontal bar charts for top diagnoses and top medicines

---

### 17. Appointment Reminders via SMS/Email

**Current state:** Appointments are created and tracked. No automated reminders are sent.

- [ ] Backend: Celery beat task — scan appointments scheduled in next 24h
- [ ] Backend: Send SMS reminder to patient phone (if SMS provider configured)
- [ ] Backend: Send email reminder to patient email (if email provider configured)
- [ ] Backend: Mark reminder sent in `appointments.reminder_sent_at`
- [ ] Frontend: Reminder opt-in toggle on appointment create/edit form

---

### 18. Bulk Operations

- [ ] Backend: `POST /patients/bulk-delete` (soft delete multiple patients)
- [ ] Backend: `POST /prescriptions/bulk-export` — batch PDF download
- [ ] Frontend: Multi-select checkboxes on patient and prescription list tables
- [ ] Frontend: Bulk action toolbar (appears when items selected)

---

## 🔵 P4 — Future / Planned Phases

These are designed and scoped but not yet scheduled for active development.

---

### Phase C — Book Library & Reader

**Prerequisite:** Medicine seed data (Task 11) should be live first.  
**Estimated effort:** 20–30 hours

**Backend:**
- [ ] `GET /library/books` — list books (global + tenant)
- [ ] `GET /library/books/{id}/chapters` — chapter listing
- [ ] `GET /library/chapters/{id}/sections` — paginated section content
- [ ] `POST /library/books/{id}/progress` — update reading position
- [ ] Bookmark and highlight CRUD endpoints
- [ ] EPUB upload + parsing pipeline (Celery: ebooklib → chapters → sections)

**Frontend:**
- [ ] Book library grid at `/library`
- [ ] Book reader UI: table of contents sidebar, chapter navigation, progress bar
- [ ] Reader toolbar: bookmark, highlight, font size, theme (light/dark/sepia)
- [ ] Reading progress widget on dashboard

**Content:**
- [ ] Acquire/digitize 20+ classical texts across all 4 systems
- [ ] Homeopathy: Organon, Boericke's Materia Medica, Kent's Repertory
- [ ] Ayurveda: Charaka Samhita, Ashtanga Hridaya
- [ ] Unani: Canon of Medicine (Ibn Sina)
- [ ] Herbal: PDR for Herbal Medicines

---

### Phase D — AI Chat Assistant (RAG)

**Prerequisite:** Book library (Phase C) must be populated and embedded.  
**Estimated effort:** 40–60 hours  
**Plan gate:** Pro plan only (`RequireProPlan`). Stub endpoint already exists at `POST /api/v1/ai/query` (returns 501).

---

#### Knowledge Sources (RAG Input Data)

The AI assistant is grounded in three data sources. Responses must always cite which source the answer came from.

| Source | What it contains | How it's used |
|---|---|---|
| **Book library** | Classical medical texts — Organon, Boericke's Materia Medica, Charaka Samhita, Canon of Medicine, etc. | Chunked into sections → embedded → vector search via pgvector |
| **Medicine database** | `medicines` + `medicine_aliases` + `medicine_symptom_mappings` — names, indications, dosage, potency, system, symptom relationships | Structured DB lookup — no embedding needed, queried directly |
| **Symptom database** | `symptoms` + `symptom_aliases` + `medicine_symptom_mappings` — symptom names, categories, linked medicines with strength scores | Structured DB lookup — used to suggest medicines for a given symptom set |

Responses are **filtered by the doctor's specializations** (`tenant.specializations`). A Homeopathy doctor only gets Homeopathy book sections and medicines.

---

#### Backend

- [ ] Implement `POST /api/v1/ai/query` (replace 501 stub)
- [ ] Embedding pipeline: chunk book sections (800 tokens, 100 overlap) → `text-embedding-3-small` → store in `embeddings` table (pgvector)
- [ ] HNSW index on `embeddings.vector` for fast cosine similarity search
- [ ] Celery batch job: embed all book sections on library population
- [ ] RAG retrieval strategy:
  - Step 1 — Vector search: top-5 book sections by cosine similarity, filtered by doctor's specializations
  - Step 2 — Structured lookup: query `medicines` and `symptoms` tables for exact name/alias matches in the query
  - Step 3 — Assemble context window (max 4,000 tokens): book excerpts + medicine/symptom records
- [ ] GPT-4o-mini response generation with mandatory source citations
- [ ] Streaming response (Server-Sent Events)
- [ ] `GET /api/v1/ai/history` — query history per doctor
- [ ] `POST /api/v1/ai/feedback` — thumbs up/down per response
- [ ] Usage quota enforcement (200 queries/month for Pro plan, tracked in `usage_tracking`)
- [ ] Redis cache for repeated queries (1-hour TTL)

#### Frontend

- [ ] `/ai` — AI chat page (Pro plan gated, upgrade prompt for others)
- [ ] Chat interface: user/AI message bubbles, streaming typewriter effect
- [ ] Citation display per response — expandable source cards:
  - Book citation: Book title · Chapter · Section (links to `/library` reader)
  - Medicine citation: Medicine name (links to `/medicines/{id}`)
  - Symptom citation: Symptom name (links to `/symptoms/{id}`)
- [ ] Source filter toggle: "Books only / Medicines DB / All sources"
- [ ] Query history sidebar (last 20 queries)
- [ ] Usage quota indicator: "X / 200 queries used this month"
- [ ] Quick prompt chips: common clinical questions per specialization
- [ ] Clinical disclaimer banner (always visible, cannot be dismissed)
- [ ] Feedback buttons (thumbs up/down) per response

#### Safety & Guardrails

- [ ] System prompt: never make prescriptive decisions, always cite source, state clearly when answer not found
- [ ] Temperature: 0.3 (factual, low creativity)
- [ ] Hallucination check: verify every cited section/medicine ID actually exists before responding
- [ ] Content filter: block non-medical queries, flag dangerous advice
- [ ] Admin view: token cost per query, feedback ratings, flagged responses

#### Admin Analytics (Phase D addition to `/admin`)

- [ ] `GET /admin/ai/usage` — per-tenant query counts, token spend, quota usage
- [ ] `GET /admin/ai/feedback` — aggregate thumbs up/down ratings
- [ ] `GET /admin/ai/flagged` — responses flagged for review

---

### Phase E — Public Doctor Directory

**Context:** Mock UI designed at `mock/doctors.html`. Backend does not yet support this.
**Estimated effort:** 25–35 hours

**New backend infrastructure needed:**
- [ ] `GET /api/v1/public/doctors` — unauthenticated, filtered by specialization/district/availability
- [ ] `DoctorSchedule` table — weekly availability (day_of_week, start_time, end_time)
- [ ] `DoctorReview` table — patient reviews (rating, text, created_at, status)
- [ ] `User.bio` field — personal doctor bio (separate from clinic `description_en`)
- [ ] `Tenant.is_publicly_listed` flag — admin controls who appears in directory

**Fields supported today** (no new DB work needed):
- `User.full_name`, `DoctorDegree` list, `Tenant.specializations`, `Tenant.district_id`

**Fields requiring new DB work:**
- Availability status, weekly schedule, rating/review, personal bio, public listing flag

**Wider scope, not detailed here (added 2026-09-23):** a College/Institution Directory and an editorial Content/CMS track were added to the product's scope, both gated behind Stage 4, neither scheduled. Direction and reasoning: `docs/planning/future-scope-2026-09.md`. Why this phase's `is_publicly_listed` flag above is the right call, not just a convenient one: `docs/architecture/adr/008-directory-from-tenant-data.md`.

---

### Phase F — Mobile Apps · **Cut — see `docs/planning/revision-2026-09.md` §2.1**

**Estimated effort:** 120–160 hours  
**Platform:** React Native (iOS + Android)

- [ ] Patient app: view prescriptions, book appointments, payment
- [ ] Doctor app: view schedule, patient lookup, quick prescriptions, push notifications
- [ ] Shared API client (Axios + React Query)
- [ ] Push notifications (Expo Notifications or Firebase)

Cut, not deferred: responsive web already covers the use case; make it installable as a PWA instead. Revisit only if a specific mobile-only capability (e.g. offline charting) becomes a real blocker.

---

### Phase G — Enterprise Features · **Cut — see `docs/planning/revision-2026-09.md` §2.1**

- [ ] Multi-clinic management (clinic chains, cross-clinic reporting)
- [ ] White-label solution (custom branding, custom domains, logo/colors)
- [ ] Audit log UI (comprehensive admin view of all system actions)
- [ ] HIPAA compliance mode (data retention policies, backup/restore UI)
- [ ] SOC 2 compliance
- [ ] GraphQL API (in addition to REST)
- [ ] Keycloak SSO (enterprise authentication)

Cut, not deferred: every item here is an enterprise-buyer feature, and there are no enterprise buyers in the pipeline. Revisit when a signed contract asks — "Audit log UI" specifically is tracked as a gated-not-dated item after Stage 4 (`docs/planning/revision-2026-09.md`), since the underlying `created_by`/`updated_by` audit columns already exist; it's the UI surfacing them that's missing.

---

## Technical Debt

These are not features but quality concerns that should be addressed incrementally.

| Item | Impact | Effort |
|---|---|---|
| Celery worker configuration missing (PDF, email, embeddings queues) | Medium — PDF/email tasks queue but may not process | Low |
| Structured logging (structlog) not configured | Low — harder to debug in production | Low |
| Sentry error tracking not wired in | Medium — blind to production errors | Low |
| Prometheus metrics collection not configured | Low — no operational dashboards | Medium |
| `pg_stat_statements` not enabled | Low — can't identify slow queries | Low |
| Database indexes missing on dashboard aggregation queries | Medium — slow dashboards at scale | Medium |
| File uploads — only URL strings stored, no actual upload UI | Low — MinIO ready but unused | Medium |
| Email/SMS templates hardcoded in service code | Low — can't customize without deploy | Medium |
| No prescription templates | Medium — doctors re-enter repeated medicines | High |
| Appointment reminders not automated | Medium — patients miss appointments | Medium |

---

## Timeline

```
2026-09-21  ← TODAY (last major shipped work: 2026-07-12, doctor provisioning under existing tenants)
│
├── NOW     🔴 P1 Remaining
│           ├─ Legacy /auth/admin/* endpoint removal
│           ├─ Password reset flow
│           └─ Email verification flow
│           (Tenant isolation guards and TypeScript cleanup shipped 2026-07-12 — see "What's Done" above)
│
├── Q3 2026 🟠 P2 + 🟡 P3 — Platform completeness
│           ├─ Operator & receptionist role enforcement
│           ├─ Admin degree/training verification UI
│           ├─ Medicine seed data (1,000+ medicines)
│           ├─ Symptom mapping seed data (1,000+ mappings)
│           ├─ Prescription DB autocomplete
│           ├─ Bengali translations completion
│           ├─ Dashboard heatmap + top diagnoses/medicines
│           └─ Appointment SMS/email reminders
│
├── Q4 2026 📚 Phase C — Book Library & Reader
│           ├─ EPUB upload + parsing pipeline
│           ├─ Book reader UI
│           └─ 20+ classical medical texts curated
│
├── Q1 2027 🤖 Phase D — AI / RAG Assistant
│           ├─ Vector embedding pipeline (50K+ sections)
│           ├─ RAG retrieval + GPT-4o-mini
│           ├─ Chat UI with streaming + citations
│           └─ Safety guardrails + admin analytics
│
├── Q2 2027 🌍 Phase E — Public Doctor Directory
│           ├─ Public /doctors browse endpoint
│           ├─ Doctor availability & review system
│           └─ Public listing controls
│
└── Q3 2027+ 📱 Phase F/G — Mobile & Enterprise
            ├─ React Native apps (iOS + Android)
            ├─ White-label solution
            ├─ Multi-clinic management
            └─ SOC 2 / HIPAA compliance
```

---

## Success Metrics

### Current (MVP v1.0) — superseded, see revision-2026-09.md §8 for the live numbers
- 129 API endpoints across 14 modules
- 34 database tables
- 132 frontend source files
- Security score: unscored (previous "A (95/100)" had no cited source)
- `pytest -q`: 397 passed / 2 xfailed / 0 failed (2026-09-23)

### Q3 2026 Targets
- [ ] Zero critical security gaps (P1 items closed)
- [ ] Zero TypeScript errors
- [ ] 10+ active paying tenants onboarded
- [ ] 1,000+ medicines seeded and searchable
- [ ] 95%+ uptime (Uptime Robot or equivalent)
- [ ] API P95 response time < 500ms

### Q1 2027 Targets (Post-AI)
- [ ] 50+ active paying clinics
- [ ] AI assistant used by 80%+ of Pro plan doctors
- [ ] 50,000+ prescriptions generated in system
- [ ] Monthly recurring revenue: ৳2.5L+ (~$2,500)

### Q3 2027 Targets (Full Platform)
- [ ] 200+ active paying clinics
- [ ] Mobile apps launched (iOS + Android)
- [ ] 99%+ uptime SLA
- [ ] Expansion to India market initiated

---

## Related Documents

| Document | Purpose |
|---|---|
| `docs/status/current.md` | Authoritative current implementation status |
| `docs/planning/admin-module.md` | Admin module Phase A/B spec |
| `docs/planning/role-distribution.md` | Role distribution spec |
| `docs/architecture/roles-access.md` | RBAC roles reference |
| `docs/architecture/database-schema.md` | Database schema reference |
| `docs/testing/TEST_STRATEGY.md` | Test coverage standards |
| `CLAUDE.md` | Architecture & conventions (source of truth for AI assistants) |
| `mock/doctors.html` | Public doctor directory UI prototype |

---

**Maintained by:** Development Team  
**Review cadence:** Update `docs/status/current.md` after every meaningful commit. Review this roadmap weekly.
