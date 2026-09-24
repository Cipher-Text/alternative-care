# AltCare — Alternative Medicine Knowledge & Practice Platform

The product direction preserves working practice-management domains and expands incrementally into platform-global knowledge and content. The current system remains one Next.js frontend, one FastAPI modular monolith, and one PostgreSQL database. Public knowledge, books, colleges, CMS, unified search, and RAG are roadmap capabilities, not delivered features.

Tenant separation currently uses application-level explicit row isolation, not PostgreSQL RLS. See [architecture inventory](../architecture/architecture-inventory.md) for code-verified models, risks, and staged migration plan.

> **⚠️ Status claims superseded — 2026-09-23, updated 2026-09-24.** See
> [Plan, Architecture & Technology Revision, Stage 0](../planning/revision-2026-09.md#stage-0--truth--green--by-2026-10-07)
> for the current, live numbers — this file isn't kept in sync with them, don't quote figures from
> here. Short version: the test suite is green (`pytest -q`: 432 passed / 2 xfailed / 0 failed,
> was 322 passed / 76 failed); Sentry/structlog are initialised. Password reset and email
> verification now work end to end (no longer commented out — see "Done 2026-09-23" below), and
> Google Sign-In/registration shipped the same day. Global medicine/symptom creation is now also
> fixed (2026-09-24, migration `ba209a25bf7d` — see "Done 2026-09-24" below). Still true: there is
> no deployment path (no Dockerfile, no IaC), and `usage_tracking` still has no writers — both are
> tracked, unfixed gaps, not newly discovered.

# Current Project Status

Last Updated: 2026-09-24

---

## Summary

AltCare has a working FastAPI backend (14 registered modules, 135 endpoints) and a Next.js frontend (132 source files, 11 route groups) covering auth, dashboard, patients, appointments, prescriptions, payments, integrations, medicines, symptoms, and a full platform admin area.

Recent work (2026-09-24):
- **Global medicine/symptom creation fixed** — the Stage 2 keystone (D1). See "Global medicine/symptom creation — fixed 2026-09-24" below.

Recent work (2026-09-23):
- **Google Sign-In and registration:** `POST /auth/google` (sign in, or `{needs_registration: true}` for a first-time Google identity) and `POST /auth/google/register` (completes clinic registration for that identity). Backend verifies the ID token itself (`app/core/security.py:verify_google_id_token`); an existing password-based account with a matching email gets its Google identity linked automatically on first sign-in. 2FA is still enforced on top of Google sign-in. Frontend: `GoogleSignInButton`, `GoogleRegisterForm`, `/register/google`. See `docs/api/authentication.md`.
- **Password reset + email verification shipped end to end** (previously commented-out stubs) — see "Done 2026-09-23" below.
- Test suite grew from 422 to 432 passed (2 xfailed, 0 failed) covering the above.

Recent work (2026-07-12):
- **Admin — doctor provisioning under existing tenants:** `POST /admin/tenants/{id}/doctors` added so platform admins can add another doctor user to an already-provisioned clinic without re-running full tenant onboarding. Frontend: `/admin/clients/[tenantId]` detail page now includes an add-doctor form. Integration tests added (`tests/integration/test_admin_tenant_doctors.py`).
- **P1 #1 — Tenant Isolation Guard:** Applied 403 guard to 4 previously unprotected service factories (`appointments`, `prescriptions`, `payments`, `dashboard`) — platform users now get proper 403 instead of 500
- **P1 #2 — TypeScript:** Resolved all 38 pre-existing TS errors across `medicines/`, `symptoms/`, `integrations/`, `doctor/` — project now compiles clean (exit 0)
  - Root fix: `useCrudFactory.ts` imported from `@tanstack/react-query` (not installed); corrected to `react-query` v3
  - Added `TList` generic to `CrudApi` so list endpoint can return lightweight type (`MedicineListItem`) while get/create/update use full type (`Medicine`)
  - Alias forms in `medicines/[id]` and `symptoms/[id]` corrected to use `alias_en`/`alias_bn` (backend schema fields)
  - `ProfileForm.tsx`: geographic ID string↔number conversions fixed; `SelectItem` values converted to strings
  - `MedicineSearchResult` type extended with optional `is_global`, `dosage_guidance_en`, `indications_en`
  - `ConfigurationWizard.tsx`: `unknown` values from `Record<string, unknown>` properly cast
  - `RevenueByMethodChart.tsx`: `percent ?? 0` guard added

Recent work (2026-07-11):
- Added geographic API (`/api/v1/geographic/`) — divisions, districts, upazilas (Bangladesh)
- Fixed patient creation: 403 guard for platform users, unhandled promise fix in form
- Implemented Platform Admin Phase A: dedicated `app/modules/admin/` module at `/api/v1/admin`
- Implemented Role Distribution: `GET /admin/users` + `PATCH /admin/users/{id}` — view users by role, change roles, activate/deactivate
- Frontend: admin-only sidebar, `/admin/dashboard` (KPI cards), `/admin/users` (role distribution + user management)
- `/admin/clients` now uses new admin API endpoints

---

## Roles

See `docs/architecture/roles-access.md` for the full authoritative reference.

| Role | Level | Status |
|---|---|---|
| `admin` | Platform | ✅ Implemented |
| `operator` | Platform | ⚠️ RBAC stub, no endpoints |
| `doctor` | Tenant | ✅ Implemented |
| `receptionist` | Tenant | ⚠️ Role string only, no enforcement |

---

## Backend

Registered routers in `backend/app/main.py`:

| Module | Prefix | Endpoints | Notes |
|---|---|---|---|
| auth | `/api/v1/auth` | 21 | Login (incl. `login-2fa`), Google Sign-In/registration, register, password reset, email verification, legacy admin compatibility |
| ai | `/api/v1/ai` | 1 | Stub, returns 501 |
| appointments | `/api/v1/appointments` | 10 | Scheduling and visits (includes nested `visits_router`: 4 endpoints under `/visits`) |
| dashboard | `/api/v1/dashboard` | 6 | Tenant-scoped analytics |
| doctor | `/api/v1/doctor` | 12 | Profile, degrees, trainings |
| patient | `/api/v1/patients` | 14 | CRUD, tags, diagnoses |
| prescription | `/api/v1/prescriptions` | 8 | |
| payment | `/api/v1/payments` | 12 | |
| integration | `/api/v1/integrations` | 12 | |
| medicine | `/api/v1/medicines` | 15 | CRUD, search, aliases, symptom mappings |
| symptom | `/api/v1/symptoms` | 9 | CRUD, search, aliases |
| tenant | `/api/v1/tenant` | 2 | Clinic profile |
| geographic | `/api/v1/geographic` | 3 | Divisions/districts/upazilas |
| admin | `/api/v1/admin` | 10 | Platform admin — tenants + users, incl. `POST /admin/tenants/{id}/doctors` |

**Total:** 135 module endpoints + `/`, `/health`, `/metrics`

Legacy platform admin endpoints remain in `auth/routes.py` (5 endpoints under `/auth/admin/*`) for backwards compatibility.
New canonical endpoints are at `/api/v1/admin`.

---

## Frontend

Implemented routes:

| Route | Status |
|---|---|
| `/login` | ✅ (incl. Google Sign-In button) |
| `/register/google` | ✅ Clinic-details completion step for a new Google identity |
| `/dashboard` | ✅ |
| `/profile` | ✅ |
| `/patients`, `/patients/new`, `/patients/[id]`, `/patients/[id]/edit` | ✅ |
| `/appointments`, `/appointments/new`, `/appointments/[id]` | ✅ |
| `/prescriptions`, `/prescriptions/new`, `/prescriptions/[id]`, `/prescriptions/[id]/edit` | ✅ |
| `/payments`, `/payments/transactions`, `/payments/invoices/*` | ✅ |
| `/medicines`, `/medicines/new`, `/medicines/[id]`, `/medicines/[id]/edit` | ✅ |
| `/symptoms`, `/symptoms/new`, `/symptoms/[id]`, `/symptoms/[id]/edit` | ✅ |
| `/settings`, `/settings/integrations` | ✅ |
| `/admin/clients` | ✅ (3-tab: directory / provision / pending) |
| `/admin/clients/[tenantId]` | ✅ detail view with lifecycle actions + add-doctor-to-tenant form |
| `/admin/dashboard` | ✅ KPI cards |
| `/admin/users` | ✅ Role distribution + user management |

---

## Known gaps

### Platform admin (see `docs/planning/admin-module.md` for full spec)
- ✅ Dedicated `app/modules/admin/` module at `/api/v1/admin`
- ✅ Platform KPI dashboard (`/admin/dashboard`)
- ✅ Tenant lifecycle actions (PATCH /admin/tenants/{id} — suspend/reactivate/change plan)
- ✅ Role distribution (`GET /admin/users`) + user management (`PATCH /admin/users/{id}`)
- ✅ Add a doctor under an existing tenant (`POST /admin/tenants/{id}/doctors`)
- ✅ Admin-only sidebar (no doctor nav items for platform users)
- ⚠️ Old endpoints remain in `auth/routes.py` — can be removed once confirmed stable
- `operator` role: RBAC guard exists, no endpoints use it (Phase B)

### Tenant isolation guard
- ✅ Guard applied in all tenant-scoped service factories: `patients`, `appointments`, `prescriptions`, `payments`, `dashboard`
- Platform users (`tenant_id = null`) get proper **403** from all tenant endpoints

### TypeScript
- ✅ 0 errors — frontend compiles clean (`npx tsc --noEmit` exits 0 as of 2026-07-12)

### Global medicine/symptom creation — fixed 2026-09-24

Previously: `medicines`/`symptoms`/`medicine_aliases`/`symptom_aliases`/`medicine_symptom_mappings`
inherited `TenantScopedModel`, whose `tenant_id` column is `NOT NULL` — but `POST /medicines` (and
the sibling symptom/alias/mapping routes) set `tenant_id=None` for a global row, so the insert
500'd at the database with an `IntegrityError` every time an admin tried to curate a global entry
(or add an alias/mapping while acting as admin, since admins have `tenant_id = NULL` on their own
account too).

Fixed by migration `ba209a25bf7d`: those five tables now inherit a new `GlobalCatalogModel` base
(`app/shared/models/base.py`) with a nullable `tenant_id`, and `medicines`/`symptoms` (the two with
their own `is_global` column) gained a CHECK constraint —
`(is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL)` — so the invalid
combination can't be written by any code path, present or future. No backfill was needed (every
existing row already satisfied the constraint); `pytest -q` stayed at 432 passed / 2 xfailed / 0
failed after the change, and both the valid-global-insert and the two invalid combinations were
verified manually against the dev database.

