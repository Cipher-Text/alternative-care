# Roles & Access Control

**Authoritative reference** — code must match this document.  
Last updated: 2026-07-11

---

## Role taxonomy

There are two levels: **Platform** (no tenant) and **Tenant** (scoped to one clinic).

| Role | Level | `tenant_id` in JWT | Implemented? |
|---|---|---|---|
| `admin` | Platform | `null` | ✅ Full |
| `operator` | Platform | `null` | ⚠️ Stub — defined in RBAC, no endpoints yet |
| `doctor` | Tenant | `<uuid>` | ✅ Full |
| `receptionist` | Tenant | `<uuid>` | ⚠️ Stub — role string exists, no RBAC enforcement |

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
| Integration provider catalog | ✅ Write *(planned)* |
| Manage platform operators | ✅ Write *(planned)* |
| View audit / activity log | ✅ Read *(planned)* |

Backend guard: `RequireAdmin` — enforces `role == "admin"`.

### `operator`
Read-only platform staff. Cannot mutate tenants or provision accounts.

| Area | Access |
|---|---|
| List / view all tenants | ✅ Read *(planned)* |
| Platform KPI dashboard | ✅ Read *(planned)* |
| View audit log | ✅ Read *(planned)* |
| Provision / approve / suspend | ❌ Forbidden |

Backend guard: `RequireAdminOrOperator` — enforces `role in ("admin", "operator")`.  
**Status:** RBAC guard is coded but zero endpoints currently use it. Will be wired up in Platform Admin Phase B.

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
| Integrations | ✅ |

Backend guard: `RequireDoctor` or `CurrentUser` (any authenticated tenant user).

### `receptionist`
Front-desk / administrative role. Clinical write operations are restricted.

| Area | Access |
|---|---|
| Patients — Read | ✅ *(planned enforcement)* |
| Appointments — Read + Write | ✅ *(planned enforcement)* |
| Prescriptions — Read only | ✅ *(planned enforcement)* |
| Payments — Read + Write | ✅ *(planned enforcement)* |
| Profile / Clinic | ✅ Read *(planned enforcement)* |
| Medicines / Prescriptions write | ❌ *(planned enforcement)* |

**Status:** Role string stored in DB. No RBAC guards distinguish it from `doctor` yet. Will be enforced in Platform Admin Phase B.

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
**Must be applied to:** appointments, prescriptions, payments, integrations, dashboard — all tenant-scoped service factories.

---

## Seeded accounts (development)

| Email | Role | Level | Password |
|---|---|---|---|
| `admin@altcare.com` | `admin` | Platform | `Admin@1234` |
| `operator@altcare.com` | `operator` | Platform | `Operator@1234` |
| `dr.rahman@example.com` | `doctor` | Tenant | `Test@1234` |
