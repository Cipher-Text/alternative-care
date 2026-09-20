# Database Design — AltCare

> Multi-tenant SaaS database schema for alternative medicine practice management

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Multi-Tenancy Strategy](#multi-tenancy-strategy)
- [Core Entities](#core-entities)
- [User Roles & Permissions](#user-roles--permissions)
- [Doctor Specialization & Resource Filtering](#doctor-specialization--resource-filtering)
- [Integration Management](#integration-management)
- [Table Definitions](#table-definitions)
- [Indexes & Performance](#indexes--performance)
- [Data Isolation & Security](#data-isolation--security)
- [Migrations](#migrations)
- [Backup Strategy](#backup-strategy)

---

## Key Features

✅ **Multi-tenant architecture** with row-level data isolation  
✅ **4 distinct user roles** — Platform Admin, Platform Operator, Doctor/Practitioner, Receptionist/Assistant  
✅ **Multi-specialization support** — Doctors can practice 1-4 systems (Homeopathy, Ayurveda, Unani, Herbal)  
📋 **Dynamic resource filtering** — `tenant.specializations` exists on the schema, but no route/service filters medicines/books/AI by it yet (AI itself is an unbuilt 501 stub)  
✅ **Integrated SMS/Email/Payment** — Pluggable integration framework with encrypted credential storage  
✅ **Complete audit trail** — All transactions logged with request/response payloads  
📋 **Vector search with pgvector** — `embeddings` table and pgvector column exist in the schema; no code performs a similarity search yet (AI module is a 501 stub, `library` module has zero routes)  
✅ **Immutable clinical records** — Prescriptions and payments are append-only  
✅ **Flexible tagging system** — JSONB-based extensible metadata  
✅ **Doctor credentials** — Multiple degrees and training/certifications with verification support  
✅ **Bangladesh geographic system** — Division, District, Upazila hierarchy with Bengali names and geospatial data  
✅ **Bilingual support** — English/Bengali content for medicines, symptoms, and UI with language preferences  

**Total tables:** 34 (core entities + doctor credentials + geographic data + patient/appointment/clinical tables + medicine & symptom library + book library + i18n + integration framework + usage tracking)

---

## Architecture Overview

### Technology Stack

- **Database:** PostgreSQL 16
- **Extensions:**
  - `pgvector` — vector similarity search for AI/RAG embeddings
  - `pg_trgm` — trigram-based GIN indexes for fuzzy medicine/symptom search
  - Primary keys are `VARCHAR(36)` UUID strings generated in application code (Python `uuid4()`), not via a `uuid-ossp` database default; several catalog/lookup tables (medicines, symptoms, doctor credentials, geographic tables) use plain `SERIAL` integer IDs instead
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic

### Design Principles

1. **Multi-tenant isolation** — every table carries `tenant_id`, all queries are auto-scoped
2. **Audit trail** — all entities track `created_at`, `updated_at`, `created_by`, `updated_by`
3. **Soft deletes** — critical data is never hard-deleted; the current implementation uses an `is_active` boolean (patients, medicines, symptoms, books) or a `status` field (prescriptions, payments, invoices, appointments) per table rather than a shared `deleted_at` column
4. **Immutable history** — prescriptions, payments, and invoices are append-only
5. **Flexible tagging** — use JSONB for extensible metadata and tag systems
6. **Global vs. tenant data** — medicines and books can be global (admin-curated) or tenant-specific

---

## Multi-Tenancy Strategy

### Model: Shared Database, Row-Level Isolation

All tables (except global lookup data) include a `tenant_id` column. Every query filters by `tenant_id` extracted from the JWT. Cross-tenant data access is architecturally impossible.

```sql
-- Every tenant-scoped table has this structure
CREATE TABLE example (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  -- ... other columns
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_example_tenant_id ON example(tenant_id);
```

> **Note:** The codebase does not have a `deleted_at` column on any model (`app/shared/models/base.py`). Soft-delete semantics are implemented per-table via `is_active` or a `status` field instead — see the individual table definitions below.

### Why not schema-per-tenant or database-per-tenant?

- **Easier migrations** — one schema change applies to all tenants
- **Lower operational overhead** — one database to backup, monitor, and tune
- **Better resource utilization** — shared connection pool, shared buffer cache
- **Simpler queries** — no dynamic schema switching logic

**Future migration path:** If an enterprise client requires full database isolation, PostgreSQL schema-per-tenant can be adopted with minimal code changes — just point the tenant's session to `SET search_path = tenant_xyz`.

---

## Core Entities

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TENANT (Clinic / Organization)                 │
│  id, name, subdomain, subscription_plan, plan_expires_at            │
│  specializations[], integration configs (SMS, Email, Payment)       │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ├─── USERS (Doctor, Receptionists)
       │     id, tenant_id, role, email, password_hash
       │       ├─── USER_SESSIONS (refresh token tracking)
       │       ├─── DOCTOR_DEGREES (academic qualifications)
       │       │     degree_name, institution_name, completion_year
       │       └─── DOCTOR_TRAININGS (certifications, workshops)
       │             title, provider, completion_date, expiry_date
       │
       ├─── USAGE_TRACKING (per-tenant, per-day plan-limit counters)
       │
       ├─── TENANT_INTEGRATIONS (SMS, Email, Payment configs)
       │     id, tenant_id, provider_id, credentials (encrypted)
       │       └─── INTEGRATION_LOGS (transaction audit trail)
       │
       ├─── PATIENTS
       │     id, tenant_id, full_name, date_of_birth, phone, is_active
       │       ├─── PATIENT_TAGS (special_case, chronic, treatment, allergy)
       │       ├─── PATIENT_DIAGNOSES (diagnosis history, optional visit_id)
       │       ├─── APPOINTMENTS
       │       │     id, patient_id, doctor_id, appointment_date/time, status
       │       │       └─── VISITS (optional appointment_id — walk-ins have none)
       │       │             id, patient_id, doctor_id, chief_complaint, vitals
       │       │               ├─── PRESCRIPTIONS
       │       │               │     id, patient_id, visit_id, status (draft/issued/voided)
       │       │               │       └─── PRESCRIPTION_ITEMS
       │       │               │             medicine_id (nullable), medicine_name,
       │       │               │             dosage, frequency, duration
       │       │               │
       │       │               └─── PAYMENTS
       │       │                     id, patient_id, visit_id, amount, method, status
       │       │                       └─── INVOICES
       │       │                             id, payment_id, pdf_url
       │
       ├─── MEDICINES (filtered by doctor's specializations)
       │     id, tenant_id (nullable), name_en/name_bn, system, category,
       │     description_en/bn, is_global
       │       ├─── MEDICINE_ALIASES (transliteration, brand/common names)
       │       └─── MEDICINE_SYMPTOM_MAPPINGS (many-to-many, references SYMPTOMS)
       │
       ├─── SYMPTOMS (normalized master list)
       │     id, tenant_id (nullable), name_en/name_bn, category, is_global
       │       └─── SYMPTOM_ALIASES (transliteration, common names)
       │
       ├─── BOOKS (filtered by doctor's specializations)
       │     id, tenant_id (nullable), title, author, epub_url, is_global
       │       └─── CHAPTERS
       │             └─── SECTIONS
       │                   └─── EMBEDDINGS (pgvector, 1536 dimensions)
       │
       ├─── READING_PROGRESS (user_id, book_id, percentage)
       ├─── BOOKMARKS (user_id, section_id, note)
       └─── HIGHLIGHTS (user_id, section_id, start_offset, end_offset)

┌─────────────────────────────────────────────────────────────────────┐
│                    PLATFORM LEVEL (No tenant_id)                     │
└─────────────────────────────────────────────────────────────────────┘

USERS (Platform Admin, Platform Operators)
  id, tenant_id = NULL, role = 'admin' | 'operator'

GEOGRAPHIC DATA (Bangladesh administrative divisions)
  DIVISIONS (বিভাগ) — 8 administrative divisions
    └─ DISTRICTS (জেলা) — 64 districts
         └─ UPAZILAS (উপজেলা) — 490+ sub-districts
  Includes: Bengali names, coordinates, PostGIS geometry

INTEGRATION_PROVIDERS (SMS, Email, Payment provider catalog)
  id, type, provider_name, config_schema, supported_countries
  Examples: Twilio, Banglalink SMS, bKash, Nagad, Stripe, SendGrid
```

---

## User Roles & Permissions

| Role                             | `role` enum value | Scope            | Capabilities                                                                                                  |
| -------------------------------- | ----------------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| **Platform Admin**               | `admin`           | Platform-wide    | Approve doctor registrations, tenant lifecycle, KPI dashboard, role management — fully implemented (`RequireAdmin`) |
| **Platform Operator**            | `operator`        | Platform-wide    | ⚠️ Stub — the `RequireAdminOrOperator` guard exists in `app/core/dependencies.py`, but no endpoint uses it yet. No operator-specific capabilities are wired up. |
| **Doctor / Practitioner**        | `doctor`          | Tenant-scoped    | Full patient & prescription management, payments, symptom search, library, AI assistant (based on specialization) |
| **Receptionist / Assistant**     | `receptionist`    | Tenant-scoped    | ⚠️ Stub — the role string exists on `users.role`, but no RBAC guard distinguishes it from `doctor`. A receptionist currently has the same access as a doctor. |
| **Patient** _(future — Phase 5)_ | `patient`         | Self-only        | Not implemented — no `patient` role, table, or endpoints exist yet                                             |

**Implementation:**

Role is a plain `VARCHAR(50)` column (`users.role`), not a Postgres enum — see `app/shared/models/tenant.py`.

Each role has a different intended data access scope:

- **Admin, Operator:** No tenant_id (platform-level) — can see all tenants, used for approval workflows and global data curation
- **Doctor, Receptionist:** `tenant_id` from the JWT is passed into each service, which explicitly filters by it (not an automatic/global filter — see [Multi-Tenancy](multi-tenancy.md)); the `receptionist` filtering distinction is not yet enforced (see above)
- **Patient:** Planned for a future phase — no `patient` role exists today

See `docs/architecture/roles-access.md` for the authoritative, code-verified RBAC reference.

---

## Table Definitions

### 1. `tenants`

Represents a clinic or organization. Each tenant is fully data-isolated.

```sql
-- Reflects app/shared/models/tenant.py:Tenant (id is a String(36) UUID, not a native UUID column)
CREATE TABLE tenants (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20),

  -- Clinic profile
  clinic_name VARCHAR(255),
  clinic_phone VARCHAR(20),
  clinic_email VARCHAR(255),
  clinic_whatsapp VARCHAR(20),
  address_line_1 VARCHAR(255),
  address_line_2 VARCHAR(255),
  postal_code VARCHAR(10),
  landmark VARCHAR(255),
  clinic_address TEXT,  -- legacy free-text field

  -- Location (Bangladesh administrative divisions)
  division_id INTEGER REFERENCES divisions(id),
  district_id INTEGER REFERENCES districts(id),
  upazila_id INTEGER REFERENCES upazilas(id),
  latitude FLOAT,
  longitude FLOAT,

  -- Branding
  logo_url VARCHAR(500),
  description_en TEXT,
  description_bn TEXT,

  -- Professional credentials
  registration_body VARCHAR(100),      -- e.g., BMDC, Bangladesh Homeopathic Board
  registration_number VARCHAR(100),
  years_of_experience INTEGER,
  license_number VARCHAR(100),

  -- Fees (stored in paisa: 100 paisa = 1 BDT)
  consultation_fee INTEGER,
  follow_up_fee INTEGER,

  -- Specializations (1-4 of: homeopathy, ayurveda, unani, herbal)
  specializations VARCHAR(50)[] NOT NULL DEFAULT '{}',

  -- Subscription
  plan VARCHAR(20) NOT NULL DEFAULT 'free',  -- free, plus, pro
  plan_started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  plan_expires_at TIMESTAMP WITH TIME ZONE,

  -- Verification / approval (admin onboarding gate)
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verified_at TIMESTAMP WITH TIME ZONE,
  is_approved BOOLEAN NOT NULL DEFAULT FALSE,
  approved_at TIMESTAMP WITH TIME ZONE,
  approved_by VARCHAR(36),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_tenants_location ON tenants(division_id, district_id, upazila_id);
```

Integration credentials (SMS/email/payment) are **not** stored on `tenants` — they live in the separate `tenant_integrations` table (see below), encrypted with Fernet. There is no `subdomain`, `trial_ends_at`, or per-plan usage-limit column on `tenants` today; usage counters live in `usage_tracking`.

---

### 2. `users`

Doctors, operators, and admins. Patients are in a separate table (future Phase 5).

```sql
-- Reflects app/shared/models/tenant.py:User
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL for platform admins/operators

  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,

  role VARCHAR(50) NOT NULL,  -- admin, operator, doctor, receptionist

  -- Profile
  full_name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  avatar_url VARCHAR(500),
  language VARCHAR(5) NOT NULL DEFAULT 'en',  -- 'en' or 'bn'

  -- 2FA
  is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  totp_secret VARCHAR(32),

  -- Status
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  email_verified_at TIMESTAMP WITH TIME ZONE,
  last_login_at TIMESTAMP WITH TIME ZONE,

  -- JWT invalidation (incremented on password/email/role change)
  token_version INTEGER NOT NULL DEFAULT 1,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

---

### 2a. `user_sessions`

Tracks refresh-token sessions per user (used for revocation, not for `tenant_id` scoping).

```sql
-- Reflects app/shared/models/tenant.py:UserSession
CREATE TABLE user_sessions (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  refresh_token_hash VARCHAR(255) NOT NULL,
  ip_address VARCHAR(45),
  user_agent TEXT,

  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
  revoked_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);
```

The table stores a hash of the refresh token (`refresh_token_hash`), not a `jti` claim.

**Note on geographic references:** The geographic tables (divisions, districts, upazilas) are defined in section "Platform-Level Tables" below. They use INTEGER primary keys as per Bangladesh's standardized geographic coding system.

**Role assignment rules:**

- One `doctor` per tenant (primary account holder, creator of the tenant)
- Multiple `receptionist` seats allowed on Pro plan (doctor's assistants)
- `admin` and `operator` users have `tenant_id = NULL` — they belong to the platform, not a specific tenant
- Doctor can have 1-4 specializations — resources (medicines, books, symptom searches) are filtered based on active specializations

---

### 3. `doctor_degrees`

Academic degrees and qualifications earned by doctors from colleges/universities.

```sql
-- Reflects app/shared/models/doctor.py:DoctorDegree
CREATE TABLE doctor_degrees (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  user_id VARCHAR(36) NOT NULL,

  -- Degree information
  degree_type VARCHAR(100) NOT NULL,   -- e.g., "Bachelor", "Master", "Diploma", "Fellowship"
  degree_name VARCHAR(255) NOT NULL,   -- e.g., "BHMS", "BAMS", "MD (Homeopathy)"
  specialization VARCHAR(255),         -- e.g., "Pediatrics", "Dermatology"
  institution_name VARCHAR(500) NOT NULL,
  institution_location VARCHAR(255),

  start_year INTEGER,
  completion_year INTEGER NOT NULL,

  certificate_url VARCHAR(500),
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verified_at TIMESTAMP WITH TIME ZONE,
  verified_by VARCHAR(36),

  display_order INTEGER NOT NULL DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_doctor_degrees_tenant_id ON doctor_degrees(tenant_id);
CREATE INDEX idx_doctor_degrees_user_id ON doctor_degrees(user_id);
```

---

### 4. `doctor_trainings`

Professional training, certifications, workshops, and continuing education completed by doctors.

```sql
-- Reflects app/shared/models/doctor.py:DoctorTraining
CREATE TABLE doctor_trainings (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  user_id VARCHAR(36) NOT NULL,

  -- Training information
  training_type VARCHAR(100) NOT NULL,   -- e.g., "Certification", "Workshop", "Conference", "CE"
  title VARCHAR(500) NOT NULL,           -- e.g., "Advanced Homeopathic Prescribing"
  provider VARCHAR(500) NOT NULL,        -- Organization/institution that provided the training
  description TEXT,
  skills TEXT,                           -- comma-separated, not a native array

  start_date DATE,
  completion_date DATE NOT NULL,
  expiry_date DATE,                      -- for certifications that expire

  certificate_url VARCHAR(500),
  credential_id VARCHAR(255),

  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verified_at TIMESTAMP WITH TIME ZONE,
  verified_by VARCHAR(36),

  display_order INTEGER NOT NULL DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_doctor_trainings_tenant_id ON doctor_trainings(tenant_id);
CREATE INDEX idx_doctor_trainings_user_id ON doctor_trainings(user_id);
```

---

### 5. `patients`

```sql
-- Reflects app/shared/models/patient.py:Patient
CREATE TABLE patients (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),

  -- Demographics
  full_name VARCHAR(255) NOT NULL,
  date_of_birth DATE,
  gender VARCHAR(20),  -- male, female, other
  blood_group VARCHAR(10),

  -- Contact
  phone VARCHAR(20),
  email VARCHAR(255),
  whatsapp VARCHAR(20),
  address TEXT,

  -- Location (Bangladesh administrative divisions)
  division_id INTEGER,
  district_id INTEGER,
  upazila_id INTEGER,

  -- Medical information
  chief_complaint TEXT,
  medical_history TEXT,
  photo_url VARCHAR(500),
  next_visit_date DATE,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,  -- soft-delete flag

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_patients_tenant_id ON patients(tenant_id);
CREATE INDEX idx_patients_full_name ON patients(full_name);
```

There is no `patient_code`/`patient_number` column or `age`/`occupation` fields on the current model — age is derived from `date_of_birth` at the application layer, and there is no clinic-assigned patient ID format (`P-YYYY-NNNN`) implemented today.

---

### 6. `patient_tags`

Flexible tagging system for special cases, chronic conditions, treatment protocols, allergies, and custom flags.

```sql
-- Reflects app/shared/models/patient.py:PatientTag
-- tag_type values in practice: special_case, chronic, treatment, allergy
CREATE TABLE patient_tags (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,

  tag_type VARCHAR(50) NOT NULL,
  tag_value VARCHAR(255) NOT NULL,  -- the actual tag text
  notes TEXT,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_patient_tags_patient_id ON patient_tags(patient_id);
```

`tag_type` is a plain `VARCHAR`, not a Postgres enum.

---

### 7. `patient_diagnoses`

Diagnosis history for a patient, with an optional link to a visit and optional ICD code.

```sql
-- Reflects app/shared/models/patient.py:PatientDiagnosis
CREATE TABLE patient_diagnoses (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  visit_id VARCHAR(36),  -- nullable, not a DB foreign key in the current model

  description TEXT NOT NULL,
  icd_code VARCHAR(20),  -- ICD-10 code (optional)

  diagnosed_at DATE NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,  -- soft-delete flag (set false, not deleted_at)

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_by VARCHAR(36)
);

CREATE INDEX idx_patient_diagnoses_patient_id ON patient_diagnoses(patient_id);
```

---

### 7a. `appointments`

Scheduled patient appointments. Separate from `visits` — an appointment is the booking, a visit is the clinical encounter record.

```sql
-- Reflects app/shared/models/appointment.py:Appointment
CREATE TABLE appointments (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id VARCHAR(36) NOT NULL REFERENCES users(id),

  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  duration_minutes INTEGER NOT NULL DEFAULT 30,

  status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  -- scheduled, confirmed, in_progress, completed, cancelled, no_show

  reason TEXT,
  notes TEXT,
  cancelled_at DATE,
  cancellation_reason TEXT,
  reminder_sent BOOLEAN NOT NULL DEFAULT FALSE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_appointments_tenant_id ON appointments(tenant_id);
CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
```

---

### 8. `visits`

Each patient encounter. Optionally linked back to the `appointments` row that generated it (walk-ins have `appointment_id = NULL`).

```sql
-- Reflects app/shared/models/appointment.py:Visit
CREATE TABLE visits (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id VARCHAR(36) NOT NULL REFERENCES users(id),
  appointment_id VARCHAR(36) REFERENCES appointments(id) ON DELETE SET NULL,

  visit_date DATE NOT NULL,
  visit_type VARCHAR(50) NOT NULL DEFAULT 'consultation',
  -- consultation, follow_up, emergency, routine_checkup

  -- Clinical information
  chief_complaint TEXT,
  history_of_present_illness TEXT,
  examination_notes TEXT,

  -- Vitals (free-text, not structured)
  temperature VARCHAR(10),
  blood_pressure VARCHAR(20),
  pulse_rate VARCHAR(10),
  weight VARCHAR(10),

  -- Diagnosis and plan
  provisional_diagnosis TEXT,
  treatment_plan TEXT,

  -- Follow-up
  follow_up_date DATE,
  follow_up_notes TEXT,

  status VARCHAR(20) NOT NULL DEFAULT 'in_progress',  -- in_progress, completed

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_visits_tenant_id ON visits(tenant_id);
CREATE INDEX idx_visits_patient_id ON visits(patient_id);
CREATE INDEX idx_visits_doctor_id ON visits(doctor_id);
CREATE INDEX idx_visits_visit_date ON visits(visit_date DESC);
```

---

### 9. `prescriptions`

Immutable prescription records. `draft` is editable; `issued` and `voided` are not.

```sql
-- Reflects app/shared/models/prescription.py:Prescription
CREATE TABLE prescriptions (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL,
  visit_id VARCHAR(36),  -- nullable — not every prescription requires a visit record

  prescribed_by VARCHAR(36) NOT NULL,  -- doctor user id

  -- Content
  diagnosis TEXT,
  doctors_notes TEXT,
  advice TEXT,

  -- PDF generation
  pdf_url VARCHAR(500),
  pdf_generated_at VARCHAR(50),

  status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft, issued, voided

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_prescriptions_tenant_id ON prescriptions(tenant_id);
CREATE INDEX idx_prescriptions_patient_id ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_status ON prescriptions(status);
```

There is no `prescription_number`, `voided_at/voided_by/void_reason`, or `replacement_prescription_id` column in the current model — voiding just sets `status = 'voided'`.

---

### 10. `prescription_items`

Individual medicines in a prescription. Either references `medicines` table OR contains free-text medicine name.

```sql
-- Reflects app/shared/models/prescription.py:PrescriptionItem
CREATE TABLE prescription_items (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  prescription_id VARCHAR(36) NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,

  -- Medicine reference (nullable — allows free-text entry)
  medicine_id INTEGER,          -- references medicines(id) at the app layer
  medicine_name VARCHAR(500),   -- free-text, used when medicine_id is NULL

  dosage VARCHAR(255) NOT NULL,       -- "30C", "200C", "2 tablets", "5ml"
  frequency VARCHAR(255) NOT NULL,    -- "3 times daily", "Morning & Evening"
  duration VARCHAR(100),              -- "7 days", "2 weeks", "1 month"
  quantity NUMERIC(10, 2),

  instructions TEXT,
  display_order INTEGER NOT NULL DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_prescription_items_prescription_id ON prescription_items(prescription_id);
```

The "either `medicine_id` or free-text name" rule is enforced at the Pydantic/service layer, not as a database `CHECK` constraint — there is no such constraint in the Alembic migrations.

---

### 11. `medicines`

Global admin-curated medicines + tenant-specific additions.

```sql
-- Reflects app/shared/models/medicine.py:Medicine
CREATE TABLE medicines (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL for global medicines

  name_en VARCHAR(500) NOT NULL,
  name_bn VARCHAR(500),
  system VARCHAR(50) NOT NULL,  -- homeopathy, ayurveda, unani, herbal
  category VARCHAR(255),        -- system-specific, e.g. Mineral/Plant/Animal/Nosode

  description_en TEXT,
  description_bn TEXT,
  potency VARCHAR(50),          -- For homeopathy: 6C, 30C, 200C, 1M
  dosage_guidance_en TEXT,
  dosage_guidance_bn TEXT,
  indications_en TEXT,
  indications_bn TEXT,
  contraindications_en TEXT,
  contraindications_bn TEXT,

  is_global BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX ix_medicines_system ON medicines(system);
-- Trigram GIN indexes power fuzzy/partial-match search (no tsvector/search_vector column)
CREATE INDEX ix_medicines_name_en_trgm ON medicines USING gin(name_en gin_trgm_ops);
CREATE INDEX ix_medicines_name_bn_trgm ON medicines USING gin(name_bn gin_trgm_ops);
```

There is no `botanical_name`, `symptom_tags`, or `search_vector` column, and no search-vector trigger — search is done via `pg_trgm` GIN indexes on `name_en`/`name_bn` plus the `medicine_aliases` table below.

---

### 11a. `medicine_aliases`

Alternate spellings, transliterations, and brand names for a medicine — used by the search API to match local/Bengali input.

```sql
-- Reflects app/shared/models/medicine.py:MedicineAlias
CREATE TABLE medicine_aliases (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),
  medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,

  alias_en VARCHAR(500),
  alias_bn VARCHAR(500),
  alias_type VARCHAR(50) NOT NULL DEFAULT 'common_name',
  -- transliteration, common_name, brand_name, regional
  priority INTEGER NOT NULL DEFAULT 5,  -- higher = better match
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_medicine_aliases_alias_en_trgm ON medicine_aliases USING gin(alias_en gin_trgm_ops);
CREATE INDEX ix_medicine_aliases_alias_bn_trgm ON medicine_aliases USING gin(alias_bn gin_trgm_ops);
```

---

### 11b. `symptoms`

Normalized master list of symptoms, shared across all medical systems.

```sql
-- Reflects app/shared/models/symptom.py:Symptom
CREATE TABLE symptoms (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL for global symptoms

  name_en VARCHAR(500) NOT NULL,
  name_bn VARCHAR(500),
  description_en TEXT,
  description_bn TEXT,
  category VARCHAR(100),  -- respiratory, digestive, neurological, skin, mental, ...

  is_global BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_symptoms_name_en_trgm ON symptoms USING gin(name_en gin_trgm_ops);
```

---

### 11c. `symptom_aliases`

Alternate spellings/transliterations for a symptom (e.g. "matha byatha" → headache).

```sql
-- Reflects app/shared/models/symptom.py:SymptomAlias
CREATE TABLE symptom_aliases (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),
  symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,

  alias_en VARCHAR(500),
  alias_bn VARCHAR(500),
  alias_type VARCHAR(50) NOT NULL DEFAULT 'common_name',
  priority INTEGER NOT NULL DEFAULT 5,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);
```

---

### 12. `medicine_symptom_mappings`

Many-to-many mapping between `medicines` and the normalized `symptoms` table (not free-text symptom strings). Named `medicine_symptoms` in earlier drafts of this doc — the actual table is `medicine_symptom_mappings`.

```sql
-- Reflects app/shared/models/symptom.py:MedicineSymptomMapping
CREATE TABLE medicine_symptom_mappings (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) REFERENCES tenants(id),
  medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
  symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,

  modality_en TEXT,  -- "worse at night", "better from warmth"
  modality_bn TEXT,
  strength INTEGER NOT NULL DEFAULT 5,  -- 1-10, for ranking
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX ix_medicine_symptom_unique ON medicine_symptom_mappings(medicine_id, symptom_id);
```

---

### 13. `payments`

Records all patient payments. Digital payments (bKash, Nagad, etc.) are processed via configured `tenant_integrations`.

```sql
-- Reflects app/shared/models/payment.py:Payment
CREATE TABLE payments (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  patient_id VARCHAR(36) NOT NULL,
  visit_id VARCHAR(36),  -- nullable

  amount NUMERIC(10, 2) NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'BDT',
  payment_method VARCHAR(50) NOT NULL,  -- cash, bkash, nagad, rocket, card, other
  status VARCHAR(20) NOT NULL DEFAULT 'paid',  -- paid, pending, failed, refunded

  integration_log_id INTEGER,  -- references integration_logs(id) at the app layer
  transaction_id VARCHAR(255),
  description TEXT,
  payment_date DATE NOT NULL,
  received_by VARCHAR(36) NOT NULL,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_payments_tenant_id ON payments(tenant_id);
CREATE INDEX idx_payments_patient_id ON payments(patient_id);
```

---

### 14. `invoices`

```sql
-- Reflects app/shared/models/payment.py:Invoice
CREATE TABLE invoices (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  payment_id VARCHAR(36) NOT NULL,

  invoice_number VARCHAR(50) NOT NULL,  -- e.g. "INV-YYYYMM-NNNN"
  pdf_url VARCHAR(500),
  status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft, sent, paid, overdue, cancelled
  due_date DATE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE,
  created_by VARCHAR(36),
  updated_by VARCHAR(36)
);

CREATE INDEX idx_invoices_tenant_id ON invoices(tenant_id);
CREATE INDEX idx_invoices_payment_id ON invoices(payment_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
```

---

### 15. `books`

Medical book library — EPUB files with parsed chapters and sections.

```sql
CREATE TABLE books (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL for global library
  
  title VARCHAR(500) NOT NULL,
  author VARCHAR(255),
  system medical_system,  -- Which tradition this book belongs to
  language VARCHAR(50) DEFAULT 'english',
  
  -- File storage
  epub_url TEXT NOT NULL,  -- MinIO S3 URL
  cover_image_url TEXT,
  
  -- Metadata
  publisher VARCHAR(255),
  published_year INTEGER,
  isbn VARCHAR(20),
  page_count INTEGER,
  description TEXT,
  
  -- Global vs. tenant-specific
  is_global BOOLEAN DEFAULT FALSE,
  
  -- Processing status
  parsing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
  parsed_at TIMESTAMP WITH TIME ZONE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_books_tenant_id ON books(tenant_id);
CREATE INDEX idx_books_is_global ON books(is_global);
CREATE INDEX idx_books_system ON books(system);
CREATE INDEX idx_books_title ON books USING gin(to_tsvector('english', title));
```

The actual model (`app/shared/models/library.py:Book`) uses `is_active`/`is_parsed` booleans (not `deleted_at`/`parsing_status`), tracks `total_chapters`/`total_sections`/`word_count` instead of `page_count`, and has bilingual `title_en`/`title_bn` rather than a single `title` column. The book library has no routes yet — models exist but the reader is unbuilt (see `docs/ROADMAP.md` Phase C).

---

### 16. `chapters`

```sql
CREATE TABLE chapters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  
  chapter_number INTEGER NOT NULL,
  title VARCHAR(500) NOT NULL,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chapters_book_id ON chapters(book_id);
CREATE UNIQUE INDEX idx_chapters_book_number ON chapters(book_id, chapter_number);
```

---

### 17. `sections`

Parsed sections within chapters. Used for reading UI and as the chunking unit for embeddings.

```sql
CREATE TABLE sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  
  section_number INTEGER NOT NULL,
  heading VARCHAR(500),
  content TEXT NOT NULL,
  
  -- Metadata for RAG retrieval
  word_count INTEGER,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sections_chapter_id ON sections(chapter_id);
CREATE UNIQUE INDEX idx_sections_chapter_number ON sections(chapter_id, section_number);
CREATE INDEX idx_sections_content ON sections USING gin(to_tsvector('english', content));
```

---

### 18. `embeddings`

Vector embeddings for RAG — one per section.

```sql
-- Reflects app/shared/models/library.py:Embedding
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,

  -- Sized for OpenAI text-embedding-3-small (1536-dimensional); no embedding
  -- pipeline is wired up yet — the AI assistant is a 501 stub
  embedding vector(1536) NOT NULL,

  chunk_text TEXT NOT NULL,
  chunk_index INTEGER NOT NULL  -- position within the section for overlapping chunks
);

CREATE INDEX idx_embeddings_section_id ON embeddings(section_id);

-- Vector similarity index (ivfflat — not HNSW)
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

There is no `book_id` or `system` column directly on `embeddings` — filtering by book/system happens via a join through `sections → chapters → books`.

---

### 19. `reading_progress`

Per-user reading progress tracking.

```sql
CREATE TABLE reading_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  
  last_section_id UUID REFERENCES sections(id) ON DELETE SET NULL,
  progress_percentage DECIMAL(5, 2) DEFAULT 0.0,  -- 0.00 to 100.00
  
  last_read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reading_progress_user_id ON reading_progress(user_id);
CREATE INDEX idx_reading_progress_book_id ON reading_progress(book_id);
CREATE UNIQUE INDEX idx_reading_progress_user_book ON reading_progress(user_id, book_id);
```

---

### 20. `bookmarks`

User-created bookmarks within books.

```sql
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
  
  note TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_section_id ON bookmarks(section_id);
```

---

### 21. `highlights`

User-created text highlights within sections.

```sql
CREATE TABLE highlights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
  
  start_offset INTEGER NOT NULL,  -- Character offset in section.content
  end_offset INTEGER NOT NULL,
  highlighted_text TEXT NOT NULL,
  
  color VARCHAR(50) DEFAULT 'yellow',  -- For UI theming
  note TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_highlights_user_id ON highlights(user_id);
CREATE INDEX idx_highlights_section_id ON highlights(section_id);
```

---

### 22. `usage_tracking`

**Correction:** earlier drafts of this doc described tables named `ai_queries` and `notifications`. Neither exists in the codebase — there is no `ai_queries` table (the `POST /api/v1/ai/query` endpoint is a 501 stub with no persistence yet) and no `notifications` table (the `notification/` backend module is an unbuilt placeholder). What actually exists for usage/quota tracking is `usage_tracking`:

```sql
-- Reflects app/shared/models/usage.py:UsageTracking
CREATE TABLE usage_tracking (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),

  usage_date DATE NOT NULL,  -- one row per tenant per day

  -- Daily counters (reset per plan period)
  patients_added INTEGER NOT NULL DEFAULT 0,
  prescriptions_created INTEGER NOT NULL DEFAULT 0,
  ai_queries_made INTEGER NOT NULL DEFAULT 0,
  pdfs_generated INTEGER NOT NULL DEFAULT 0,

  -- Running totals (for display)
  total_patients INTEGER NOT NULL DEFAULT 0,
  total_prescriptions INTEGER NOT NULL DEFAULT 0,
  total_ai_queries_this_month INTEGER NOT NULL DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_usage_tracking_usage_date ON usage_tracking(usage_date);
```

When the AI assistant (Phase D, see `docs/ROADMAP.md`) and notification queue are actually built, they will need their own tables — this doc should be updated at that point rather than treated as already describing them.

---

## Platform-Level Tables

These tables have no `tenant_id` — they are shared across all tenants.

---

### 24. `divisions`

Bangladesh administrative divisions (বিভাগ). There are 8 divisions in Bangladesh.

```sql
-- Reflects app/shared/models/geographic.py:Division — no PostGIS extension in use
CREATE TABLE divisions (
  id SERIAL PRIMARY KEY,
  name_en VARCHAR(100) NOT NULL,
  name_bn VARCHAR(100) NOT NULL,
  latitude FLOAT,
  longitude FLOAT
);
```

**Sample data:** Dhaka (ঢাকা), Chittagong (চট্টগ্রাম), Rajshahi (রাজশাহী), Khulna (খুলনা), Barisal (বরিশাল), Sylhet (সিলেট), Rangpur (রংপুর), Mymensingh (ময়মনসিংহ)

---

### 25. `districts`

Bangladesh districts (জেলা). There are 64 districts under the 8 divisions.

```sql
-- Reflects app/shared/models/geographic.py:District
CREATE TABLE districts (
  id SERIAL PRIMARY KEY,
  division_id INTEGER NOT NULL,
  name_en VARCHAR(100) NOT NULL,
  name_bn VARCHAR(100) NOT NULL,
  latitude FLOAT,
  longitude FLOAT
);

CREATE INDEX idx_districts_division_id ON districts(division_id);
```

**Example:** Dhaka district (ঢাকা জেলা) under Dhaka division, Chittagong district (চট্টগ্রাম জেলা) under Chittagong division.

---

### 26. `upazilas`

Bangladesh sub-districts (উপজেলা). There are 490+ upazilas under the 64 districts.

```sql
-- Reflects app/shared/models/geographic.py:Upazila
CREATE TABLE upazilas (
  id SERIAL PRIMARY KEY,
  district_id INTEGER NOT NULL,
  name_en VARCHAR(100) NOT NULL,
  name_bn VARCHAR(100) NOT NULL,
  latitude FLOAT,
  longitude FLOAT
);

CREATE INDEX idx_upazilas_district_id ON upazilas(district_id);
```

**Example:** Dhanmondi (ধানমন্ডি), Mohammadpur (মোহাম্মদপুর), Gulshan (গুলশান) under Dhaka district.

**Note:** These tables use `SERIAL` (integer) primary keys, not UUID. There is no PostGIS extension, boundary-polygon (`geom`) column, or `url` slug field in the current models — only optional `latitude`/`longitude` floats.

---

### 27. `integration_providers`

Platform-level configuration for third-party integrations (SMS, Email, Payment gateways).

```sql
CREATE TYPE integration_type AS ENUM ('sms', 'email', 'payment');
CREATE TYPE integration_provider_status AS ENUM ('active', 'inactive', 'deprecated');

CREATE TABLE integration_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  type integration_type NOT NULL,
  provider_name VARCHAR(100) NOT NULL,  -- 'twilio', 'smtp', 'bkash', 'nagad', 'stripe'
  display_name VARCHAR(255) NOT NULL,    -- 'Twilio SMS', 'bKash Payment Gateway'
  
  -- Configuration schema (JSON Schema)
  config_schema JSONB NOT NULL,  -- Defines required fields for this provider
  
  -- Provider metadata
  logo_url TEXT,                 -- local frontend asset path, e.g. '/integrations/twilio.svg'
  documentation_url TEXT,
  supported_countries VARCHAR(50)[],  -- ['BD', 'IN', 'US']
  
  status integration_provider_status DEFAULT 'active',
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integration_providers_type ON integration_providers(type);
CREATE UNIQUE INDEX idx_integration_providers_name ON integration_providers(type, provider_name);

-- Current seeded provider set (Bangladesh-focused + international options)
INSERT INTO integration_providers (type, provider_name, display_name, config_schema, supported_countries) VALUES
-- SMS Providers
('sms', 'twilio', 'Twilio SMS', '{"required": ["account_sid", "auth_token", "phone_number"]}', ARRAY['US', 'BD']),
('sms', 'banglalink', 'Banglalink Bulk SMS', '{"required": ["api_key", "sender_id"]}', ARRAY['BD']),
('sms', 'robi', 'Robi SMS API', '{"required": ["username", "password", "mask"]}', ARRAY['BD']),
('sms', 'bulksmsbd', 'BulkSMSBD', '{"required": ["api_key", "sender_id", "mask_type"]}', ARRAY['BD']),

-- Email Providers
('email', 'smtp', 'SMTP Server', '{"required": ["host", "port", "username", "password"]}', ARRAY['*']),
('email', 'sendgrid', 'SendGrid', '{"required": ["api_key"]}', ARRAY['*']),
('email', 'aws_ses', 'AWS SES', '{"required": ["access_key", "secret_key", "region"]}', ARRAY['*']),

-- Payment Providers (Bangladesh)
('payment', 'bkash', 'bKash', '{"required": ["merchant_number", "app_key", "app_secret", "username", "password"]}', ARRAY['BD']),
('payment', 'nagad', 'Nagad', '{"required": ["merchant_id", "merchant_number", "public_key", "private_key"]}', ARRAY['BD']),
('payment', 'rocket', 'Rocket', '{"required": ["merchant_number", "api_key"]}', ARRAY['BD']),
('payment', 'sslcommerz', 'SSLCommerz', '{"required": ["store_id", "store_password"]}', ARRAY['BD']),

-- Payment Providers (International)
('payment', 'stripe', 'Stripe', '{"required": ["secret_key", "publishable_key", "webhook_secret"]}', ARRAY['*']);
```

Provider logos are shipped as local frontend assets in `frontend/public/integrations/`. Seeded `logo_url` values use `/integrations/*` paths so the settings UI does not depend on external vendor CDNs.

---

### 28. `tenant_integrations`

Tenant-specific integration credentials (encrypted).

```sql
CREATE TABLE tenant_integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  provider_id UUID NOT NULL REFERENCES integration_providers(id) ON DELETE CASCADE,
  
  -- Encrypted credentials (application-level encryption before storing)
  credentials JSONB NOT NULL,  -- Matches the config_schema from integration_providers
  
  -- Status
  is_enabled BOOLEAN DEFAULT TRUE,
  is_verified BOOLEAN DEFAULT FALSE,  -- Set to true after test transaction succeeds
  last_verified_at TIMESTAMP WITH TIME ZONE,
  
  -- Usage tracking
  last_used_at TIMESTAMP WITH TIME ZONE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_tenant_integrations_tenant_id ON tenant_integrations(tenant_id);
CREATE INDEX idx_tenant_integrations_provider_id ON tenant_integrations(provider_id);
CREATE UNIQUE INDEX idx_tenant_integrations_unique ON tenant_integrations(tenant_id, provider_id);
```

---

### 29. `integration_logs`

Audit log for all integration transactions (SMS sent, emails sent, payments processed).

```sql
CREATE TYPE integration_log_status AS ENUM ('pending', 'success', 'failed');

CREATE TABLE integration_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  integration_id UUID NOT NULL REFERENCES tenant_integrations(id) ON DELETE CASCADE,
  
  -- Transaction details
  transaction_type VARCHAR(50) NOT NULL,  -- 'sms_send', 'email_send', 'payment_charge', 'payment_refund'
  external_transaction_id VARCHAR(255),   -- Provider's transaction ID
  
  -- Request/Response
  request_payload JSONB,
  response_payload JSONB,
  
  -- Status
  status integration_log_status NOT NULL,
  error_message TEXT,
  
  -- Performance
  response_time_ms INTEGER,
  
  -- Metadata
  metadata JSONB,  -- {patient_id, payment_id, notification_id, etc.}
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integration_logs_tenant_id ON integration_logs(tenant_id);
CREATE INDEX idx_integration_logs_integration_id ON integration_logs(integration_id);
CREATE INDEX idx_integration_logs_status ON integration_logs(status);
CREATE INDEX idx_integration_logs_created_at ON integration_logs(created_at DESC);
CREATE INDEX idx_integration_logs_external_tx ON integration_logs(external_transaction_id) WHERE external_transaction_id IS NOT NULL;
```

---

## Indexes & Performance

### Critical indexes (already defined above)

1. **Tenant scoping:** Every tenant-scoped table has `idx_<table>_tenant_id`
2. **Foreign keys:** Key FK columns are indexed (`index=True` in the SQLAlchemy models)
3. **Fuzzy search:** `medicines.name_en/name_bn`, `medicine_aliases.alias_en/alias_bn`, `symptoms.name_en/name_bn`, `symptom_aliases.alias_en/alias_bn` use `pg_trgm` GIN indexes; `patients.full_name` is a plain indexed column, not full-text
4. **Vector search:** `embeddings.embedding` uses an `ivfflat` index for cosine similarity (not HNSW)
5. **Time-series queries:** `visits.visit_date`, `appointments.appointment_date` are indexed
6. **Status filters:** `prescriptions.status`, `payments.status`, `appointments.status` — there is no `notifications` or `ai_queries` table to index

### Additional performance optimizations

```sql
-- Composite index for common patient lookup pattern
CREATE INDEX idx_patients_tenant_name ON patients(tenant_id, full_name);

-- Composite index for dashboard queries (recent visits)
CREATE INDEX idx_visits_tenant_date ON visits(tenant_id, visit_date DESC);

-- Composite index for appointment scheduling views
CREATE INDEX idx_appointments_tenant_date ON appointments(tenant_id, appointment_date);
```

These are illustrative examples of the kind of composite indexes worth adding as query patterns emerge — check `alembic/versions/` for the indexes actually created to date.

### Query optimization guidelines

1. **Always filter by `tenant_id` first** — this massively reduces the query scan size
2. **Use LIMIT + OFFSET carefully** — for large result sets, prefer keyset pagination over offset-based
3. **Precompute aggregates** — dashboard KPIs should be cached in Redis with 5-minute TTL
4. **Avoid SELECT \*** — always specify the columns you need, especially on tables with TEXT/JSONB columns

---

## Data Isolation & Security

### Row-Level Security (future enhancement)

PostgreSQL RLS can enforce tenant isolation at the database layer:

```sql
-- Example RLS policy (not enabled by default, but shows the pattern)
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON patients
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**Current approach:** Tenant filtering is enforced in the ORM layer via a `ContextVar` set from the JWT. RLS is a future hardening layer, not a requirement for MVP.

### Encryption

- **At rest:** Enable PostgreSQL transparent data encryption (TDE) in production
- **In transit:** All connections use TLS 1.3
- **Application layer:** Sensitive fields like `patients.medical_history` can be encrypted using `pgcrypto` if required by compliance

### Backup & Disaster Recovery

- **Daily automated backups** via `pg_dump` to encrypted S3 bucket
- **Point-in-time recovery (PITR)** enabled via WAL archiving
- **Retention:** 30 days for daily backups, 12 months for monthly snapshots
- **Test restore quarterly** to verify backup integrity

---

## Migrations

### Alembic workflow

```bash
# Create a new migration
alembic revision --autogenerate -m "Add patient_tags table"

# Review the generated migration file
# Edit alembic/versions/xxxxx_add_patient_tags_table.py if needed

# Apply migration
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Migration best practices

1. **Never edit applied migrations** — always create a new migration to fix mistakes
2. **Test migrations on a copy of production data** before applying to prod
3. **Use transactions** — all DDL wrapped in `BEGIN; ... COMMIT;` (enabled by default in Alembic)
4. **Add indexes concurrently** to avoid locking large tables:
   ```sql
   CREATE INDEX CONCURRENTLY idx_example ON table(column);
   ```
5. **Backfill data in batches** — never update millions of rows in one transaction

---

## Backup Strategy

### Automated backups

```bash
# Daily full backup (runs via cron at 2 AM UTC)
pg_dump -Fc -U postgres -d altcare > /backups/altcare_$(date +%Y%m%d).dump

# Upload to S3
aws s3 cp /backups/altcare_$(date +%Y%m%d).dump s3://altcare-backups/ --storage-class GLACIER

# Delete local backups older than 7 days
find /backups -name "altcare_*.dump" -mtime +7 -delete
```

### Restore procedure

```bash
# Restore from backup
pg_restore -U postgres -d altcare_restored /backups/altcare_20240415.dump

# Verify row counts
psql -U postgres -d altcare_restored -c "SELECT COUNT(*) FROM patients;"
```

### Monitoring

- **Disk usage alerts** when DB size > 80% of allocated storage
- **Slow query log** for queries > 1000ms
- **Connection pool exhaustion** alerts
- **Replication lag** (if using read replicas)

---

### 30. `translations`

UI translations for bilingual English/Bengali support. Stores key-value pairs for all UI strings.

```sql
CREATE TABLE translations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  translation_key VARCHAR(255) NOT NULL UNIQUE,  -- e.g., 'dashboard.welcome', 'patient.add_new'
  
  -- Translations
  text_en TEXT NOT NULL,  -- English text
  text_bn TEXT NOT NULL,  -- Bengali text
  
  -- Context
  category VARCHAR(100),  -- 'ui', 'error', 'email', 'sms', 'medicine', etc.
  description TEXT,       -- Developer note about where this is used
  
  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_translations_key ON translations(translation_key);
CREATE INDEX idx_translations_category ON translations(category);
```

**Usage examples:**
- `dashboard.welcome` → "Welcome to AltCare" / "আলটকেয়ারে স্বাগতম"
- `patient.add_new` → "Add New Patient" / "নতুন রোগী যোগ করুন"
- `prescription.generate` → "Generate Prescription" / "প্রেসক্রিপশন তৈরি করুন"

**Implementation:**
- Backend: Load translations on app start, cache in Redis
- Frontend: next-intl library with JSON translation files
- Admin UI: Translation management page for updating text

---

## Doctor Specialization & Resource Filtering

### How specializations work

When a doctor registers, they select 1-4 specializations from the `medical_system` enum:

```sql
-- Example: Doctor specializing in Homeopathy only
UPDATE tenants SET specializations = ARRAY['homeopathy'] WHERE id = $1;

-- Example: Doctor practicing multiple systems
UPDATE tenants SET specializations = ARRAY['homeopathy', 'ayurveda', 'herbal'] WHERE id = $1;
```

### Resource filtering based on specialization (not implemented)

`tenant.specializations` exists in the schema, but no current route or service actually filters medicines/books/symptoms by it — `app/modules/medicine/routes.py` only filters by `is_global`/`tenant_id`. The query below shows the intended design, not shipped behavior:

```sql
-- Get medicines available to this doctor (based on specializations)
SELECT * FROM medicines
WHERE (tenant_id = $1 OR is_global = true)
  AND system = ANY(
    SELECT unnest(specializations) FROM tenants WHERE id = $1
  );

-- Get books available to this doctor
SELECT * FROM books
WHERE (tenant_id = $1 OR is_global = true)
  AND (system IS NULL OR system = ANY(
    SELECT unnest(specializations) FROM tenants WHERE id = $1
  ));

-- Symptom search scoped to doctor's specializations
SELECT m.* FROM medicines m
JOIN medicine_symptoms ms ON ms.medicine_id = m.id
WHERE (m.tenant_id = $1 OR m.is_global = true)
  AND m.system = ANY(
    SELECT unnest(specializations) FROM tenants WHERE id = $1
  )
  AND ms.symptom ILIKE ANY (ARRAY['%headache%', '%fatigue%']);
```

This ensures that a Homeopathy-only practitioner doesn't see Ayurvedic medicines in their prescription builder, and vice versa. Doctors practicing multiple systems see combined resources from all their specializations.

---

## Integration Management

### Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   INTEGRATION FRAMEWORK                       │
└──────────────────────────────────────────────────────────────┘

PLATFORM LEVEL (Admin manages):
  INTEGRATION_PROVIDERS
    ├─ SMS: Twilio, Banglalink, Robi
    ├─ Email: SMTP, SendGrid, AWS SES
    └─ Payment: bKash, Nagad, Stripe, Razorpay

TENANT LEVEL (Doctor configures):
  TENANT_INTEGRATIONS (encrypted credentials)
    ├─ Chooses providers from catalog
    ├─ Enters API keys/credentials
    └─ System validates with test transaction

USAGE TRACKING:
  INTEGRATION_LOGS
    ├─ Every SMS sent
    ├─ Every email sent
    └─ Every payment transaction
```

### SMS Integration Flow

1. **Admin adds provider** (already seeded in `integration_providers`)
2. **Doctor configures credentials** in Settings → Integrations
3. **System validates** credentials with a test message
4. **Credentials encrypted** and stored in `tenant_integrations`
5. **Notifications sent** via configured provider, logged in `integration_logs`

### Email Integration Flow

Similar to SMS — doctor chooses SMTP, SendGrid, or other provider, enters credentials, system validates with test email.

### Payment Integration Flow

1. **Doctor applies for merchant account** with bKash/Nagad/Stripe
2. **Enters credentials** in Settings → Payment Gateways
3. **System makes test ৳1 charge** (auto-refunded) to verify
4. **Credentials stored encrypted**, `is_verified = true`
5. **All payments** go through configured gateway, logged in `integration_logs`

### Common Integration Scenarios

#### Scenario 1: Doctor sets up bKash payment

```sql
-- 1. Doctor registers for bKash merchant account (done outside the system)
-- 2. Doctor enters credentials in Settings → Payment Integrations
-- 3. System creates tenant_integration record

INSERT INTO tenant_integrations (tenant_id, provider_id, credentials, is_enabled, is_verified)
VALUES (
  '123e4567-e89b-12d3-a456-426614174000',  -- Doctor's tenant_id
  (SELECT id FROM integration_providers WHERE provider_name = 'bkash'),
  encrypt_credentials('{"merchant_number": "01XXXXXXXXX", "app_key": "xxx", "app_secret": "xxx", "username": "xxx", "password": "xxx"}'),
  true,
  false  -- Not verified yet
);

-- 4. System makes test ৳1 payment to verify credentials
-- 5. If successful, set is_verified = true, last_verified_at = NOW()
-- 6. All future payments with method='bkash' go through this integration
```

#### Scenario 2: Automated appointment reminder SMS

> **Not yet implemented.** There is no `notifications` table in the codebase today (the `notification/` backend module is an unbuilt placeholder). `appointments.reminder_sent` exists as a boolean flag, but no Celery task currently sends reminders. The queries below describe how this *would* work once built, using `appointments` (not `visits`) as the source of truth for scheduled times.

```sql
-- 1. Celery worker runs daily at 8 AM to find tomorrow's appointments
SELECT a.id, p.phone, a.appointment_date, a.appointment_time
FROM appointments a
JOIN patients p ON p.id = a.patient_id
WHERE a.tenant_id = $1
  AND a.appointment_date = CURRENT_DATE + 1
  AND a.status IN ('scheduled', 'confirmed');

-- 2. For each appointment, create notification (hypothetical — table does not exist yet)
INSERT INTO notifications (tenant_id, type, recipient, body, context)
VALUES (
  $1,
  'sms',
  '01712345678',
  'Reminder: You have an appointment tomorrow at 10 AM with Dr. Rahman. - AltCare',
  '{"patient_id": "...", "visit_id": "..."}'
);

-- 3. Celery worker picks up pending notifications
SELECT * FROM notifications WHERE status = 'pending' AND type = 'sms';

-- 4. Fetch tenant's SMS integration
SELECT ti.* FROM tenant_integrations ti
JOIN integration_providers ip ON ip.id = ti.provider_id
WHERE ti.tenant_id = $1 AND ip.type = 'sms' AND ti.is_enabled = true;

-- 5. Send SMS via configured provider (Banglalink, Twilio, etc.)
-- 6. Log transaction in integration_logs
-- 7. Update notification.status = 'sent', notification.sent_at = NOW()
```

#### Scenario 3: Prescription ready email notification

> **Not yet implemented** — same caveat as Scenario 2, this uses the hypothetical `notifications` table.

```sql
-- 1. Doctor finalizes prescription, triggers PDF generation (Celery task)
-- 2. PDF generated and uploaded to MinIO
-- 3. Create email notification

INSERT INTO notifications (tenant_id, type, recipient, subject, body, context)
VALUES (
  $1,
  'email',
  'patient@example.com',
  'Your Prescription is Ready - AltCare',
  'Dear Patient, Your prescription from Dr. Rahman is now ready. View it here: [link]',
  '{"patient_id": "...", "prescription_id": "...", "pdf_url": "..."}'
);

-- 4. Worker sends email via tenant's configured email provider (SMTP, SendGrid, etc.)
-- 5. Logs transaction with response headers, message ID
-- 6. If failed (e.g., invalid email), retry up to 3 times, then mark as failed
```

### Security considerations

- Credentials in `tenant_integrations.credentials` are **encrypted at application level** using Fernet (Python) before storing
- Encryption key stored in environment variable (`INTEGRATION_ENCRYPTION_KEY`), rotated quarterly
- Payment gateway webhooks use **HMAC signature verification**
- Rate limiting on integration endpoints (e.g., max 100 SMS/hour per tenant)
- **No plain-text credentials** ever logged — `integration_logs.request_payload` redacts sensitive fields
- Webhook endpoints use tenant-specific signing keys to prevent replay attacks

---

## Appendix: Sample Queries

### Get patient's full visit history with prescriptions

```sql
SELECT 
  v.id as visit_id,
  v.visit_date,
  v.chief_complaint,
  v.provisional_diagnosis,
  p.id as prescription_id,
  p.pdf_url,
  json_agg(json_build_object(
    'medicine', COALESCE(m.name_en, pi.medicine_name),
    'dosage', pi.dosage,
    'frequency', pi.frequency,
    'duration', pi.duration
  )) as medicines
FROM visits v
LEFT JOIN prescriptions p ON p.visit_id = v.id AND p.status = 'issued'
LEFT JOIN prescription_items pi ON pi.prescription_id = p.id
LEFT JOIN medicines m ON m.id = pi.medicine_id
WHERE v.patient_id = $1
  AND v.tenant_id = $2
GROUP BY v.id, p.id
ORDER BY v.visit_date DESC;
```

### Symptom-based medicine search

```sql
SELECT 
  m.id,
  m.name,
  m.system,
  m.description,
  COUNT(ms.id) as symptom_match_count,
  AVG(ms.match_strength) as avg_match_strength
FROM medicines m
JOIN medicine_symptoms ms ON ms.medicine_id = m.id
WHERE (m.tenant_id = $1 OR m.is_global = true)
  AND ms.symptom ILIKE ANY (ARRAY['%headache%', '%nausea%', '%fatigue%'])
GROUP BY m.id
ORDER BY symptom_match_count DESC, avg_match_strength DESC
LIMIT 20;
```

### Monthly revenue report

```sql
SELECT 
  DATE_TRUNC('day', paid_at) as payment_date,
  COUNT(*) as transaction_count,
  SUM(amount) as total_revenue,
  json_object_agg(method, method_count) as payment_methods
FROM (
  SELECT 
    paid_at,
    amount,
    method,
    COUNT(*) OVER (PARTITION BY DATE_TRUNC('day', paid_at), method) as method_count
  FROM payments
  WHERE tenant_id = $1
    AND status = 'paid'
    AND paid_at >= $2  -- Start of month
    AND paid_at < $3   -- End of month
) subq
GROUP BY DATE_TRUNC('day', paid_at)
ORDER BY payment_date;
```

### RAG vector similarity search (filtered by doctor's specializations)

```sql
SELECT 
  s.id as section_id,
  s.content,
  b.title as book_title,
  c.title as chapter_title,
  1 - (e.embedding <=> $1::vector) as similarity_score
FROM embeddings e
JOIN sections s ON s.id = e.section_id
JOIN chapters c ON c.id = s.chapter_id
JOIN books b ON b.id = c.book_id
WHERE e.system = ANY(
  SELECT unnest(specializations) FROM tenants WHERE id = $2
)
ORDER BY e.embedding <=> $1::vector  -- Cosine distance (lower is better)
LIMIT 5;
```

### Get integration usage summary for a tenant

```sql
SELECT 
  ip.display_name as provider,
  il.transaction_type,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN il.status = 'success' THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN il.status = 'failed' THEN 1 ELSE 0 END) as failed,
  AVG(il.response_time_ms) as avg_response_time_ms
FROM integration_logs il
JOIN tenant_integrations ti ON ti.id = il.integration_id
JOIN integration_providers ip ON ip.id = ti.provider_id
WHERE il.tenant_id = $1
  AND il.created_at >= $2  -- Start date
  AND il.created_at < $3   -- End date
GROUP BY ip.display_name, il.transaction_type
ORDER BY total_transactions DESC;
```

---

## Summary

This database schema is designed to:

✅ **Support multi-tenancy** with full data isolation via row-level `tenant_id` filtering  
✅ **4 distinct user roles** with clear separation of platform (admin, operator) and tenant (doctor, receptionist) scopes  
⚠️ **Multi-specialization support (data model only)** — `tenant.specializations` (1-4 systems) exists on the schema, but no route or service currently filters medicines/library resources by it; only `is_global`/`tenant_id` filtering is implemented today  
✅ **Integrated SMS/Email/Payment** — pluggable provider framework with 10+ pre-configured providers (bKash, Nagad, Rocket, Twilio, etc.)  
✅ **Complete transaction audit** — every SMS, email, and payment logged with request/response payloads  
✅ **Scale to thousands of clinics** on a single PostgreSQL instance  
✅ **Enable rich clinical workflows** with flexible tagging and visit tracking  
✅ **Power AI/RAG** with vector embeddings stored natively in PostgreSQL (pgvector)  
✅ **Maintain audit trails** with automatic timestamp and user tracking on all entities  
✅ **Enforce data integrity** with foreign keys, constraints, and check conditions  
✅ **Optimize query performance** with targeted indexes and GIN/ivfflat indexes  

The schema balances **flexibility** (JSONB for extensible metadata, nullable columns for optional data) with **strictness** (immutable prescriptions, append-only status transitions).

**Total tables:** 34 — see [Key Features](#key-features) above for the full breakdown. `admin`/`operator` are platform roles with `tenant_id = NULL`; only `admin` has enforced RBAC today (see [User Roles & Permissions](#user-roles--permissions)).

**Integration providers:** SMS (Twilio, Banglalink, Robi, GP), Email (SMTP, SendGrid, AWS SES), Payment (bKash, Nagad, Rocket, Upay, Stripe, Razorpay)

It is designed to evolve incrementally — Phase 1 launches with core clinic tables, Phase 2 adds medicines, Phase 3 adds books, Phase 4 adds embeddings and integrations — without requiring destructive schema migrations.

---

## Quick Reference

### Key Design Patterns

| Pattern | Implementation | Example |
|---------|---------------|---------|
| Multi-tenancy | `tenant_id` on every table; JWT → service constructor → explicit filter | `BaseTenantService` helpers add `WHERE tenant_id = $current_tenant`; hand-written queries must add it themselves (not automatic) |
| Platform vs Tenant users | `tenant_id IS NULL` for platform users | Admin/Operator: no tenant, Doctor/Receptionist: has tenant |
| Specialization filtering | Not implemented — `tenant.specializations` exists on the schema but no query uses it | Intended: `WHERE system = ANY(tenant.specializations) OR is_global` |
| Global vs Tenant data | `is_global` flag + nullable `tenant_id` | Medicines: global pool + tenant additions |
| Immutable records | Status transitions, not UPDATE-then-delete | Prescriptions: `draft` → `issued` → `voided`, never edited once issued |
| Soft deletes | Per-table `is_active` boolean or `status` field | Filters: `WHERE is_active = true` (no shared `deleted_at` column) |
| Integration abstraction | Provider catalog + tenant config + logs | One framework for SMS, Email, Payment |
| Audit trail | `created_at`, `updated_at`, `created_by`, `updated_by` | `created_at`/`updated_at` are DB-level automatic (`server_default`/`onupdate=func.now()`); `created_by`/`updated_by` are plain nullable columns explicitly set by the service layer — no SQLAlchemy event listeners exist in the codebase |

### Common Operations Quick Reference

```sql
-- Get doctor's active specializations
SELECT specializations FROM tenants WHERE id = $tenant_id;

-- Get medicines available to a doctor (global + tenant-specific + filtered by specialization)
SELECT * FROM medicines 
WHERE (tenant_id = $1 OR is_global = true)
  AND system = ANY(SELECT unnest(specializations) FROM tenants WHERE id = $1)
  AND is_active = true;

-- Get tenant's active payment integration
SELECT ti.*, ip.display_name 
FROM tenant_integrations ti
JOIN integration_providers ip ON ip.id = ti.provider_id
WHERE ti.tenant_id = $1 
  AND ip.type = 'payment' 
  AND ti.is_enabled = true 
  AND ti.is_verified = true;

-- Create prescription with mixed medicines (DB + free-text)
INSERT INTO prescription_items (prescription_id, medicine_id, medicine_name, dosage, frequency)
VALUES 
  ($1, 42, NULL, '2 tablets', 'twice daily'),
  ($1, NULL, 'Custom Herbal Mix', '1 teaspoon', 'before bed');

-- Track monthly integration usage
SELECT 
  DATE_TRUNC('day', created_at) as date,
  COUNT(*) FILTER (WHERE status = 'success') as successful,
  COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM integration_logs
WHERE tenant_id = $1 
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date;

-- Find patients due for follow-up
SELECT p.full_name, p.phone, v.follow_up_date, v.follow_up_notes
FROM visits v
JOIN patients p ON p.id = v.patient_id
WHERE v.tenant_id = $1
  AND v.follow_up_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 7
  AND v.status = 'completed'
ORDER BY v.follow_up_date;
```

### Environment Setup Checklist

- [ ] PostgreSQL 16 installed with extensions: `pgvector`, `uuid-ossp`, `pg_trgm`
- [ ] Run migrations: `alembic upgrade head`
- [ ] Seed integration providers: `INSERT INTO integration_providers ...` (see `usage_tracking` and integration tables above)
- [ ] Create platform admin user: `role='admin', tenant_id=NULL`
- [ ] Set up encryption key: `INTEGRATION_ENCRYPTION_KEY` in `.env`
- [ ] Configure backup schedule: daily `pg_dump` to S3
- [ ] Enable connection pooling: PgBouncer or SQLAlchemy pool_size=20
