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
✅ **Dynamic resource filtering** — Medicines, books, and AI responses filtered by doctor's active specializations  
✅ **Integrated SMS/Email/Payment** — Pluggable integration framework with encrypted credential storage  
✅ **Complete audit trail** — All transactions logged with request/response payloads  
✅ **Vector search with pgvector** — Native PostgreSQL embeddings for RAG/AI assistant  
✅ **Immutable clinical records** — Prescriptions and payments are append-only  
✅ **Flexible tagging system** — JSONB-based extensible metadata  
✅ **Doctor credentials** — Multiple degrees and training/certifications with verification support  
✅ **Bangladesh geographic system** — Division, District, Upazila hierarchy with Bengali names and geospatial data  

**Total tables:** 29 (core entities + doctor credentials + geographic data + integration framework)

---

## Architecture Overview

### Technology Stack

- **Database:** PostgreSQL 16
- **Extensions:**
  - `pgvector` — vector similarity search for AI/RAG embeddings
  - `uuid-ossp` — UUID generation
  - `pg_trgm` — trigram-based text search for fuzzy matching
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic

### Design Principles

1. **Multi-tenant isolation** — every table carries `tenant_id`, all queries are auto-scoped
2. **Audit trail** — all entities track `created_at`, `updated_at`, `created_by`, `updated_by`
3. **Soft deletes** — critical data is never hard-deleted, use `deleted_at` timestamp
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
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_example_tenant_id ON example(tenant_id) WHERE deleted_at IS NULL;
```

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
       │     id, tenant_id, role, email, hashed_password
       │       ├─── DOCTOR_DEGREES (academic qualifications)
       │       │     degree_name, institution, completion_year, certificate_number
       │       └─── DOCTOR_TRAININGS (certifications, workshops)
       │             training_name, issuing_organization, completion_date, expiry_date
       │
       ├─── TENANT_INTEGRATIONS (SMS, Email, Payment configs)
       │     id, tenant_id, provider_id, credentials (encrypted)
       │       └─── INTEGRATION_LOGS (transaction audit trail)
       │
       ├─── PATIENTS
       │     id, tenant_id, name, age, contact, created_by
       │       ├─── PATIENT_TAGS (special_case, chronic, treatment, allergy)
       │       ├─── PATIENT_DIAGNOSES (visit-specific diagnoses)
       │       └─── VISITS
       │             id, patient_id, doctor_id, chief_complaint, notes
       │               ├─── PRESCRIPTIONS
       │               │     id, visit_id, doctor_id, status
       │               │       └─── PRESCRIPTION_ITEMS
       │               │             medicine_id (nullable), custom_medicine,
       │               │             dosage, frequency, duration
       │               │
       │               └─── PAYMENTS
       │                     id, visit_id, amount, method, status
       │                       └─── INVOICES
       │                             id, payment_id, pdf_url
       │
       ├─── MEDICINES (filtered by doctor's specializations)
       │     id, tenant_id (nullable), name, system, category,
       │     description, is_global
       │       └─── MEDICINE_SYMPTOMS (many-to-many symptom mapping)
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
| **Platform Admin**               | `admin`           | Platform-wide    | Approve doctor registrations, manage global medicines/books, platform analytics, integration management       |
| **Platform Operator**            | `operator`        | Platform-wide    | Admin's assistant — support doctor approvals, content moderation, handle support tickets                      |
| **Doctor / Practitioner**        | `doctor`          | Tenant-scoped    | Full patient & prescription management, payments, symptom search, library, AI assistant (based on specialization) |
| **Receptionist / Assistant**     | `receptionist`    | Tenant-scoped    | Doctor's assistant — patient management, appointment scheduling, payment recording, invoice generation        |
| **Patient** _(future — Phase 5)_ | `patient`         | Self-only        | View own prescriptions, visit history, educational content                                                    |

**Implementation:**

```sql
CREATE TYPE user_role AS ENUM ('admin', 'operator', 'doctor', 'receptionist', 'patient');
```

Each role has a different data access scope:

- **Admin, Operator:** No tenant_id (platform-level) — can see all tenants, used for approval workflows and global data curation
- **Doctor, Receptionist:** Queries auto-filter by `tenant_id` from JWT (clinic-specific)
- **Patient:** Queries filter by `user_id` (can only see their own data)

---

## Table Definitions

### 1. `tenants`

Represents a clinic or organization. Each tenant is fully data-isolated.

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  subdomain VARCHAR(100) UNIQUE,  -- e.g., "dr-rahman" → dr-rahman.altcare.health
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20),
  address TEXT,
  
  -- Location (Bangladesh administrative divisions)
  division_id INTEGER REFERENCES divisions(id),
  district_id INTEGER REFERENCES districts(id),
  upazila_id INTEGER REFERENCES upazilas(id),
  
  -- Subscription
  subscription_plan VARCHAR(50) NOT NULL DEFAULT 'free',  -- free, plus, pro
  plan_started_at TIMESTAMP WITH TIME ZONE,
  plan_expires_at TIMESTAMP WITH TIME ZONE,
  trial_ends_at TIMESTAMP WITH TIME ZONE,
  
  -- Limits tracking (enforced at service layer)
  patient_limit INTEGER DEFAULT 30,
  prescription_limit_monthly INTEGER,  -- NULL = unlimited
  ai_query_count_monthly INTEGER DEFAULT 0,
  ai_query_limit_monthly INTEGER,  -- NULL = unlimited
  
  -- Doctor profile
  specializations medical_system[],  -- Array: can have 1 to 4 specializations
  license_number VARCHAR(100),
  registration_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, suspended
  
  -- Integration configurations (encrypted JSON)
  sms_config JSONB,     -- {provider: 'twilio', api_key: '...', sender_id: '...'}
  email_config JSONB,   -- {provider: 'smtp', host: '...', port: 587, username: '...'}
  payment_config JSONB, -- {bkash: {merchant_number: '...'}, nagad: {...}, stripe: {...}}
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tenants_subdomain ON tenants(subdomain) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenants_registration_status ON tenants(registration_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenants_location ON tenants(division_id, district_id, upazila_id) WHERE deleted_at IS NULL;
```

