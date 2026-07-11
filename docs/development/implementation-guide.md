# Implementation Guide

Step-by-step patterns for adding features to AltCare.

---

## Add a Backend Endpoint

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

---

## Database Migration

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

---

## Add a Frontend Feature

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

---

## Seed Data

```bash
cd backend && ./scripts/run_seed.sh
```

Seeds:
- Bangladesh geographic data (8 divisions, 64 districts, upazilas)
- Integration providers (12: SMS, Email, Payment, with local logo paths)
- UI translations (80+ English/Bengali)
- Sample tenants/users (dev only)
