---
title: "Database Schema"
type: "architecture"
version: "1.0.0"
last_updated: "2026-07-12"
ai_summary: "34 PostgreSQL tables with multi-tenant isolation, pgvector for AI, and complete audit trail"
---

# Database Schema

Complete database schema for AltCare with 34 tables organized by domain.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Core Tables](#core-tables)
- [Doctor Tables](#doctor-tables)
- [Patient Tables](#patient-tables)
- [Clinical Tables](#clinical-tables)
- [Geographic Tables](#geographic-tables)
- [Medicine & Library](#medicine--library)
- [Integration Tables](#integration-tables)
- [System Tables](#system-tables)

---

## 🌐 Overview

**Database:** PostgreSQL 16
**Total Tables:** 34
**Extensions:** pgvector, pg_trgm

**Design Principles:**
- Multi-tenant isolation (`tenant_id` on all tenant-scoped tables)
- Audit trail (`created_at`, `updated_at`, `created_by`, `updated_by`)
- Soft deletes — no shared `deleted_at` column; each table uses either an `is_active` boolean (patients, medicines, symptoms, books) or a `status` field (prescriptions, payments, invoices, appointments)
- Immutable records (prescriptions, payments)
- Primary keys are app-generated `VARCHAR(36)` UUID strings (Python `uuid4()`) on core entity tables, or plain `SERIAL` integers on catalog/lookup tables — not database-generated via `uuid-ossp`

---

## 🔑 Core Tables (3)

### `tenants`
**Purpose:** Clinic/Organization records

```sql
-- Reflects app/shared/models/tenant.py:Tenant
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),

    -- Clinic details
    clinic_name VARCHAR(255),
    clinic_address TEXT,
    division_id INTEGER,
    district_id INTEGER,
    upazila_id INTEGER,

    -- Specializations (array)
    specializations VARCHAR(50)[] NOT NULL DEFAULT '{}',

    -- License / verification / approval
    license_number VARCHAR(100),
    is_verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMP,
    is_approved BOOLEAN NOT NULL DEFAULT false,   -- admin approval gate for onboarding
    approved_at TIMESTAMP,
    approved_by VARCHAR(36),
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Subscription
    plan VARCHAR(20) NOT NULL DEFAULT 'free',
    plan_started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    plan_expires_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

**Specializations:** `homeopathy`, `ayurveda`, `unani`, `herbal` (1-4 per tenant)
**Plans:** `free`, `plus`, `pro` — there is no `basic` or `enterprise` plan in the model's comments, and no `subdomain` or per-plan `max_patients`/`max_monthly_patients` column; usage limits are tracked separately in `usage_tracking`. Integration credentials (SMS/email/payment) live in `tenant_integrations`, not on `tenants`.

---

### `users`
**Purpose:** All system users (platform + tenant)

```sql
-- Reflects app/shared/models/tenant.py:User
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL for platform users

    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),

    role VARCHAR(50) NOT NULL,  -- admin, operator, doctor, receptionist
    language VARCHAR(5) NOT NULL DEFAULT 'en',  -- en, bn

    is_active BOOLEAN NOT NULL DEFAULT true,
    is_email_verified BOOLEAN NOT NULL DEFAULT false,
    email_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,

    -- 2FA
    is_2fa_enabled BOOLEAN NOT NULL DEFAULT false,
    totp_secret VARCHAR(32),

    -- JWT invalidation (incremented on password/email/role change)
    token_version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

**Roles:** `admin`, `operator`, `doctor`, `receptionist` — only `admin` and `doctor` have enforced RBAC today; `operator` has a guard (`RequireAdminOrOperator`) but no endpoint uses it, and `receptionist` has no distinct enforcement from `doctor`. See `roles-access.md`.

---

### `user_sessions`
**Purpose:** Track active JWT sessions

```sql
-- Reflects app/shared/models/tenant.py:UserSession
CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    refresh_token_hash VARCHAR(255) NOT NULL,  -- not a jti claim
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),

    ip_address VARCHAR(45),
    user_agent TEXT,

    is_revoked BOOLEAN NOT NULL DEFAULT false,
    revoked_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

There is no `tenant_id` column on `user_sessions` in the current model.

---

## 👨‍⚕️ Doctor Tables (2)

### `doctor_degrees`
**Purpose:** Academic qualifications

```sql
CREATE TABLE doctor_degrees (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    tenant_id UUID REFERENCES tenants(id),

    degree_type VARCHAR(100) NOT NULL,  -- Bachelor, Master, Diploma, Fellowship
    degree_name VARCHAR(255) NOT NULL,  -- BHMS, BAMS, MD, etc.
    specialization VARCHAR(255),

    institution_name VARCHAR(500) NOT NULL,
    institution_location VARCHAR(255),

    start_year INTEGER,
    completion_year INTEGER NOT NULL,

    certificate_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,

    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    verified_by UUID REFERENCES users(id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

---

### `doctor_trainings`
**Purpose:** Certifications, workshops, continuing education

```sql
CREATE TABLE doctor_trainings (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    tenant_id UUID REFERENCES tenants(id),

    training_type VARCHAR(100) NOT NULL,  -- Certification, Workshop, Conference, CE
    title VARCHAR(500) NOT NULL,
    provider VARCHAR(500) NOT NULL,

    description TEXT,
    skills TEXT,  -- Comma-separated

    start_date DATE,
    completion_date DATE NOT NULL,
    expiry_date DATE,

    certificate_url VARCHAR(500),
    credential_id VARCHAR(255),
    display_order INTEGER DEFAULT 0,

    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    verified_by UUID REFERENCES users(id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

---

## 🏥 Patient Tables (3)

### `patients`
**Purpose:** Patient demographics

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),

    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),  -- male, female, other
    blood_group VARCHAR(10),

    phone VARCHAR(20),
    email VARCHAR(255),
    whatsapp VARCHAR(20),
    address TEXT,

    division_id INTEGER REFERENCES divisions(id),
    district_id INTEGER REFERENCES districts(id),
    upazila_id INTEGER REFERENCES upazilas(id),

    chief_complaint TEXT,
    medical_history TEXT,
    photo_url VARCHAR(500),
    next_visit_date DATE,

    is_active BOOLEAN NOT NULL DEFAULT true,  -- soft-delete flag; there is no deleted_at column

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

There is no `patient_code`/patient-number column in the current model (`app/shared/models/patient.py`) — the `P-2026-0001` format described below is aspirational, not implemented.

---

### `patient_tags`
**Purpose:** Categorize patients

```sql
CREATE TABLE patient_tags (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    patient_id VARCHAR(36) NOT NULL REFERENCES patients(id),

    tag_type VARCHAR(50) NOT NULL,    -- special_case, chronic, treatment, allergy
    tag_value VARCHAR(255) NOT NULL,  -- e.g., diabetes, hypertension
    notes TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

---

### `patient_diagnoses`
**Purpose:** Diagnosis history

```sql
CREATE TABLE patient_diagnoses (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    patient_id VARCHAR(36) NOT NULL REFERENCES patients(id),
    visit_id VARCHAR(36),  -- optional link to a visit

    description TEXT NOT NULL,
    icd_code VARCHAR(20),
    diagnosed_at DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(36)
);
```

---

## 🩺 Clinical Tables (6)

### `appointments`, `visits`, `prescriptions`, `prescription_items`, `payments`, `invoices`

**See API documentation for details:**
- [Appointments API](../api/appointments.md)
- [Prescriptions API](../api/prescriptions.md)
- [Payments API](../api/payments.md)

**Key Fields:**
- All have `tenant_id`, `created_at`, `updated_at`, audit fields
- Appointments: time slot, duration, status
- Visits: chief complaint, vitals, diagnosis, treatment plan
- Prescriptions: status (draft/issued/voided), immutable when issued
- Prescription Items: medicine_id OR medicine_name (free-text)
- Payments: method (cash/bkash), status (pending/paid/failed)
- Invoices: auto-number (INV-YYYYMM-NNNN), PDF URL

---

## 🌍 Geographic Tables (3)

### Bangladesh Administrative Hierarchy

```sql
-- Reflects app/shared/models/geographic.py — no `code` column; optional lat/long instead
CREATE TABLE divisions (
    id SERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT
);

CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    division_id INTEGER NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT
);

CREATE TABLE upazilas (
    id SERIAL PRIMARY KEY,
    district_id INTEGER NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT
);
```

**Seed Data:**
- 8 divisions
- 64 districts
- 490+ upazilas

---

## 💊 Medicine & Library (12)

### `medicines`
**Purpose:** Medicine database with bilingual content

```sql
CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) REFERENCES tenants(id),  -- NULL if global

    name_en VARCHAR(500) NOT NULL,
    name_bn VARCHAR(500),

    system VARCHAR(50) NOT NULL,  -- homeopathy, ayurveda, unani, herbal
    category VARCHAR(255),
    potency VARCHAR(50),

    description_en TEXT,
    description_bn TEXT,
    dosage_guidance_en TEXT,
    dosage_guidance_bn TEXT,
    indications_en TEXT,
    indications_bn TEXT,
    contraindications_en TEXT,
    contraindications_bn TEXT,

    is_global BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);

ALTER TABLE medicines ADD CONSTRAINT ck_medicines_tenant_global
    CHECK ( (is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL) );
```

Search uses `pg_trgm` GIN indexes on `name_en`/`name_bn` (no `search_vector`/tsvector column).

`tenant_id` was `NOT NULL` until migration `ba209a25bf7d` (2026-09-24) — the CHECK constraint above is what now makes a global-row-with-a-tenant or tenant-row-with-no-tenant unrepresentable. Same history and same constraint shape on `symptoms` below.

---

### `medicine_aliases`
**Purpose:** Alternate spellings, transliterations, and brand names for search (`medicine_id`, `alias_en`/`alias_bn`, `alias_type`, `priority`). `tenant_id` nullable, no CHECK of its own — mirrors whatever creator/medicine it's attached to.

### `symptoms`
**Purpose:** Normalized master list of symptoms shared across all medical systems (`name_en`/`name_bn`, `description_en`/`bn`, `category`, `is_global`). Same `ck_symptoms_tenant_global` CHECK constraint as `medicines`.

### `symptom_aliases`
**Purpose:** Alternate spellings/transliterations for a symptom (`symptom_id`, `alias_en`/`alias_bn`, `alias_type`, `priority`). `tenant_id` nullable, no CHECK of its own, same reasoning as `medicine_aliases`.

### `medicine_symptom_mappings`
**Purpose:** Many-to-many mapping between `medicines` and the normalized `symptoms` table (`medicine_id`, `symptom_id`, `modality_en`/`bn`, `strength`). Not named `medicine_symptoms` — see `app/shared/models/symptom.py:MedicineSymptomMapping`. `tenant_id` nullable, no CHECK of its own.

---

### Library Tables (7)
- `books`: EPUB books (global or tenant-specific)
- `chapters`: Book chapters
- `sections`: Chapter sections
- `embeddings`: pgvector embeddings (1536 dimensions) for RAG
- `reading_progress`: User reading progress
- `bookmarks`: User bookmarks
- `highlights`: User highlights

---

## 🔌 Integration Tables (3)

### `integration_providers`
**Purpose:** Global catalog of SMS/Email/Payment providers

```sql
-- Reflects app/shared/models/integration.py:IntegrationProvider (platform-level, no tenant_id)
CREATE TABLE integration_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,       -- e.g., "twilio", "sendgrid"
    display_name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,      -- sms, email, payment
    description TEXT,
    logo_url VARCHAR(500),

    config_schema JSONB,
    supported_countries JSONB,

    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Examples:** Twilio (SMS), SendGrid (Email), bKash (Payment)

---

### `tenant_integrations`
**Purpose:** Tenant-specific integration configs

```sql
-- Reflects app/shared/models/integration.py:TenantIntegration
CREATE TABLE tenant_integrations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    provider_id INTEGER NOT NULL REFERENCES integration_providers(id),

    display_name VARCHAR(255),
    encrypted_credentials TEXT NOT NULL,  -- Fernet-encrypted JSON, not raw JSONB
    is_primary BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,

    last_tested_at TIMESTAMP,
    test_status VARCHAR(20),  -- success, failed

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

---

### `integration_logs`
**Purpose:** Audit trail for all integration API calls

```sql
-- Reflects app/shared/models/integration.py:IntegrationLog
CREATE TABLE integration_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    tenant_integration_id INTEGER NOT NULL REFERENCES tenant_integrations(id),

    transaction_type VARCHAR(50) NOT NULL,  -- sms_sent, email_sent, payment_initiated, ...
    request_payload JSONB,
    response_payload JSONB,
    response_status_code INTEGER,

    status VARCHAR(20) NOT NULL,  -- pending, success, failed
    error_message TEXT,
    external_reference VARCHAR(255),
    recipient VARCHAR(255),
    amount INTEGER,
    currency VARCHAR(3),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);
```

---

## ⚙️ System Tables (2)

### `translations`
**Purpose:** UI translations (English/Bengali)

```sql
CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    text_en TEXT NOT NULL,
    text_bn TEXT NOT NULL,
    category VARCHAR(100)
);
```

---

### `usage_tracking`
**Purpose:** Track tenant usage against plan limits. Written by `UsageService`
(`app/core/usage_tracking.py`) on prescription issue, SMS send, and AI query (Stage 1 "Billing
enforcement"); `total_patients`/`total_prescriptions`/`total_ai_queries_this_month` remain
unmaintained display columns — reads go through `UsageService.get_month_to_date()`, which sums the
daily counters directly rather than trusting them.

```sql
-- Reflects app/shared/models/usage.py:UsageTracking — one row per tenant per day,
-- with fixed counter columns rather than a generic metric_name/metric_value pair
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),

    usage_date DATE NOT NULL,

    patients_added INTEGER NOT NULL DEFAULT 0,
    prescriptions_created INTEGER NOT NULL DEFAULT 0,
    ai_queries_made INTEGER NOT NULL DEFAULT 0,
    pdfs_generated INTEGER NOT NULL DEFAULT 0,
    sms_sent INTEGER NOT NULL DEFAULT 0,

    total_patients INTEGER NOT NULL DEFAULT 0,
    total_prescriptions INTEGER NOT NULL DEFAULT 0,
    total_ai_queries_this_month INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,

    UNIQUE (tenant_id, usage_date)
);
```

---

## 🔍 Indexes

**Key indexes automatically created:**
- Key foreign keys (`index=True` columns in the SQLAlchemy models)
- `tenant_id` on tenant-scoped tables
- Unique constraints (`users.email`, `tenants.email`)
- Fuzzy-search filters via `pg_trgm` GIN indexes: `medicines`/`medicine_aliases`/`symptoms`/`symptom_aliases` name/alias columns

**Performance indexes:**
```sql
CREATE INDEX idx_patients_tenant_id ON patients(tenant_id);
CREATE INDEX idx_appointments_date ON appointments(tenant_id, appointment_date);
CREATE INDEX idx_prescriptions_status ON prescriptions(tenant_id, status);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 🤖 AI Quick Reference

**Q: How many tables?**
→ 34 tables

**Q: What's the multi-tenant key?**
→ `tenant_id` (a `VARCHAR(36)` UUID string, not a native Postgres `UUID` column) on all tenant-scoped tables

**Q: Which tables don't have tenant_id?**
→ Platform data: `integration_providers`, `divisions`, `districts`, `upazilas`, `translations`, `user_sessions`

**Q: How are soft deletes implemented?**
→ There is no shared `deleted_at` column. Each table uses either an `is_active` boolean (patients, medicines, symptoms, books) or a `status` field (prescriptions, payments, invoices, appointments) instead.

**Q: What's the patient code format?**
→ Not implemented — there is no patient-code/patient-number column on `patients` today.

**Q: How are prescriptions made immutable?**
→ Status field: draft (editable) → issued (immutable) → voided

---

**See Also:**
- [Multi-Tenancy](multi-tenancy.md) - Tenant isolation details
- [Authentication](authentication.md) - User and session tables
- [Roles & Access](roles-access.md) - Authoritative RBAC reference

---

**Last Updated:** 2026-07-12
**Tables:** 34 ✅