---

### 2. `users`

Doctors, operators, and admins. Patients are in a separate table (future Phase 5).

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL for platform admins
  
  email VARCHAR(255) NOT NULL UNIQUE,
  hashed_password VARCHAR(255) NOT NULL,
  
  role user_role NOT NULL,
  
  -- Profile
  full_name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  avatar_url TEXT,
  
  -- Status
  is_active BOOLEAN DEFAULT TRUE,
  email_verified BOOLEAN DEFAULT FALSE,
  last_login_at TIMESTAMP WITH TIME ZONE,
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
```

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
CREATE TABLE doctor_degrees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Degree information
  degree_name VARCHAR(255) NOT NULL,  -- e.g., "BHMS", "BAMS", "MD (Homeopathy)"
  field_of_study VARCHAR(255),        -- e.g., "Homeopathic Medicine", "Ayurvedic Medicine"
  institution VARCHAR(255) NOT NULL,  -- College/University name
  location VARCHAR(255),              -- City, Country
  
  -- Timeline
  start_year INTEGER,                 -- Year started
  completion_year INTEGER NOT NULL,   -- Year completed/awarded
  
  -- Verification
  certificate_number VARCHAR(100),    -- Degree certificate/registration number
  is_verified BOOLEAN DEFAULT FALSE,  -- Admin-verified credential
  
  -- Metadata
  display_order INTEGER DEFAULT 0,    -- For sorting in profile display
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_doctor_degrees_tenant_id ON doctor_degrees(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_doctor_degrees_user_id ON doctor_degrees(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_doctor_degrees_display_order ON doctor_degrees(user_id, display_order) WHERE deleted_at IS NULL;
```

---

### 4. `doctor_trainings`

Professional training, certifications, workshops, and continuing education completed by doctors.

```sql
CREATE TABLE doctor_trainings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Training information
  training_name VARCHAR(255) NOT NULL,     -- e.g., "Advanced Constitutional Prescribing"
  training_type VARCHAR(100),              -- e.g., "Certificate", "Diploma", "Workshop", "Seminar"
  issuing_organization VARCHAR(255) NOT NULL,  -- Organization/Institute that issued
  location VARCHAR(255),                   -- City, Country (or "Online")
  
  -- Timeline
  start_date DATE,                         -- Training start date
  completion_date DATE,                    -- Training completion date
  expiry_date DATE,                        -- For certifications that expire
  duration_hours INTEGER,                  -- Total training hours (if applicable)
  
  -- Verification
  certificate_number VARCHAR(100),         -- Certificate/credential number
  is_verified BOOLEAN DEFAULT FALSE,       -- Admin-verified credential
  
  -- Additional details
  description TEXT,                        -- Brief description of training content
  skills_acquired TEXT[],                  -- Array of skills/competencies gained
  
  -- Metadata
  display_order INTEGER DEFAULT 0,         -- For sorting in profile display
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_doctor_trainings_tenant_id ON doctor_trainings(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_doctor_trainings_user_id ON doctor_trainings(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_doctor_trainings_display_order ON doctor_trainings(user_id, display_order) WHERE deleted_at IS NULL;
CREATE INDEX idx_doctor_trainings_expiry_date ON doctor_trainings(expiry_date) WHERE deleted_at IS NULL AND expiry_date IS NOT NULL;
```

