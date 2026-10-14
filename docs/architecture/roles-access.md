# Roles & Access Control

**Authoritative reference** — code must match this document.  
Last updated: 2026-07-11

---

> **Dynamic roles (ADR 010, Phases 1 to 4 built 2026-10-14).** Roles and permissions are stored as data
> (`roles`, `permissions`, `user_roles`) and every route is guarded by permission, not by role name. The four roles
> below are the *system roles*: their permission sets reproduce exactly what is described here (pinned by
> `tests/unit/test_permissions.py`, and route by route by `tests/golden/access_matrix.json`). Only the platform
> adds staff and creates or assigns roles (a clinic sees its team read-only at `/team` and contacts AltCare for changes; a platform
> admin manages a clinic at `/admin/clients/{id}/team` and the platform's own staff at `/admin/staff`); a person's access is the union of their roles. Read this
> document as the default each system role starts from. See `docs/architecture/adr/010-dynamic-roles-and-permissions.md`.

## Role taxonomy

There are two levels: **Platform** (no tenant) and **Tenant** (scoped to one clinic).

| Role | Level | `tenant_id` in JWT | Implemented? |
|---|---|---|---|
| `admin` | Platform | `null` | ✅ Full |
| `operator` | Platform | `null` | ✅ Read-only — enforced on all platform-admin GET endpoints |
| `doctor` | Tenant | `<uuid>` | ✅ Full |
| `receptionist` | Tenant | `<uuid>` | ✅ Enforced (2026-10-10) — read-only on clinical records, see matrix below |

**Platform users** (`tenant_id = null`) cannot access any tenant-scoped data.  
All clinical modules (`/patients`, `/appointments`, `/prescriptions`, etc.) reject platform users with **403**.

---

## Platform roles

### `admin`
Full platform control. Created manually by seeding or by another admin.

| Area | Access |
|---|---|
| Provision tenant + doctor | ✅ Write |
| List / view all tenants | ✅ Read |
| Approve pending tenants | ✅ Write |
| Suspend / reactivate tenant | ✅ Write *(planned)* |
| Change tenant plan | ✅ Write *(planned)* |
| Platform KPI dashboard | ✅ Read *(planned)* |
| Global medicine catalog | ✅ Write *(planned)* |
| Manage platform operators | ✅ Write *(planned)* |
| View audit / activity log | ✅ Read *(planned)* |

Backend guard: `RequireAdmin` — enforces `role == "admin"`.

### `operator`
Read-only platform staff. Cannot mutate tenants or provision accounts.

| Area | Access |
|---|---|
| List / view all tenants | ✅ Read |
| View tenant detail / usage | ✅ Read |
| Platform KPI dashboard | ✅ Read |
| List users (role distribution) | ✅ Read |
| View audit log | ✅ Read *(planned — no audit log endpoint exists yet)* |
| Provision / approve / suspend tenant | ❌ Forbidden (`RequireAdmin`) |
| Add doctor to tenant | ❌ Forbidden (`RequireAdmin`) |
| Change user role / status | ❌ Forbidden (`RequireAdmin`) |

Backend guard: `RequireAdminOrOperator` — enforces `role in ("admin", "operator")`.  
**Status:** wired up on all 6 read-only endpoints in `admin/routes.py` (`GET /dashboard`, `GET /tenants`, `GET /tenants/pending`, `GET /tenants/{id}`, `GET /tenants/{id}/usage`, `GET /users`). The 5 write endpoints remain `RequireAdmin`-only. Frontend `/admin/*` pages mirror this: operators see the same read views as admins, with write controls (provision, approve, add doctor, edit user) hidden.

---

## Tenant roles

### `doctor`
Primary practitioner. Full access to all clinical data within their tenant.

| Area | Access |
|---|---|
| Patients — CRUD | ✅ |
| Appointments — CRUD | ✅ |
| Prescriptions — CRUD | ✅ |
| Payments — CRUD | ✅ |
| Own profile, degrees, trainings | ✅ |
| Clinic/tenant profile | ✅ Read + Write |
| Medicines / Symptoms library | ✅ |
| Messaging (SMS/email credits, send, log) | ✅ |

Backend guard: `RequireDoctor` or `CurrentUser` (any authenticated tenant user).

### `receptionist`
Front-desk / administrative role. Clinical records are read-only; scheduling and payments are full.

| Area | Access | Enforcement |
|---|---|---|
| Patients | Read | writes blocked (router guard) |
| Appointments | Read + Write | none needed |
| Visits (clinical notes) | Read | writes blocked |
| Prescriptions | Read, and print (PDF) | create/edit/issue/void blocked; `GET /pdf` is a read |
| Payments & invoices | Read + Write | none needed |
| Medicines / Symptoms library | Read | writes blocked |
| Clinic profile (`/tenant`) | Read | writes blocked |
| Dashboard | Read | — |
| Doctor profile, degrees, trainings | None | blocked entirely |
| Messaging (send SMS/email, message log) | None | blocked entirely |
| AI assistant | None | blocked entirely |

Errors are `403` with `detail = {"code": "role_not_permitted", "message": ...}`. A receptionist
does **not** use a practitioner seat (`max_seats` counts active doctors only).

**Implementation:** two router-level guards in `app/core/dependencies.py`, wired in `app/main.py`
(and on the visits router): `deny_receptionist_writes` (anything but GET/HEAD/OPTIONS) and
`deny_receptionist` (everything). Because they sit on the router, a write route added later is
protected automatically. The frontend hides
the matching controls via `useCan()` (`src/lib/auth/permissions.ts`); the server is the authority.

**Open product questions (defaults chosen, change in one place):**
- Patient creation is blocked for receptionists, per this document's original matrix. Many clinics
  want the front desk to register walk-ins; allowing it is one change (move `patient_router` from
  `deny_receptionist_writes` to no guard, or carve out `POST /patients`).
- SMS/email sending is blocked together with messaging; reminders are a front-desk task.
- There is no endpoint yet to create a receptionist (only the seed). A doctor-side "invite staff"
  flow is the missing piece.

---

## RBAC implementation

All guards live in `backend/app/core/dependencies.py`.

```python
RequireAdmin         = Annotated[CurrentUser, Depends(require_role("admin"))]
RequireAdminOrOperator = Annotated[CurrentUser, Depends(require_role("admin", "operator"))]
RequireDoctor        = Annotated[CurrentUser, Depends(require_role("doctor"))]
```

`require_role()` is a dependency factory. Any combination is possible:
```python
Depends(require_role("doctor", "receptionist"))   # both tenant roles
Depends(require_role("admin", "operator"))        # both platform roles
```

`get_current_user()` validates JWT, checks token_version (invalidated on password/role change), and populates `CurrentUser`. `tenant_id` is `None` for platform users.

---

## Tenant isolation guard pattern

Every tenant-scoped service dependency must check for platform users:

```python
def get_patient_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PatientService:
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Platform users cannot access tenant data.")
    return PatientService(db=db, tenant_id=current_user.tenant_id)
```

This pattern is applied in: `patient/routes.py`.  
**Must be applied to:** appointments, prescriptions, payments, messaging, dashboard — all tenant-scoped service factories.

---

## Seeded accounts (development)

| Email | Role | Level | Password |
|---|---|---|---|
| `admin@altcare.com` | `admin` | Platform | `Admin@1234` |
| `operator@altcare.com` | `operator` | Platform | `Operator@1234` |
| `dr.rahman@example.com` | `doctor` | Tenant | `Test@1234` |
