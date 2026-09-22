---
title: "Multi-Tenancy Architecture"
type: "architecture"
version: "1.0.0"
last_updated: "2026-09-21"
ai_summary: "Application-level multi-tenant isolation via explicit tenant predicates; PostgreSQL RLS is not enabled"
---

# Multi-Tenancy Architecture

Application-level row isolation using explicit tenant predicates. PostgreSQL Row-Level Security (RLS) is not enabled, and no system can guarantee zero leakage solely from this architecture.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Strategy](#strategy)
- [Implementation](#implementation)
- [Tenant Context Flow](#tenant-context-flow)
- [Code Examples](#code-examples)
- [Security Guarantees](#security-guarantees)

---

## 🌐 Overview

**Model:** Shared database, application-level row isolation (not PostgreSQL RLS)
**Method:** `tenant_id` column on all tenant-scoped tables  
**Enforcement:** Explicit `tenant_id` filtering in each service method, using a `tenant_id` passed in from `current_user.tenant_id` at the route's service-factory dependency (see [Tenant Context Flow](#tenant-context-flow) below — a `tenant_id_ctx` ContextVar exists but is not currently read anywhere)

**Benefits:**
- ✅ Easier migrations (one schema change for all tenants)
- ✅ Lower operational overhead (one database to manage)
- ✅ Better resource utilization (shared connection pool)
- ✅ Simpler queries (no dynamic schema switching)
- Explicit filters must be present in every tenant-scoped query; missing filters are a code-level risk.

---

## 🏗️ Strategy

### Shared Database vs Schema-per-Tenant vs Database-per-Tenant

| Approach | Pros | Cons | AltCare Choice |
|----------|------|------|----------------|
| **Shared DB** | Simple, efficient, easy migrations | Requires careful filtering | ✅ **Current** |
| **Schema-per-Tenant** | Better isolation, simpler queries | Complex migrations, harder to manage | Future option for enterprise |
| **DB-per-Tenant** | Maximum isolation | Very complex, expensive, migration nightmare | Not planned |

**Current:** Shared database with application-level explicit tenant filtering.
**Future:** Can migrate to schema-per-tenant if enterprise client requires it

---

## 💻 Implementation

### 1. Database Schema

**All tenant-scoped tables have:**
```sql
CREATE TABLE example (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- ... business columns ...
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);

-- Index for fast tenant filtering
CREATE INDEX idx_example_tenant_id ON example(tenant_id);
```

**Note:** There is no shared `deleted_at` column (`app/shared/models/base.py:BaseAuditModel` doesn't define one). Soft-delete semantics are implemented per-table instead — an `is_active` boolean (e.g. `patients`, `medicines`) or a `status` field (e.g. `prescriptions`, `payments`) — see `database-schema.md` for the per-table pattern.

**Tables WITHOUT tenant_id (global data):**
- `integration_providers`
- `divisions`, `districts`, `upazilas`
- `translations`

---

### 2. JWT Token Structure

**JWT Claims:**
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "doctor",
  "email": "doctor@clinic.com",
  "plan": "pro",
  "exp": 1234567890,
  "type": "access"
}
```

**Platform Users (admins, operators):**
```json
{
  "sub": "admin-uuid",
  "tenant_id": null,  // Platform identity; tenant-owned endpoints must reject this context
  "role": "admin",
  "type": "access"
}
```

---

### 3. Tenant Context Flow

```
1. Request arrives with JWT token
   ↓
2. get_current_user() dependency decodes token
   app/core/dependencies.py:get_current_user()
   ↓
3. Extract tenant_id from JWT claims
   tenant_id = payload.get("tenant_id")
   ↓
4. tenant_id_ctx.set(tenant_id)  — ContextVar defined in app/core/dependencies.py
   ↓
5. Route-level service-factory dependency constructs the service explicitly
   service = PatientService(db, tenant_id=current_user.tenant_id)
   ↓
6. Each service method filters explicitly (no automatic/global filter)
   .where(Patient.tenant_id == self.tenant_id)
   ↓
7. Return filtered results
```

**Correction — `tenant_id_ctx` is not currently used to filter queries.** It is set in `get_current_user()` (`app/core/dependencies.py`), but nothing reads it — there is no SQLAlchemy event listener, `with_loader_criteria`, or session-level hook applying it. The actual isolation mechanism is: each route depends on a small per-module "service factory" function (e.g. `get_patient_service`) that reads `current_user.tenant_id` directly and passes it into the service's constructor; every service method then writes an explicit `.where(Model.tenant_id == self.tenant_id)` clause. It works, but it is manual per-service-method filtering, not automatic ContextVar-based filtering — anyone adding a new service method must remember to add the `tenant_id` filter themselves. There is also no `app/core/context.py` module; `tenant_id_ctx` lives directly in `app/core/dependencies.py`.

---

## 🔐 Security Guarantees

### Application-Level Isolation and Its Limits

**1. Service Layer Enforcement:**
```python
class PatientService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id  # Set once at initialization
    
    async def list_patients(self):
        # Explicit tenant filter — written by hand in this method,
        # not applied automatically by a shared query layer
        query = select(Patient).where(Patient.tenant_id == self.tenant_id)
        result = await self.db.execute(query)
        return result.scalars().all()
```

**Security properties and limitations:**
- `tenant_id` comes from JWT (cryptographically signed)
- Service initialized with tenant_id from authenticated user
- Every query filters by tenant_id, but each service method must add the `.where()` clause itself — there is no shared/automatic enforcement layer, so a new method that forgets the filter would leak cross-tenant data. This pattern (per-module "service factory" + explicit filter in each method) is currently applied in `patient/routes.py`; per `roles-access.md`, it still needs to be applied consistently to appointments, prescriptions, payments, integrations, and dashboard.

---

**2. Dependency Injection (service factory):**
```python
# patient/routes.py
@router.get("/patients")
async def list_patients(
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    # service already has current_user.tenant_id
    return await service.list_patients()

def get_patient_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PatientService:
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Platform users cannot access tenant data.")
    return PatientService(db=db, tenant_id=current_user.tenant_id)
```

**Why it's secure:**
- `current_user` populated from JWT token
- Service gets `tenant_id` from authenticated user
- No manual tenant_id parameter (can't be manipulated by client)
- Platform users (`tenant_id is None`) are explicitly rejected with 403 before a service is ever constructed

---

**3. Database Constraints:**
```sql
-- Foreign key ensures tenant_id exists
tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE

-- Index optimizes tenant filtering
CREATE INDEX idx_patients_tenant_id ON patients(tenant_id);
```

**Why it's secure:**
- Can't insert row without valid tenant_id
- CASCADE delete prevents orphaned records
- Fast lookups via index

---

## 📝 Code Examples

### Example 1: Patient CRUD

```python
from app.modules.patient.service import PatientService
from app.shared.schemas.patient import PatientCreate

# In route handler
@router.post("/patients")
async def create_patient(
    data: PatientCreate,
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    # Service already scoped to current_user.tenant_id
    patient = await service.create_patient(data, created_by=current_user.id)
    return patient

# In service.py
async def create_patient(
    self, data: PatientCreate, created_by: str
) -> Patient:
    # Automatic tenant_id from self.tenant_id
    patient = Patient(
        **data.dict(),
        tenant_id=self.tenant_id,  # From JWT
        created_by=created_by
    )
    self.db.add(patient)
    await self.db.commit()
    await self.db.refresh(patient)
    return patient
```

---

### Example 2: Cross-Tenant Query (404 Not Found)

```python
# Tenant A tries to access Tenant B's patient
# Patient ID exists in database but belongs to Tenant B

@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    service: Annotated[PatientService, Depends(get_patient_service)]
):
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# In service.py
async def get_patient(self, patient_id: str) -> Patient | None:
    # Explicit tenant filter
    query = select(Patient).where(
        Patient.id == patient_id,
        Patient.tenant_id == self.tenant_id,  # Tenant A's ID
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()  # Returns None (not Tenant B's patient)
```

**Result:** 404 Not Found (security through obscurity - looks like doesn't exist)

---

### Example 3: Explicitly Authorized Platform Operations

```python
# Platform admin services may perform authorized platform operations.
# This is separate from tenant clinical access and must be role-gated.
class PlatformService:
    def __init__(self, db: AsyncSession):
        self.db = db  # No tenant_id filtering
    
    async def list_all_tenants(self) -> list[Tenant]:
        query = select(Tenant).where(Tenant.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def approve_doctor(self, user_id: str) -> User:
        # Can access any tenant's user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            user.is_verified = True
            await self.db.commit()
        return user
```

**Access Control:**
```python
from app.core.dependencies import RequireAdmin

@router.get("/admin/tenants")
async def list_tenants(current_user: RequireAdmin):
    # RequireAdmin = Annotated[CurrentUser, Depends(require_role("admin"))]
    # This only checks current_user.role == "admin" — it does not independently
    # verify tenant_id is None (that's guaranteed by how admin accounts are created,
    # not re-checked at request time).
    ...
```

---

## 🧪 Testing Multi-Tenant Isolation

**Critical test pattern:**
```python
@pytest.mark.asyncio
async def test_tenant_isolation(db_session):
    # Create two tenants (email is required/unique on Tenant)
    tenant_a = Tenant(id=str(uuid4()), name="Clinic A", email="a@example.com")
    tenant_b = Tenant(id=str(uuid4()), name="Clinic B", email="b@example.com")
    db_session.add_all([tenant_a, tenant_b])
    
    # Create patient for Tenant A (Patient uses full_name, not first/last_name)
    patient_a = Patient(
        id=str(uuid4()),
        tenant_id=tenant_a.id,
        full_name="John Doe",
    )
    db_session.add(patient_a)
    await db_session.commit()
    
    # Try to query with Tenant B context
    service_b = PatientService(db_session, tenant_id=tenant_b.id)
    patients = await service_b.list_patients()
    
    # Should return empty (no cross-tenant access)
    assert len(patients) == 0
    
    # Try to get by ID with Tenant B context
    patient = await service_b.get_patient(patient_a.id)
    
    # Should return None
    assert patient is None
```

**Test all modules for tenant isolation!**

---

## 🤖 AI Quick Reference

**Q: How does multi-tenancy work?**
→ Row-level isolation: `tenant_id` from the JWT is passed into each service, and each service method explicitly filters by it

**Q: Can Tenant A access Tenant B's data?**
→ Not through the modules that follow the pattern correctly (queries filter by tenant_id from JWT). This is enforced per service method, not by a global/automatic filter, so it depends on every method remembering the `.where()` clause.

**Q: What happens if I try to access another tenant's record?**
→ Returns 404 Not Found (looks like doesn't exist)

**Q: How do platform admins access platform records?**
→ Through platform-admin endpoints guarded by the platform role. A null tenant is not implicit authorization for clinical records.

**Q: Where is tenant_id extracted from?**
→ JWT token decoded in `get_current_user()` (`app/core/dependencies.py`), then passed explicitly into each service's constructor

**Q: Can I bypass tenant filtering?**
→ Yes, accidentally — if a new service method omits the `.where(Model.tenant_id == self.tenant_id)` clause, nothing else catches it. There is no shared/automatic enforcement layer today.

---

**See Also:**
- [Authentication](authentication.md) - JWT token structure
- [Database Schema](database-schema.md) - tenant_id on tables
- [Roles & Access](roles-access.md) - RBAC and the tenant-isolation guard pattern

---

**Last Updated:** 2026-09-21  
**Security:** Application-level isolation relies on explicit per-method `tenant_id` filtering; PostgreSQL RLS is not enabled.
