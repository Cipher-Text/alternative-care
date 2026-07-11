---
title: "Database Schema"
type: "architecture"
version: "0.9.0"
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
**Extensions:** pgvector, uuid-ossp, pg_trgm

**Design Principles:**
- Multi-tenant isolation (`tenant_id` on all tenant-scoped tables)
- Audit trail (`created_at`, `updated_at`, `created_by`, `updated_by`)
- Soft deletes (`deleted_at` for clinical data)
- Immutable records (prescriptions, payments)

---

## 🔑 Core Tables (3)

### `tenants`
**Purpose:** Clinic/Organization records

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE,

    -- Clinic details
    clinic_address TEXT,
    division_id INTEGER REFERENCES divisions(id),
    district_id INTEGER REFERENCES districts(id),
    upazila_id INTEGER REFERENCES upazila(id),

    -- Specializations (array)
    specializations TEXT[] DEFAULT ARRAY['homeopathy'],

    -- License
    license_number VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,

    -- Subscription
    plan VARCHAR(50) DEFAULT 'free',
    plan_started_at TIMESTAMP,
    plan_expires_at TIMESTAMP,

    -- Limits
    max_patients INTEGER DEFAULT 50,
    max_monthly_patients INTEGER DEFAULT 100,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

**Specializations Enum:** `homeopathy`, `ayurveda`, `unani`, `herbal`
**Plans:** `free`, `basic`, `pro`, `enterprise`

---

### `users`
**Purpose:** All system users (platform + tenant)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),  -- NULL for platform users

    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),

    role VARCHAR(50) NOT NULL,  -- admin, operator, doctor, receptionist
    language VARCHAR(10) DEFAULT 'en',  -- en, bn

    is_active BOOLEAN DEFAULT true,
    is_email_verified BOOLEAN DEFAULT false,

    -- 2FA
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

**Roles:** `admin`, `operator`, `doctor`, `receptionist`

---

### `user_sessions`
**Purpose:** Track active JWT sessions

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id),

    refresh_token_jti VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,

    ip_address VARCHAR(45),
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

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

    patient_code VARCHAR(100) UNIQUE NOT NULL,  -- P-2026-0001

    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL,  -- male, female, other

    phone VARCHAR(20) NOT NULL,
    email VARCHAR(320),
    address TEXT,

    division_id INTEGER REFERENCES divisions(id),
    district_id INTEGER REFERENCES districts(id),
    upazila_id INTEGER REFERENCES upazilas(id),

    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),

    blood_group VARCHAR(10),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP
);
```

---

### `patient_tags`
**Purpose:** Categorize patients

```sql
CREATE TABLE patient_tags (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    tenant_id UUID REFERENCES tenants(id),

    tag VARCHAR(100) NOT NULL,  -- diabetes, hypertension, etc.

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### `patient_diagnoses`
**Purpose:** Diagnosis history

```sql
CREATE TABLE patient_diagnoses (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    tenant_id UUID REFERENCES tenants(id),

    diagnosis VARCHAR(500) NOT NULL,
    diagnosed_at DATE NOT NULL,
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
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
CREATE TABLE divisions (
    id SERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE
);

CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES divisions(id),
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE
);

CREATE TABLE upazilas (
    id SERIAL PRIMARY KEY,
    district_id INTEGER REFERENCES districts(id),
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE
);
```

**Seed Data:**
- 8 divisions
- 64 districts
- 490+ upazilas

---

## 💊 Medicine & Library (9)

### `medicines`
**Purpose:** Medicine database with bilingual content

```sql
CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),  -- NULL if global

    name_en VARCHAR(255) NOT NULL,
    name_bn VARCHAR(255),

    system VARCHAR(50) NOT NULL,  -- homeopathy, ayurveda, unani, herbal
    category VARCHAR(100),
    potency VARCHAR(50),

    description_en TEXT,
    description_bn TEXT,

    is_global BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### `medicine_symptoms`
**Purpose:** Many-to-many medicine-symptom mapping

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
CREATE TABLE integration_providers (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,  -- sms, email, payment
    provider_name VARCHAR(100) NOT NULL,

    config_schema JSONB NOT NULL,
    supported_countries TEXT[],

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Examples:** Twilio (SMS), SendGrid (Email), bKash (Payment)

---

### `tenant_integrations`
**Purpose:** Tenant-specific integration configs

```sql
CREATE TABLE tenant_integrations (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    provider_id INTEGER REFERENCES integration_providers(id),

    credentials JSONB NOT NULL,  -- Encrypted with Fernet
    config JSONB,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

---

### `integration_logs`
**Purpose:** Audit trail for all integration API calls

```sql
CREATE TABLE integration_logs (
    id UUID PRIMARY KEY,
    tenant_integration_id UUID REFERENCES tenant_integrations(id),
    tenant_id UUID REFERENCES tenants(id),

    request_payload JSONB,
    response_payload JSONB,

    status_code INTEGER,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
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
**Purpose:** Track tenant usage against plan limits

```sql
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),

    metric_name VARCHAR(100) NOT NULL,  -- patients_count, monthly_patients
    metric_value INTEGER NOT NULL,

    period_month INTEGER,
    period_year INTEGER,

    recorded_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔍 Indexes

**Key indexes automatically created:**
- All foreign keys
- `tenant_id` on tenant-scoped tables
- Unique constraints (email, patient_code, etc.)
- Soft delete filter: `WHERE deleted_at IS NULL`

**Performance indexes:**
```sql
CREATE INDEX idx_patients_tenant_id ON patients(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_appointments_date ON appointments(tenant_id, appointment_date);
CREATE INDEX idx_prescriptions_status ON prescriptions(tenant_id, status);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 🤖 AI Quick Reference

**Q: How many tables?**
→ 34 tables

**Q: What's the multi-tenant key?**
→ tenant_id (UUID) on all tenant-scoped tables

**Q: Which tables don't have tenant_id?**
→ Platform data: integration_providers, divisions, districts, upazilas, translations

**Q: How are soft deletes implemented?**
→ deleted_at TIMESTAMP column, query with WHERE deleted_at IS NULL

**Q: What's the patient code format?**
→ P-YYYY-NNNN (e.g., P-2026-0001)

**Q: How are prescriptions made immutable?**
→ Status field: draft (editable) → issued (immutable) → voided

---

**See Also:**
- [Multi-Tenancy](multi-tenancy.md) - Tenant isolation details
- [Authentication](authentication.md) - User and session tables
- [API Reference](../api/README.md) - How to query these tables

---

**Last Updated:** May 1, 2026
**Tables:** 30 ✅
