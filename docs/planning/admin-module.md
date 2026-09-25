# Platform Admin Module — Implementation Spec

**Status:** Phase A shipped (2026-07-11) — Phase A2 extended 2026-07-12 with tenant-doctor
provisioning. Phase B (operator RBAC, receptionist enforcement) is still Planning.
**Last updated:** 2026-09-24

---

## Goal

Give the platform admin a dedicated module (`app/modules/admin/`) with proper navigation,
a dashboard, and full tenant lifecycle controls. This has been delivered — `app/modules/admin/`
now holds 11 endpoints (`routes.py`, `service.py`, `schemas.py`) registered at `/api/v1/admin`
(the 11th, `GET /admin/tenants/{id}/usage`, shipped 2026-09-24 as part of Stage 1 "Billing
enforcement"), replacing the old prototype (5 endpoints buried in `auth/routes.py`, one nav link).
The legacy `/auth/admin/*` endpoints (5, buried in `auth/routes.py`, one nav link) have since been
removed (2026-09-25, see Roadmap item 3) — the frontend had already fully migrated.

---

## Current state (baseline, pre-Phase A — kept for history)

### Backend
Originally all admin endpoints lived in `backend/app/modules/auth/routes.py` (lines 55–131):

| Endpoint | What it does |
|---|---|
| `POST /auth/admin/provision-client` | Create tenant + primary doctor |
| `GET /auth/admin/clients` | List all tenants |
| `GET /auth/admin/clients/{id}` | Tenant detail + doctor users |
| `GET /auth/admin/tenants/pending` | Self-registered awaiting approval |
| `POST /auth/admin/tenants/{id}/approve` | Approve a pending tenant |

These paths still work (compatibility shim) but are superseded by `app/modules/admin/routes.py`
below.

### Frontend (pre-Phase A)
- `frontend/src/app/(dashboard)/admin/clients/page.tsx` — 3-tab page
- `frontend/src/app/(dashboard)/admin/clients/[tenantId]/page.tsx` — detail view
- Sidebar: one item "Admin Clients" appended to the doctor nav

---

## Phase A — Foundation  *(do this first)*

### A1: Extract admin backend into its own module

Create `backend/app/modules/admin/` with:
- `__init__.py`
- `routes.py`
- `service.py` (extract admin service logic out of `AuthService`)
- `schemas.py` (admin-specific Pydantic models)

Register in `main.py` at prefix `/api/v1/admin`.

**Keep the old `/auth/admin/*` paths working** via redirect or alias until frontend is updated,
then remove them.

### A2: New backend endpoints

Add to `app/modules/admin/routes.py`:

```
GET  /admin/dashboard          Platform KPIs (tenant count, doctor count, pending count)
GET  /admin/tenants            List all tenants (replaces /auth/admin/clients)
POST /admin/tenants            Provision tenant + doctor (replaces /auth/admin/provision-client)
GET  /admin/tenants/pending    Pending approvals (replaces /auth/admin/tenants/pending)
GET  /admin/tenants/{id}       Tenant detail + doctors (replaces /auth/admin/clients/{id})
POST /admin/tenants/{id}/approve  Approve (replaces /auth/admin/tenants/{id}/approve)
PATCH /admin/tenants/{id}      Update plan / suspend / reactivate   ← NEW
POST /admin/tenants/{id}/doctors  Add another doctor user under this tenant   ← SHIPPED 2026-07-12
```

All guarded by `RequireAdmin`.

**`PATCH /admin/tenants/{id}` payload:**
```json
{
  "plan": "free | plus | pro",
  "is_active": true | false,
  "is_approved": true | false
}
```

**`GET /admin/dashboard` response:**
```json
{
  "total_tenants": 12,
  "active_tenants": 10,
  "pending_approvals": 2,
  "total_doctors": 18,
  "plans": { "free": 6, "plus": 3, "pro": 3 }
}
```

### A3: Frontend — separate admin nav and layout

**Sidebar change** (`frontend/src/components/layout/Sidebar.tsx`):

When `role === 'admin'`, show **only** the admin navigation (not the doctor nav).
Platform admins see no Patients / Appointments / Prescriptions links — those are irrelevant to them.

Admin navigation items:
```
Platform Dashboard   /admin/dashboard
Clients              /admin/clients
Pending Approvals    /admin/pending   (badge: count)
```

### A4: Frontend pages

**New: `/admin/dashboard`**  
Platform KPI cards:
- Total tenants / Active tenants / Pending approvals
- Total doctors
- Plan breakdown (free / plus / pro)

Call `GET /api/v1/admin/dashboard`.

**Updated: `/admin/clients`**  
- Keep existing 3-tab structure (Directory / Provision / Pending)
- Update API calls to new `/admin/tenants` paths
- Add **tenant actions** in the directory table:
  - Change plan (inline select or modal)
  - Suspend / reactivate (button toggle)

**Updated: `/admin/clients/[tenantId]`**  
- Keep existing detail layout
- Add action buttons: Change plan, Suspend, Reactivate

### A5: Migration

No new tables needed. The `tenants` table already has `is_active`, `is_approved`, `plan`.
No migration required for Phase A.

---

## Phase B — Operator role  *(after Phase A)*

**Decision:** Implement `operator` as a read-only platform user.

### B1: Backend
- All `GET` endpoints in `admin/routes.py` change guard from `RequireAdmin` to `RequireAdminOrOperator`
- `POST` / `PATCH` endpoints stay `RequireAdmin` only
- No new tables needed

### B2: Frontend
- Sidebar detects `role === 'operator'` → show read-only admin nav (no Provision tab, no action buttons)
- Disable Provision tab, Change Plan, Suspend buttons when `role === 'operator'`

### B3: Receptionist (tenant-level)
- Add `require_role("doctor", "receptionist")` to patient read endpoints
- Keep write endpoints as `RequireDoctor` only
- This is mostly a backend RBAC change; frontend already hides write actions for non-doctors if `role` is checked

---

## Phase C — Content & Ops  *(future)*

| Feature | Backend | Frontend |
|---|---|---|
| Global medicine admin (set `is_global=true`) | Extend medicine module | Admin medicines tab |
| Integration provider catalog CRUD | Extend integration module | Admin providers tab |
| Platform activity / audit log | New `admin_logs` table | Admin logs tab |
| Platform operators management | Extend admin module | Admin team tab |

---

## File checklist for Phase A

### Backend
- [x] `backend/app/modules/admin/__init__.py`
- [x] `backend/app/modules/admin/routes.py`
- [x] `backend/app/modules/admin/service.py`
- [x] `backend/app/modules/admin/schemas.py`
- [x] `backend/app/main.py` — register admin router at `/api/v1/admin`
- [x] `backend/app/modules/auth/routes.py` — old `/auth/admin/*` endpoints removed (2026-09-25, see `docs/ROADMAP.md` item 3)
- [x] `backend/tests/integration/test_admin_tenant_doctors.py` — NEW, covers `POST /admin/tenants/{id}/doctors` (shipped 2026-07-12)

### Frontend
- [x] `frontend/src/lib/api/admin.ts` — update API paths to `/admin/...`
- [x] `frontend/src/lib/hooks/useAdminClients.ts` — update hook paths
- [x] `frontend/src/components/layout/Sidebar.tsx` — separate admin nav
- [x] `frontend/src/app/(dashboard)/admin/dashboard/page.tsx` — NEW platform dashboard
- [x] `frontend/src/app/(dashboard)/admin/clients/page.tsx` — add tenant actions
- [x] `frontend/src/app/(dashboard)/admin/clients/[tenantId]/page.tsx` — add action buttons + add-doctor form (2026-07-12)

---

## Conventions to follow

- New admin endpoints use `RequireAdmin` (not `CurrentUser`)
- Admin service methods must NOT accept `tenant_id` — platform data is unscoped
- Response schemas live in `admin/schemas.py`, not in `auth/schemas.py`
- Frontend admin pages redirect non-admins to `/dashboard` with an error card (pattern already in place)
- No new migrations needed for Phase A