---

### 5. `patients`

```sql
CREATE TABLE patients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  
  -- Demographics
  full_name VARCHAR(255) NOT NULL,
  age INTEGER,
  date_of_birth DATE,
  gender VARCHAR(20),  -- male, female, other, prefer_not_to_say
  
  -- Contact
  phone VARCHAR(20),
  email VARCHAR(255),
  address TEXT,
  
  -- Location (Bangladesh administrative divisions)
  division_id INTEGER REFERENCES divisions(id),
  district_id INTEGER REFERENCES districts(id),
  upazila_id INTEGER REFERENCES upazilas(id),
  
  -- Medical history summary (free text)
  medical_history TEXT,
  
  -- Metadata
  patient_number VARCHAR(50),  -- clinic-specific patient ID (e.g., "P-2024-001")
  blood_group VARCHAR(5),
  occupation VARCHAR(100),
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_patients_tenant_id ON patients(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_full_name ON patients USING gin(to_tsvector('english', full_name)) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_patient_number ON patients(tenant_id, patient_number) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_phone ON patients(tenant_id, phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_location ON patients(division_id, district_id, upazila_id) WHERE deleted_at IS NULL;
```

---

### 6. `patient_tags`

Flexible tagging system for special cases, chronic conditions, treatment protocols, allergies, and custom flags.

```sql
CREATE TYPE patient_tag_category AS ENUM (
  'special_case',    -- VIP, elderly, pediatric, requires_home_visit
  'chronic',         -- diabetes, hypertension, asthma
  'treatment',       -- constitutional_rx, panchakarma, rasayana
  'allergy',         -- lactose, gluten, specific_medicine
  'custom'           -- tenant-defined tags
);

CREATE TABLE patient_tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  
  category patient_tag_category NOT NULL,
  label VARCHAR(100) NOT NULL,  -- The actual tag text
  notes TEXT,                   -- Additional context
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_patient_tags_patient_id ON patient_tags(patient_id);
CREATE INDEX idx_patient_tags_category ON patient_tags(category);
```

---

### 7. `patient_diagnoses`

Visit-specific diagnoses with optional ICD code.

```sql
CREATE TABLE patient_diagnoses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  visit_id UUID REFERENCES visits(id) ON DELETE SET NULL,  -- nullable for pre-visit diagnoses
  
  diagnosis TEXT NOT NULL,
  icd_code VARCHAR(20),  -- ICD-10 code (optional)
  
  diagnosed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  diagnosed_by UUID REFERENCES users(id)
);

CREATE INDEX idx_patient_diagnoses_patient_id ON patient_diagnoses(patient_id);
CREATE INDEX idx_patient_diagnoses_visit_id ON patient_diagnoses(visit_id);
```

---

### 8. `visits`

Each patient encounter.

```sql
CREATE TABLE visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id UUID NOT NULL REFERENCES users(id),
  
  -- Visit details
  visit_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  chief_complaint TEXT NOT NULL,
  examination_notes TEXT,
  diagnosis_summary TEXT,  -- Free-text summary (detailed diagnoses in patient_diagnoses table)
  
  -- Follow-up
  follow_up_date DATE,
  follow_up_notes TEXT,
  
  -- Status
  visit_status VARCHAR(50) DEFAULT 'completed',  -- scheduled, in_progress, completed, cancelled
  
  -- Attachments
  attachments JSONB,  -- [{url, type, uploaded_at}]
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_visits_tenant_id ON visits(tenant_id);
CREATE INDEX idx_visits_patient_id ON visits(patient_id);
CREATE INDEX idx_visits_doctor_id ON visits(doctor_id);
CREATE INDEX idx_visits_visit_date ON visits(visit_date DESC);
CREATE INDEX idx_visits_follow_up_date ON visits(follow_up_date) WHERE follow_up_date IS NOT NULL;
```

---

### 9. `prescriptions`

Immutable prescription records. Once generated, cannot be edited — only voided and replaced.

