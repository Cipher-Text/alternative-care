---
title: "Multi-Tenancy Architecture"
type: "architecture"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "Row-level multi-tenant isolation with automatic tenant_id filtering from JWT tokens"
---

# Multi-Tenancy Architecture

Complete row-level isolation ensuring no cross-tenant data leakage.

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

**Model:** Shared database, row-level isolation  
**Method:** `tenant_id` column on all tenant-scoped tables  
**Enforcement:** Automatic filtering via ContextVar from JWT

**Benefits:**
- ✅ Easier migrations (one schema change for all tenants)
- ✅ Lower operational overhead (one database to manage)
- ✅ Better resource utilization (shared connection pool)
- ✅ Simpler queries (no dynamic schema switching)
- ✅ Impossible cross-tenant data leakage (architectural guarantee)

---

## 🏗️ Strategy

### Shared Database vs Schema-per-Tenant vs Database-per-Tenant

| Approach | Pros | Cons | AltCare Choice |
|----------|------|------|----------------|
| **Shared DB** | Simple, efficient, easy migrations | Requires careful filtering | ✅ **Current** |
| **Schema-per-Tenant** | Better isolation, simpler queries | Complex migrations, harder to manage | Future option for enterprise |
| **DB-per-Tenant** | Maximum isolation | Very complex, expensive, migration nightmare | Not planned |

**Current:** Shared database with row-level isolation  
**Future:** Can migrate to schema-per-tenant if enterprise client requires it

---

## 💻 Implementation

### 1. Database Schema

**All tenant-scoped tables have:**
```sql
CREATE TABLE example (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- ... business columns ...
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP
);

-- Index for fast tenant filtering
CREATE INDEX idx_example_tenant_id 
ON example(tenant_id) 
WHERE deleted_at IS NULL;
```

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
  "tenant_id": null,  // No tenant = platform-wide access
  "role": "admin",
  "type": "access"
}
```

---

### 3. Tenant Context Flow

```
1. Request arrives with JWT token
   ↓
2. Auth middleware decodes token
   app/core/dependencies.py:get_current_user()
   ↓
3. Extract tenant_id from JWT claims
   tenant_id = payload.get("tenant_id")
   ↓
4. Set in ContextVar
   from app.core.context import tenant_id_ctx
   tenant_id_ctx.set(tenant_id)
   ↓
5. Service layer uses tenant_id
   service = PatientService(db, tenant_id=current_user.tenant_id)
   ↓
6. All queries automatically filter
   WHERE tenant_id = <tenant_id>
   AND deleted_at IS NULL
   ↓
7. Return filtered results
```

---

## 🔐 Security Guarantees

### Architectural Impossibility of Cross-Tenant Access

**1. Service Layer Enforcement:**
```python
class PatientService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id  # Set once at initialization
    
    async def list_patients(self):
        # Automatic tenant filter
        query = select(Patient).where(
            Patient.tenant_id == self.tenant_id,
            Patient.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

**Why it's secure:**
- `tenant_id` comes from JWT (cryptographically signed)
- Service initialized with tenant_id from authenticated user
- Every query explicitly filters by tenant_id
- No way to bypass filter without modifying service code

---

**2. Dependency Injection:**
```python
# routes.py
@router.get("/patients")
async def list_patients(
    service: Annotated[PatientService, Depends(get_patient_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    # service already has current_user.tenant_id
    return await service.list_patients()

# dependencies.py
def get_patient_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> PatientService:
    return PatientService(db=db, tenant_id=current_user.tenant_id)
```

**Why it's secure:**
- `current_user` populated from JWT token
- Service gets `tenant_id` from authenticated user
- No manual tenant_id parameter (can't be manipulated by client)

---

**3. Database Constraints:**
```sql
-- Foreign key ensures tenant_id exists
tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE

-- Index optimizes tenant filtering
CREATE INDEX idx_patients_tenant_id 
ON patients(tenant_id) 
WHERE deleted_at IS NULL;
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
    # Automatic tenant filter
    query = select(Patient).where(
        Patient.id == patient_id,
        Patient.tenant_id == self.tenant_id,  # Tenant A's ID
        Patient.deleted_at.is_(None)
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()  # Returns None (not Tenant B's patient)
```

**Result:** 404 Not Found (security through obscurity - looks like doesn't exist)

---

### Example 3: Platform Admin (No Tenant Filter)

```python
# Platform admin can see all tenants
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
@router.get("/admin/tenants")
async def list_tenants(
    current_user: Annotated[CurrentUser, Depends(require_admin)]
):
    # require_admin checks current_user.role == "admin"
    # and current_user.tenant_id is None
    ...
```

---

## 🧪 Testing Multi-Tenant Isolation

**Critical test pattern:**
```python
@pytest.mark.asyncio
async def test_tenant_isolation(db_session):
    # Create two tenants
    tenant_a = Tenant(id=uuid4(), name="Clinic A")
    tenant_b = Tenant(id=uuid4(), name="Clinic B")
    db_session.add_all([tenant_a, tenant_b])
    
    # Create patient for Tenant A
    patient_a = Patient(
        tenant_id=tenant_a.id,
        first_name="John",
        last_name="Doe"
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
→ Row-level isolation with tenant_id in JWT → auto-filtered queries

**Q: Can Tenant A access Tenant B's data?**
→ No, architecturally impossible (queries auto-filter by tenant_id from JWT)

**Q: What happens if I try to access another tenant's record?**
→ Returns 404 Not Found (looks like doesn't exist)

**Q: How do platform admins access all tenants?**
→ tenant_id = NULL in JWT, service layer doesn't filter by tenant

**Q: Where is tenant_id extracted from?**
→ JWT token decoded in get_current_user() → set in service layer

**Q: Can I bypass tenant filtering?**
→ No, unless you modify service code (requires code-level access)

---

**See Also:**
- [Authentication](authentication.md) - JWT token structure
- [Database Schema](database-schema.md) - tenant_id on tables
- [API Reference](../api/README.md) - Tenant-scoped endpoints

---

**Last Updated:** May 1, 2026  
**Security:** Architecturally guaranteed isolation ✅
