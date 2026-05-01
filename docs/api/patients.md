---
title: "Patient Management API"
type: "api-reference"
module: "patients"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "14 endpoints for patient CRUD, search, tags, and diagnoses"
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
  - [Get Patient](#get-patient)
  - [Create Patient](#create-patient)
  - [Update Patient](#update-patient)
  - [Delete Patient](#delete-patient)
  - [Search Patients](#search-patients)
  - [Patient Tags](#patient-tags)
  - [Patient Diagnoses](#patient-diagnoses)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## 🌐 Overview

Patient management endpoints for CRUD operations, search, tags, and medical history.

**Key Features:**
- ✅ Full CRUD operations
- ✅ Search by name/phone/code
- ✅ Filter by gender/tags
- ✅ Tag management
- ✅ Diagnosis history
- ✅ Multi-tenant isolation

**Authentication:** Required (JWT)

---

## 📡 Endpoints

### List Patients

```http
GET /api/v1/patients
```

**Query Parameters:**
- `skip` (int, optional): Offset for pagination (default: 0)
- `limit` (int, optional): Max results (default: 100)
- `search` (string, optional): Search by name/phone/code
- `gender` (string, optional): Filter by gender (male|female|other)
- `tag_id` (uuid, optional): Filter by tag ID

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "tenant_id": "uuid",
    "patient_code": "P-2026-0001",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "phone": "01712345678",
    "email": "john@example.com",
    "address": "123 Main St",
    "division_id": "uuid",
    "district_id": "uuid",
    "upazila_id": "uuid",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "01798765432",
    "blood_group": "A+",
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-01T10:00:00Z"
  }
]
```

---

### Get Patient

```http
GET /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (uuid, required): Patient ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "patient_code": "P-2026-0001",
  "first_name": "John",
  "last_name": "Doe",
  ...
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
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "phone": "01712345678",
  "email": "john@example.com",
  "address": "123 Main St",
  "division_id": "uuid",
  "district_id": "uuid",
  "upazila_id": "uuid",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "01798765432",
  "blood_group": "A+"
}
```

**Required Fields:**
- `first_name` (string)
- `last_name` (string)
- `date_of_birth` (date)
- `gender` (enum: male|female|other)
- `phone` (string, min 11 chars)

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "patient_code": "P-2026-0001",
  ...
}
```

**Errors:**
- `400 Bad Request`: Validation error
- `409 Conflict`: Phone number already exists

---

### Update Patient

```http
PUT /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (uuid, required): Patient ID

**Request Body:** (partial update supported)
```json
{
  "phone": "01712345679",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Patient doesn't exist
- `400 Bad Request`: Validation error

---

### Delete Patient

```http
DELETE /api/v1/patients/{id}
```

**Path Parameters:**
- `id` (uuid, required): Patient ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Patient doesn't exist

<!-- AI: This is a soft delete, sets deleted_at timestamp -->

---

### Search Patients

```http
GET /api/v1/patients/search?q={query}
```

**Query Parameters:**
- `q` (string, required): Search query (name, phone, or patient code)

**Response:** `200 OK` (same as List Patients)

**Search Fields:**
- First name
- Last name
- Phone number
- Patient code

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
    "id": "uuid",
    "patient_id": "uuid",
    "tag": "diabetes",
    "created_at": "2026-05-01T10:00:00Z"
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
  "tag": "diabetes"
}
```

**Response:** `201 Created`

#### Delete Tag

```http
DELETE /api/v1/patients/{patient_id}/tags/{tag_id}
```

**Response:** `204 No Content`

---

### Patient Diagnoses

#### List Diagnoses

```http
GET /api/v1/patients/{patient_id}/diagnoses
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "diagnosis": "Hypertension",
    "diagnosed_at": "2026-05-01",
    "notes": "Stage 1, monitoring",
    "created_at": "2026-05-01T10:00:00Z"
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
  "diagnosis": "Hypertension",
  "diagnosed_at": "2026-05-01",
  "notes": "Stage 1"
}
```

**Response:** `201 Created`

#### Update Diagnosis

```http
PUT /api/v1/patients/{patient_id}/diagnoses/{diagnosis_id}
```

**Response:** `200 OK`

#### Delete Diagnosis

```http
DELETE /api/v1/patients/{patient_id}/diagnoses/{diagnosis_id}
```

**Response:** `204 No Content`

---

## 💡 Examples

### Create a Patient (cURL)

```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "phone": "01712345678"
  }'
```

### Search Patients (Python)

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/patients/search",
    headers={"Authorization": f"Bearer {token}"},
    params={"q": "john"}
)
patients = response.json()
```

### Filter by Gender (JavaScript)

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/patients?gender=male',
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

### Validation Error (400)

```json
{
  "detail": [
    {
      "loc": ["body", "phone"],
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

### Conflict (409)

```json
{
  "detail": "Patient with this phone number already exists"
}
```

---

## 🤖 AI Quick Reference

**Q: What fields are required to create a patient?**
→ first_name, last_name, date_of_birth, gender, phone

**Q: How do I search for a patient?**
→ GET /patients/search?q=name_or_phone

**Q: Can I filter by gender?**
→ Yes, GET /patients?gender=male

**Q: How do I add tags to a patient?**
→ POST /patients/{id}/tags with {"tag": "tag_name"}

**Q: Are patients tenant-scoped?**
→ Yes, automatically filtered by tenant_id from JWT

---

**See Also:**
- [Appointments API](appointments.md) - Schedule patient visits
- [Prescriptions API](prescriptions.md) - Issue prescriptions
- [Authentication](authentication.md) - Get JWT token

---

**Last Updated:** May 1, 2026  
**Endpoints:** 14 ✅
