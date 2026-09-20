---
title: "Patient Management API"
type: "api-reference"
module: "patients"
version: "0.9.0"
last_updated: "2026-09-21"
ai_summary: "14 endpoints for patient CRUD, tags, and diagnoses"
endpoints: 14
authentication: "required"
---

# Patient Management API

**Module:** Patients  
**Endpoints:** 14  
**Base Path:** `/api/v1/patients`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [List Patients](#list-patients)
  - [Patient Count](#patient-count)
  - [Get Patient](#get-patient)
  - [Create Patient](#create-patient)
  - [Update Patient](#update-patient)
  - [Delete Patient](#delete-patient)
  - [Patient Tags](#patient-tags)
  - [Patient Diagnoses](#patient-diagnoses)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## 🌐 Overview

Patient management endpoints for CRUD operations, search, tags, and medical history.

**Key Features:**
- ✅ Full CRUD operations
- ✅ Search by name/phone/email (via `search` query param on list)
- ✅ Filter by active status and upcoming visits
- ✅ Tag management (special_case, chronic, treatment, allergy)
- ✅ Diagnosis history
- ✅ Multi-tenant isolation

**Authentication:** Required (JWT, tenant user — platform users get `403`)

---

## 📡 Endpoints

### List Patients

```http
GET /api/v1/patients
```

**Query Parameters:**
- `search` (string, optional): Search by full name, phone, or email
- `is_active` (bool, optional): Filter by active status
- `has_upcoming_visit` (bool, optional): Filter patients with/without an upcoming `next_visit_date`
- `limit` (int, optional): Max results (default: 100, max: 500)
- `offset` (int, optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "full_name": "John Doe",
    "phone": "01712345678",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "next_visit_date": "2026-06-01",
    "is_active": true
  }
]
```

<!-- AI: There is no separate /patients/search endpoint — search is a query param on this list endpoint -->

---

### Patient Count

```http
GET /api/v1/patients/count
```

**Response:** `200 OK`
```json
{
  "count": 150
}
```

**Description:** Count of active patients for the tenant.

---

### Get Patient

```http
GET /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (string, required): Patient ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "blood_group": "A+",
  "phone": "01712345678",
  "email": "john@example.com",
  "whatsapp": "01712345678",
  "address": "123 Main St",
  "division_id": 1,
  "district_id": 2,
  "upazila_id": 3,
  "chief_complaint": "Recurring headache",
  "medical_history": "None reported",
  "photo_url": null,
  "next_visit_date": null,
  "is_active": true,
  "created_at": "2026-05-01T10:00:00Z",
  "updated_at": "2026-05-01T10:00:00Z",
  "created_by": "uuid",
  "updated_by": "uuid"
}
```

**Errors:**
- `404 Not Found`: Patient doesn't exist

---

### Create Patient

```http
POST /api/v1/patients
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "blood_group": "A+",
  "phone": "01712345678",
  "email": "john@example.com",
  "whatsapp": "01712345678",
  "address": "123 Main St",
  "division_id": 1,
  "district_id": 2,
  "upazila_id": 3,
  "chief_complaint": "Recurring headache",
  "medical_history": "None reported",
  "next_visit_date": "2026-06-01"
}
```

**Required Fields:**
- `full_name` (string)

**Optional Fields:**
- `date_of_birth` (date)
- `gender` (enum: male|female|other)
- `blood_group` (enum: A+|A-|B+|B-|AB+|AB-|O+|O-)
- `phone`, `email`, `whatsapp` (string)
- `address` (string), `division_id`/`district_id`/`upazila_id` (int, Bangladesh geographic IDs)
- `chief_complaint`, `medical_history` (string)
- `photo_url` (string)
- `next_visit_date` (date)

**Response:** `201 Created` (same shape as [Get Patient](#get-patient))

**Errors:**
- `422 Unprocessable Entity`: Validation error

<!-- AI: There is no patient_code, first_name, or last_name field — patients use a single full_name field and are identified by their id -->

---

### Update Patient

```http
PATCH /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (string, required): Patient ID

**Request Body:** (partial update supported — any field from [Create Patient](#create-patient), plus `is_active`)
```json
{
  "phone": "01712345679",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Patient doesn't exist
- `422 Unprocessable Entity`: Validation error

---

### Delete Patient

```http
DELETE /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (string, required): Patient ID

**Response:** `200 OK` (updated patient record with `is_active: false`)

**Errors:**
- `404 Not Found`: Patient doesn't exist

<!-- AI: This is a soft delete — sets is_active=false and returns the updated patient, it does NOT return 204 -->

---

### Patient Tags

#### List Tags

```http
GET /api/v1/patients/{patient_id}/tags
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": "uuid",
    "tenant_id": "uuid",
    "tag_type": "chronic",
    "tag_value": "diabetes",
    "notes": null,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": null
  }
]
```

#### Add Tag

```http
POST /api/v1/patients/{patient_id}/tags
```

**Request Body:**
```json
{
  "tag_type": "chronic",
  "tag_value": "diabetes",
  "notes": "Type 2, diet-controlled"
}
```

**Required Fields:**
- `tag_type` (enum: special_case|chronic|treatment|allergy)
- `tag_value` (string)

**Response:** `201 Created`

#### Update Tag

```http
PATCH /api/v1/patients/tags/{tag_id}
```

**Note:** Path does **not** include `patient_id` — tags are addressed by `tag_id` alone.

**Request Body:** (partial update — `tag_type`, `tag_value`, `notes`)

**Response:** `200 OK`

#### Delete Tag

```http
DELETE /api/v1/patients/tags/{tag_id}
```

**Note:** Path does **not** include `patient_id` — tags are addressed by `tag_id` alone.

**Response:** `204 No Content`

---

### Patient Diagnoses

#### List Diagnoses

```http
GET /api/v1/patients/{patient_id}/diagnoses
```

**Query Parameters:**
- `active_only` (bool, optional, default: `true`): Only show active diagnoses

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": "uuid",
    "visit_id": null,
    "tenant_id": "uuid",
    "description": "Hypertension",
    "icd_code": null,
    "diagnosed_at": "2026-05-01",
    "is_active": true,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": null
  }
]
```

#### Add Diagnosis

```http
POST /api/v1/patients/{patient_id}/diagnoses
```

**Request Body:**
```json
{
  "description": "Hypertension",
  "icd_code": "I10",
  "diagnosed_at": "2026-05-01",
  "visit_id": "uuid"
}
```

**Required Fields:**
- `description` (string)
- `diagnosed_at` (date)

**Optional Fields:**
- `icd_code` (string)
- `visit_id` (string): Link to a visit

**Response:** `201 Created`

#### Update Diagnosis

```http
PATCH /api/v1/patients/diagnoses/{diagnosis_id}
```

**Note:** Path does **not** include `patient_id` — diagnoses are addressed by `diagnosis_id` alone.

**Request Body:** (partial update — `description`, `icd_code`, `diagnosed_at`, `is_active`)

**Response:** `200 OK`

#### Delete Diagnosis

```http
DELETE /api/v1/patients/diagnoses/{diagnosis_id}
```

**Note:** Path does **not** include `patient_id` — diagnoses are addressed by `diagnosis_id` alone.

**Response:** `200 OK` (updated diagnosis record with `is_active: false`)

<!-- AI: This is a soft delete — sets is_active=false and returns the updated diagnosis, it does NOT return 204 -->

---

## 💡 Examples

### Create a Patient (cURL)

```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "phone": "01712345678"
  }'
```

### Search Patients (Python)

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/patients",
    headers={"Authorization": f"Bearer {token}"},
    params={"search": "john"}
)
patients = response.json()
```

### Filter Active Patients (JavaScript)

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/patients?is_active=true',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
)
const patients = await response.json()
```

---

## ❌ Error Handling

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "full_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Not Found (404)

```json
{
  "detail": "Patient not found"
}
```

### Forbidden (403)

```json
{
  "detail": "Platform users cannot manage patient records. Use a tenant account."
}
```

---

## 🤖 AI Quick Reference

**Q: What fields are required to create a patient?**
→ Only `full_name`

**Q: How do I search for a patient?**
→ GET /patients?search=name_or_phone_or_email (there is no separate /patients/search route)

**Q: Can I filter by upcoming visits?**
→ Yes, GET /patients?has_upcoming_visit=true

**Q: How do I add tags to a patient?**
→ POST /patients/{id}/tags with {"tag_type": "chronic", "tag_value": "diabetes"}

**Q: Are patients tenant-scoped?**
→ Yes — the service filters by `tenant_id` from the JWT explicitly (not an automatic global filter; see `docs/architecture/multi-tenancy.md`)

---

**See Also:**
- [Appointments API](appointments.md) - Schedule patient visits
- [Prescriptions API](prescriptions.md) - Issue prescriptions
- [Authentication](authentication.md) - Get JWT token

---

**Last Updated:** September 21, 2026  
**Endpoints:** 14 ✅