This was Stage 2's keystone item (D1 in `docs/planning/revision-2026-09.md`) — the prescription
autocomplete now has something to autocomplete against once the catalog is actually seeded, though
seeding (300 reviewed medicines) and the rest of Stage 2 (service-layer cleanup, RLS, public API
boundary, search) are still open.

### Medicine & Symptom search — backend done, frontend gap

Both modules have a full server-side search API that is **not used by the list pages**:

| Endpoint | Status | Used by |
|---|---|---|
| `GET /medicines/search?q=` | ✅ Backend done | `MedicineAutocomplete` in prescription builder only |
| `GET /symptoms/search?q=` | ✅ Backend done | Nowhere in frontend |
| `GET /medicines/{id}/symptoms` | ✅ Backend done | Nowhere in frontend |
| `GET /medicines/symptoms/{id}/medicines` | ✅ Backend done | Nowhere in frontend |

- `/medicines` list page: client-side `.filter()` on first 100 loaded rows — misses anything beyond that
- `/symptoms` list page: same pattern — client-side only
- **No dedicated "enter symptom → get recommended medicines" page exists** (key clinical workflow)

Planned frontend work:
- Wire `/medicines/search` into the medicines list page (replace client-side filter)
- Wire `/symptoms/search` into the symptoms list page
- Build `/symptoms/[id]` detail page showing linked medicines (calls `GET /medicines/symptoms/{id}/medicines`)
- Build a dedicated clinical lookup page: multi-symptom input → ranked medicine results