```sql
CREATE TYPE prescription_status AS ENUM ('draft', 'finalized', 'voided');

CREATE TABLE prescriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  visit_id UUID NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id UUID NOT NULL REFERENCES users(id),
  
  prescription_number VARCHAR(50) UNIQUE,  -- e.g., "RX-2024-001234"
  
  -- Content
  notes TEXT,  -- Doctor's general notes/advice
  
  -- PDF generation
  pdf_url TEXT,
  pdf_generated_at TIMESTAMP WITH TIME ZONE,
  
  -- Status
  status prescription_status DEFAULT 'draft',
  
  -- Voiding (for corrections)
  voided_at TIMESTAMP WITH TIME ZONE,
  voided_by UUID REFERENCES users(id),
  void_reason TEXT,
  replacement_prescription_id UUID REFERENCES prescriptions(id),  -- Points to the corrected version
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_prescriptions_tenant_id ON prescriptions(tenant_id);
CREATE INDEX idx_prescriptions_patient_id ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_visit_id ON prescriptions(visit_id);
CREATE INDEX idx_prescriptions_status ON prescriptions(status);
CREATE INDEX idx_prescriptions_number ON prescriptions(prescription_number);
```

---

### 10. `prescription_items`

Individual medicines in a prescription. Either references `medicines` table OR contains free-text medicine name.

```sql
CREATE TABLE prescription_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prescription_id UUID NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
  
  -- Medicine reference (nullable — allows free-text entry)
  medicine_id UUID REFERENCES medicines(id),
  custom_medicine VARCHAR(255),  -- Used when medicine_id is NULL
  
  -- Dosage
  dosage VARCHAR(100) NOT NULL,       -- "2 tablets", "10 drops", "1 teaspoon"
  frequency VARCHAR(100) NOT NULL,    -- "twice daily", "after meals", "at bedtime"
  duration VARCHAR(100),              -- "7 days", "until symptoms resolve", "1 month"
  
  -- Instructions
  instructions TEXT,                  -- Additional patient instructions
  
  -- Sequence (display order)
  sequence_number INTEGER DEFAULT 0,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prescription_items_prescription_id ON prescription_items(prescription_id);
CREATE INDEX idx_prescription_items_medicine_id ON prescription_items(medicine_id) WHERE medicine_id IS NOT NULL;

-- Ensure either medicine_id OR custom_medicine is present
ALTER TABLE prescription_items ADD CONSTRAINT check_medicine_source 
  CHECK (
    (medicine_id IS NOT NULL AND custom_medicine IS NULL) OR 
    (medicine_id IS NULL AND custom_medicine IS NOT NULL)
  );
```

---

### 11. `medicines`

Global admin-curated medicines + tenant-specific additions.

```sql
CREATE TYPE medical_system AS ENUM ('homeopathy', 'ayurveda', 'unani', 'herbal');

CREATE TABLE medicines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL for global medicines
  
  name VARCHAR(255) NOT NULL,
  system medical_system NOT NULL,
  category VARCHAR(100),  -- remedy, tincture, tablet, powder, oil, etc.
  
  -- Content
  description TEXT,
  indications TEXT,       -- What it treats
  contraindications TEXT, -- When NOT to use
  dosage_guidance TEXT,   -- Standard dosing info
  
  -- Metadata
  potency VARCHAR(50),    -- For homeopathy: 30C, 200C, 1M
  botanical_name VARCHAR(255),  -- For herbal medicines
  
  -- Search optimization
  symptom_tags TEXT[],    -- Array of symptoms for matching
  search_vector tsvector, -- Full-text search index
  
  -- Global vs. tenant-specific
  is_global BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_medicines_tenant_id ON medicines(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_medicines_is_global ON medicines(is_global) WHERE deleted_at IS NULL;
CREATE INDEX idx_medicines_system ON medicines(system) WHERE deleted_at IS NULL;
CREATE INDEX idx_medicines_name ON medicines USING gin(to_tsvector('english', name)) WHERE deleted_at IS NULL;
CREATE INDEX idx_medicines_search_vector ON medicines USING gin(search_vector) WHERE deleted_at IS NULL;
CREATE INDEX idx_medicines_symptom_tags ON medicines USING gin(symptom_tags) WHERE deleted_at IS NULL;

-- Trigger to auto-update search_vector
CREATE TRIGGER medicines_search_vector_update BEFORE INSERT OR UPDATE
ON medicines FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', name, description, indications);
```

---

### 12. `medicine_symptoms`

Many-to-many symptom mapping for symptom-based search.

