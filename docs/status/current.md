# Current Project Status

Last Updated: 2026-07-11

---

## Summary

AltCare has a working FastAPI backend (14 registered modules) and a Next.js frontend covering auth, dashboard, patients, appointments, prescriptions, payments, integrations, medicines, symptoms, and a full platform admin area.

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
| auth | `/api/v1/auth` | 12 | Login, 2FA, register, admin provisioning |
| ai | `/api/v1/ai` | 1 | Stub, returns 501 |
| appointments | `/api/v1/appointments` | 6 | |
| dashboard | `/api/v1/dashboard` | 6 | Tenant-scoped analytics |
| doctor | `/api/v1/doctor` | 12 | Profile, degrees, trainings |
| patient | `/api/v1/patients` | 14 | CRUD, tags, diagnoses |
| prescription | `/api/v1/prescriptions` | 8 | |
| payment | `/api/v1/payments` | 12 | |
| integration | `/api/v1/integrations` | 12 | |
| medicine | `/api/v1/medicines` | 8 | CRUD, search, aliases, symptom mappings |
| symptom | `/api/v1/symptoms` | 8 | CRUD, search, aliases |
| tenant | `/api/v1/tenant` | 2 | Clinic profile |
| geographic | `/api/v1/geographic` | 3 | Divisions/districts/upazilas |
| admin | `/api/v1/admin` | 9 | Platform admin — tenants + users (NEW) |

**Total:** ~113 module endpoints + `/`, `/health`, `/metrics`

Legacy platform admin endpoints remain in `auth/routes.py` (5 endpoints under `/auth/admin/*`) for backwards compatibility.
New canonical endpoints are at `/api/v1/admin`.

---

## Frontend

Implemented routes:

| Route | Status |
|---|---|
| `/login` | ✅ |
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
| `/admin/clients/[tenantId]` | ✅ |
| `/admin/dashboard` | ✅ KPI cards |
| `/admin/users` | ✅ Role distribution + user management |

---

## Known gaps

### Platform admin (see `docs/planning/admin-module.md` for full spec)
- ✅ Dedicated `app/modules/admin/` module at `/api/v1/admin`
- ✅ Platform KPI dashboard (`/admin/dashboard`)
- ✅ Tenant lifecycle actions (PATCH /admin/tenants/{id} — suspend/reactivate/change plan)
- ✅ Role distribution (`GET /admin/users`) + user management (`PATCH /admin/users/{id}`)
- ✅ Admin-only sidebar (no doctor nav items for platform users)
- ⚠️ Old endpoints remain in `auth/routes.py` — can be removed once confirmed stable
- `operator` role: RBAC guard exists, no endpoints use it (Phase B)

### Tenant isolation guard
- Pattern applied in: `patients/routes.py`
- Still missing in: `appointments`, `prescriptions`, `payments`, `dashboard` service factories
  (platform users would get 500 instead of 403 if they hit those endpoints)

### TypeScript
- 38 pre-existing TS errors in: `medicines/`, `symptoms/`, `integrations/`, `doctor/` pages
- Patient and appointment modules are clean

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
- Public doctor directory — mock at `mock/doctors.html` — Phase E
- Public landing page
- Password reset flow (no `/auth/forgot-password` endpoint)
- Email verification flow

---

## Documentation source-of-truth rules

1. `backend/app/main.py` — active module list
2. `backend/app/modules/*/routes.py` — endpoint truth
3. `frontend/src/app/**` — implemented UI routes
4. `docs/architecture/roles-access.md` — roles and RBAC
5. `docs/planning/admin-module.md` — admin Phase A spec
6. `docs/ROADMAP.md` — product roadmap and priorities