### Book Library — models exist, nothing else

All DB models are defined and migrated:
`books`, `chapters`, `sections`, `embeddings`, `reading_progress`, `bookmarks`, `highlights`

Nothing built yet:
- No backend routes (`app/modules/library/` — no `routes.py`)
- No frontend pages
- No EPUB parsing pipeline
- No reader UI

Planned as **Phase C** in `docs/ROADMAP.md`. Prerequisite for the AI/RAG assistant (Phase D).

### AI Chat Assistant — planned Phase D

Stub endpoint exists: `POST /api/v1/ai/query` returns `501 Not Implemented`. Pro plan gated.

Planned as a doctor-facing chat interface powered by RAG across three knowledge sources:

| Source | Data | Access method |
|---|---|---|
| Book library | Classical medical texts (books → chapters → sections) | Vector similarity search via pgvector (`embeddings` table) |
| Medicine database | Medicines, aliases, indications, dosage, potency | Structured DB query (`medicines` + `medicine_aliases`) |
| Symptom database | Symptoms, aliases, symptom→medicine mappings with strength scores | Structured DB query (`symptoms` + `medicine_symptom_mappings`) |

Responses filtered by doctor's specializations. Every answer cites which source it came from (book section / medicine / symptom). See `docs/ROADMAP.md` Phase D for full spec.

**Dependencies in order:**
1. Phase C — Book library routes + EPUB parsing + reader UI
2. Phase D — Embedding pipeline + RAG retrieval + chat UI

### Other unimplemented features
- `receptionist` role enforcement (RBAC not applied)
- Public doctor directory — mock at `mock/doctors.html` — see below
- Public landing page

**Done 2026-09-23:** password reset (`POST /auth/password/forgot`, `/password/reset`) and email
verification (`POST /auth/email/verify`, `/email/resend`) — previously commented-out code, now
live end to end including Celery-delivered system email (`app/core/system_email.py`). Provider is
picked by `EMAIL_PROVIDER` (`sendgrid` | `resend` | `mailgun` | `smtp2go` | `smtp`, all sent over
SMTP relay, no per-provider SDK) — no-ops with a logged warning when unset or its credentials are
incomplete.

### Expanded scope, not yet built — added 2026-09-23

A feature-by-feature audit against a wider product scope (practitioner/college/clinic directories, editorial content, a knowledge taxonomy beyond Medicine/Symptom) found 38 of 95 named items with zero footprint anywhere in the repo before this date. Direction and sequencing, not left undocumented: `docs/planning/future-scope-2026-09.md`. Kept separate from this file and from `revision-2026-09.md`'s dated stages, since none of it has a date yet.

---

## Documentation source-of-truth rules

1. `backend/app/main.py` — active module list
2. `backend/app/modules/*/routes.py` — endpoint truth
3. `frontend/src/app/**` — implemented UI routes
4. `docs/architecture/roles-access.md` — roles and RBAC
5. `docs/planning/admin-module.md` — admin Phase A spec
6. `docs/ROADMAP.md` — product roadmap and priorities