```sql
CREATE TABLE medicine_symptoms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  medicine_id UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
  
  symptom VARCHAR(255) NOT NULL,
  match_strength INTEGER DEFAULT 100,  -- 0-100, for ranking
  modality TEXT,  -- "worse in morning", "better with warmth", etc.
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_medicine_symptoms_medicine_id ON medicine_symptoms(medicine_id);
CREATE INDEX idx_medicine_symptoms_symptom ON medicine_symptoms USING gin(to_tsvector('english', symptom));
CREATE UNIQUE INDEX idx_medicine_symptoms_unique ON medicine_symptoms(medicine_id, symptom);
```

---

### 13. `payments`

Records all patient payments. Digital payments (bKash, Nagad, etc.) are processed via configured `tenant_integrations`.

```sql
CREATE TYPE payment_method AS ENUM ('cash', 'bkash', 'nagad', 'rocket', 'upay', 'card', 'bank_transfer');
CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'overdue', 'refunded', 'failed');

CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  visit_id UUID NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  
  amount DECIMAL(10, 2) NOT NULL,
  method payment_method NOT NULL,
  status payment_status DEFAULT 'pending',
  
  -- Integration tracking (for digital payments)
  integration_id UUID REFERENCES tenant_integrations(id),
  integration_log_id UUID REFERENCES integration_logs(id),
  
  -- Transaction details
  transaction_id VARCHAR(100),  -- Provider's transaction ID (bKash TrxID, Stripe charge_id, etc.)
  paid_at TIMESTAMP WITH TIME ZONE,
  
  -- Notes
  notes TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_payments_tenant_id ON payments(tenant_id);
CREATE INDEX idx_payments_patient_id ON payments(patient_id);
CREATE INDEX idx_payments_visit_id ON payments(visit_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_paid_at ON payments(paid_at DESC) WHERE paid_at IS NOT NULL;
CREATE INDEX idx_payments_integration_id ON payments(integration_id) WHERE integration_id IS NOT NULL;
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id) WHERE transaction_id IS NOT NULL;

-- Payment flow examples:
-- Cash payment: method='cash', integration_id=NULL, status='paid' (recorded manually)
-- bKash payment: method='bkash', integration_id=<bkash_config>, transaction_id=<TrxID>, status='paid'
-- Failed payment: status='failed', error logged in integration_logs
```

---

### 14. `invoices`

```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
  
  invoice_number VARCHAR(50) UNIQUE NOT NULL,  -- "INV-2024-001234"
  
  -- PDF
  pdf_url TEXT,
  pdf_generated_at TIMESTAMP WITH TIME ZONE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
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
  created_by UUID REFERENCES users(id),
  deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_books_tenant_id ON books(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_is_global ON books(is_global) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_system ON books(system) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_title ON books USING gin(to_tsvector('english', title)) WHERE deleted_at IS NULL;
```

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
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
  
  -- OpenAI text-embedding-3-small produces 1536-dimensional vectors
  embedding vector(1536) NOT NULL,
  
  -- Metadata for filtering during retrieval
  book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  system medical_system,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_embeddings_section_id ON embeddings(section_id);
CREATE INDEX idx_embeddings_book_id ON embeddings(book_id);

-- Vector similarity index (HNSW for fast approximate nearest neighbor search)
CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (embedding vector_cosine_ops);
```

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

### 22. `ai_queries`

Log of all AI assistant queries for usage tracking and analytics.

```sql
CREATE TABLE ai_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  query TEXT NOT NULL,
  response TEXT,
  
  -- Retrieval metadata
  retrieved_sections JSONB,  -- Array of {section_id, book_title, chapter, similarity_score}
  
  -- Performance
  retrieval_time_ms INTEGER,
  llm_time_ms INTEGER,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_queries_tenant_id ON ai_queries(tenant_id);
CREATE INDEX idx_ai_queries_user_id ON ai_queries(user_id);
CREATE INDEX idx_ai_queries_created_at ON ai_queries(created_at DESC);
```

---

### 23. `notifications`

Email and SMS notification queue. Notifications are dispatched via tenant's configured integrations.

```sql
CREATE TYPE notification_type AS ENUM ('email', 'sms');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');

CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  
  type notification_type NOT NULL,
  recipient VARCHAR(255) NOT NULL,  -- Email or phone number
  
  subject VARCHAR(500),  -- For emails
  body TEXT NOT NULL,
  
  -- Integration tracking
  integration_id UUID REFERENCES tenant_integrations(id),  -- Which integration was used
  integration_log_id UUID REFERENCES integration_logs(id), -- Link to the actual transaction
  
  -- Status
  status notification_status DEFAULT 'pending',
  sent_at TIMESTAMP WITH TIME ZONE,
  failed_reason TEXT,
  retry_count INTEGER DEFAULT 0,
  
  -- Context (for templating and tracking)
  context JSONB,  -- {patient_id, visit_id, prescription_id, payment_id}
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_status ON notifications(status) WHERE status = 'pending';
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX idx_notifications_integration_id ON notifications(integration_id) WHERE integration_id IS NOT NULL;
```

---

## Platform-Level Tables

These tables have no `tenant_id` — they are shared across all tenants.

---

### 24. `divisions`

Bangladesh administrative divisions (বিভাগ). There are 8 divisions in Bangladesh.

```sql
CREATE TABLE divisions (
  id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY (START WITH 10),
  
  name VARCHAR(100) NOT NULL,        -- English name (e.g., "Dhaka", "Chittagong")
  bn_name VARCHAR(100) NOT NULL,     -- Bengali name (e.g., "ঢাকা", "চট্টগ্রাম")
  url VARCHAR(100),                  -- URL slug for division page
  
  -- Geospatial data (PostGIS)
  geom GEOMETRY(MultiPolygon, 4326)  -- Division boundary polygon
);

CREATE INDEX idx_divisions_name ON divisions(name);
CREATE INDEX idx_divisions_geom ON divisions USING GIST(geom);
```

**Sample data:** Dhaka (ঢাকা), Chittagong (চট্টগ্রাম), Rajshahi (রাজশাহী), Khulna (খুলনা), Barisal (বরিশাল), Sylhet (সিলেট), Rangpur (রংপুর), Mymensingh (ময়মনসিংহ)

---

### 25. `districts`

Bangladesh districts (জেলা). There are 64 districts under the 8 divisions.

```sql
CREATE TABLE districts (
  id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY (START WITH 66),
  division_id INTEGER NOT NULL REFERENCES divisions(id) ON UPDATE CASCADE,
  
  name VARCHAR(100) NOT NULL,        -- English name
  bn_name VARCHAR(100) NOT NULL,     -- Bengali name
  lat NUMERIC(12, 9),                -- Latitude of district center
  lon NUMERIC(12, 9),                -- Longitude of district center
  url VARCHAR(100),                  -- URL slug
  
  -- Geospatial data (PostGIS)
  geom GEOMETRY(MultiPolygon, 4326)  -- District boundary polygon
);

CREATE INDEX idx_districts_division_id ON districts(division_id);
CREATE INDEX idx_districts_name ON districts(name);
CREATE INDEX idx_districts_geom ON districts USING GIST(geom);
```

**Example:** Dhaka district (ঢাকা জেলা) under Dhaka division, Chittagong district (চট্টগ্রাম জেলা) under Chittagong division.

---

### 26. `upazilas`

Bangladesh sub-districts (উপজেলা). There are 490+ upazilas under the 64 districts.

```sql
CREATE TABLE upazilas (
  id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY (START WITH 493),
  district_id INTEGER NOT NULL REFERENCES districts(id) ON UPDATE CASCADE,
  
  name VARCHAR(100) NOT NULL,        -- English name
  bn_name VARCHAR(100) NOT NULL,     -- Bengali name
  lat NUMERIC(12, 9),                -- Latitude of upazila center
  lon NUMERIC(12, 9),                -- Longitude of upazila center
  url VARCHAR(100),                  -- URL slug
  
  -- Geospatial data (PostGIS)
  geom GEOMETRY(MultiPolygon, 4326)  -- Upazila boundary polygon
);

CREATE INDEX idx_upazilas_district_id ON upazilas(district_id);
CREATE INDEX idx_upazilas_name ON upazilas(name);
CREATE INDEX idx_upazilas_geom ON upazilas USING GIST(geom);
```

**Example:** Dhanmondi (ধানমন্ডি), Mohammadpur (মোহাম্মদপুর), Gulshan (গুলশান) under Dhaka district.

**Note:** These tables use INTEGER primary keys (not UUID) to match Bangladesh's official geographic coding system. The IDENTITY start values align with existing government data standards.

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
  logo_url TEXT,
  documentation_url TEXT,
  supported_countries VARCHAR(50)[],  -- ['BD', 'IN', 'US']
  
  status integration_provider_status DEFAULT 'active',
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integration_providers_type ON integration_providers(type);
CREATE UNIQUE INDEX idx_integration_providers_name ON integration_providers(type, provider_name);

-- Seed data example (Bangladesh-focused + international options)
INSERT INTO integration_providers (type, provider_name, display_name, config_schema, supported_countries) VALUES
-- SMS Providers
('sms', 'twilio', 'Twilio SMS', '{"required": ["account_sid", "auth_token", "phone_number"]}', ARRAY['US', 'BD']),
('sms', 'banglalink', 'Banglalink Bulk SMS', '{"required": ["api_key", "sender_id"]}', ARRAY['BD']),
('sms', 'robi', 'Robi SMS API', '{"required": ["username", "password", "mask"]}', ARRAY['BD']),
('sms', 'grameenphone', 'Grameenphone SMS', '{"required": ["api_key", "sender_id"]}', ARRAY['BD']),

-- Email Providers
('email', 'smtp', 'SMTP Server', '{"required": ["host", "port", "username", "password"]}', ARRAY['*']),
('email', 'sendgrid', 'SendGrid', '{"required": ["api_key"]}', ARRAY['*']),
('email', 'aws_ses', 'AWS SES', '{"required": ["access_key", "secret_key", "region"]}', ARRAY['*']),

-- Payment Providers (Bangladesh)
('payment', 'bkash', 'bKash', '{"required": ["merchant_number", "app_key", "app_secret", "username", "password"]}', ARRAY['BD']),
('payment', 'nagad', 'Nagad', '{"required": ["merchant_id", "merchant_number", "public_key", "private_key"]}', ARRAY['BD']),
('payment', 'rocket', 'Rocket', '{"required": ["merchant_number", "api_key"]}', ARRAY['BD']),
('payment', 'upay', 'Upay', '{"required": ["merchant_id", "api_key"]}', ARRAY['BD']),

-- Payment Providers (International)
('payment', 'stripe', 'Stripe', '{"required": ["secret_key", "publishable_key", "webhook_secret"]}', ARRAY['*']),
('payment', 'razorpay', 'Razorpay', '{"required": ["key_id", "key_secret"]}', ARRAY['IN', 'BD']);
```

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
2. **Foreign keys:** All FK columns are indexed
3. **Full-text search:** `medicines.name`, `patients.full_name`, `sections.content` use GIN indexes
4. **Vector search:** `embeddings.embedding` uses HNSW index for fast cosine similarity
5. **Time-series queries:** `visits.visit_date`, `payments.paid_at`, `ai_queries.created_at` indexed DESC
6. **Status filters:** `prescriptions.status`, `payments.status`, `notifications.status`

### Additional performance optimizations

```sql
-- Composite index for common patient lookup pattern
CREATE INDEX idx_patients_tenant_name ON patients(tenant_id, full_name) WHERE deleted_at IS NULL;

-- Composite index for dashboard queries (recent visits)
CREATE INDEX idx_visits_tenant_date ON visits(tenant_id, visit_date DESC) WHERE visit_status = 'completed';

-- Partial index for pending follow-ups
CREATE INDEX idx_visits_pending_followup ON visits(tenant_id, follow_up_date) 
  WHERE follow_up_date >= CURRENT_DATE AND visit_status = 'completed';

-- Index for monthly revenue reports
CREATE INDEX idx_payments_tenant_paid_month ON payments(tenant_id, DATE_TRUNC('month', paid_at)) 
  WHERE status = 'paid';
```

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

## Doctor Specialization & Resource Filtering

### How specializations work

When a doctor registers, they select 1-4 specializations from the `medical_system` enum:

```sql
-- Example: Doctor specializing in Homeopathy only
UPDATE tenants SET specializations = ARRAY['homeopathy'] WHERE id = $1;

-- Example: Doctor practicing multiple systems
UPDATE tenants SET specializations = ARRAY['homeopathy', 'ayurveda', 'herbal'] WHERE id = $1;
```

### Resource filtering based on specialization

All resources (medicines, books, symptom searches) are automatically filtered by the doctor's active specializations:

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

```sql
-- 1. Celery worker runs daily at 8 AM to find tomorrow's appointments
SELECT v.id, p.phone, v.visit_date 
FROM visits v 
JOIN patients p ON p.id = v.patient_id
WHERE v.tenant_id = $1
  AND v.visit_date::date = CURRENT_DATE + 1
  AND v.visit_status = 'scheduled';

-- 2. For each appointment, create notification
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
  v.diagnosis_summary,
  p.prescription_number,
  p.pdf_url,
  json_agg(json_build_object(
    'medicine', COALESCE(m.name, pi.custom_medicine),
    'dosage', pi.dosage,
    'frequency', pi.frequency,
    'duration', pi.duration
  )) as medicines
FROM visits v
LEFT JOIN prescriptions p ON p.visit_id = v.id AND p.status = 'finalized'
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
✅ **Multi-specialization support** — doctors can practice 1-4 systems, resources auto-filter based on active specializations  
✅ **Integrated SMS/Email/Payment** — pluggable provider framework with 10+ pre-configured providers (bKash, Nagad, Rocket, Twilio, etc.)  
✅ **Complete transaction audit** — every SMS, email, and payment logged with request/response payloads  
✅ **Scale to thousands of clinics** on a single PostgreSQL instance  
✅ **Enable rich clinical workflows** with flexible tagging and visit tracking  
✅ **Power AI/RAG** with vector embeddings stored natively in PostgreSQL (pgvector)  
✅ **Maintain audit trails** with automatic timestamp and user tracking on all entities  
✅ **Enforce data integrity** with foreign keys, constraints, and check conditions  
✅ **Optimize query performance** with targeted indexes, partial indexes, and GIN/HNSW indexes  

The schema balances **flexibility** (JSONB for extensible metadata, nullable foreign keys for optional data) with **strictness** (immutable prescriptions, strong FK constraints, enum types for controlled vocabularies).

**Total tables:** 24 (core clinic + knowledge base + integrations + usage tracking)

**Integration providers:** SMS (Twilio, Banglalink, Robi, GP), Email (SMTP, SendGrid, AWS SES), Payment (bKash, Nagad, Rocket, Upay, Stripe, Razorpay)

It is designed to evolve incrementally — Phase 1 launches with core clinic tables, Phase 2 adds medicines, Phase 3 adds books, Phase 4 adds embeddings and integrations — without requiring destructive schema migrations.

---

## Quick Reference

### Key Design Patterns

| Pattern | Implementation | Example |
|---------|---------------|---------|
| Multi-tenancy | `tenant_id` on every table + JWT-based filtering | All queries auto-filter: `WHERE tenant_id = $current_tenant` |
| Platform vs Tenant users | `tenant_id IS NULL` for platform users | Admin/Operator: no tenant, Doctor/Receptionist: has tenant |
| Specialization filtering | Array membership check | `WHERE system = ANY(doctor.specializations)` |
| Global vs Tenant data | `is_global` flag + nullable `tenant_id` | Medicines: global pool + tenant additions |
| Immutable records | No UPDATE, only INSERT | Prescriptions/Payments: void and replace, never edit |
| Soft deletes | `deleted_at` timestamp | Filters: `WHERE deleted_at IS NULL` |
| Integration abstraction | Provider catalog + tenant config + logs | One framework for SMS, Email, Payment |
| Audit trail | `created_at`, `updated_at`, `created_by`, `updated_by` | Automatic via SQLAlchemy event listeners |

### Common Operations Quick Reference

```sql
-- Get doctor's active specializations
SELECT specializations FROM tenants WHERE id = $tenant_id;

-- Get medicines available to a doctor (global + tenant-specific + filtered by specialization)
SELECT * FROM medicines 
WHERE (tenant_id = $1 OR is_global = true)
  AND system = ANY(SELECT unnest(specializations) FROM tenants WHERE id = $1)
  AND deleted_at IS NULL;

-- Get tenant's active payment integration
SELECT ti.*, ip.display_name 
FROM tenant_integrations ti
JOIN integration_providers ip ON ip.id = ti.provider_id
WHERE ti.tenant_id = $1 
  AND ip.type = 'payment' 
  AND ti.is_enabled = true 
  AND ti.is_verified = true;

-- Create prescription with mixed medicines (DB + custom)
INSERT INTO prescription_items (prescription_id, medicine_id, custom_medicine, dosage, frequency)
VALUES 
  ($1, 'uuid-of-existing-medicine', NULL, '2 tablets', 'twice daily'),
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
  AND v.visit_status = 'completed'
ORDER BY v.follow_up_date;
```

### Environment Setup Checklist

- [ ] PostgreSQL 16 installed with extensions: `pgvector`, `uuid-ossp`, `pg_trgm`
- [ ] Run migrations: `alembic upgrade head`
- [ ] Seed integration providers: `INSERT INTO integration_providers ...` (see table 22)
- [ ] Create platform admin user: `role='admin', tenant_id=NULL`
- [ ] Set up encryption key: `INTEGRATION_ENCRYPTION_KEY` in `.env`
- [ ] Configure backup schedule: daily `pg_dump` to S3
- [ ] Enable connection pooling: PgBouncer or SQLAlchemy pool_size=20
