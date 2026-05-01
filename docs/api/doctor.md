---
title: "Doctor Profile & Credentials API"
type: "api-reference"
module: "doctor"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "12 endpoints for doctor profile, academic degrees, and professional training management"
endpoints: 12
authentication: "required"
---

# Doctor Profile & Credentials API

**Module:** Doctor  
**Endpoints:** 12  
**Base Path:** `/api/v1/doctor`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [Profile Management](#profile-management)
  - [Academic Degrees](#academic-degrees)
  - [Professional Training](#professional-training)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## 🌐 Overview

Complete doctor profile management with academic credentials and professional development tracking.

**Key Features:**
- ✅ Combined User + Tenant profile
- ✅ Clinic details management
- ✅ Academic degrees (BHMS, BAMS, MD, etc.)
- ✅ Professional training & certifications
- ✅ Certificate upload support
- ✅ Verification workflow
- ✅ Display order management
- ✅ Multi-tenant isolation

**Authentication:** Required (JWT, doctor role)

---

## 📡 Endpoints

### Profile Management

#### Get Doctor Profile

```http
GET /api/v1/doctor/profile
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "doctor@clinic.com",
  "full_name": "Dr. John Doe",
  "phone": "+8801712345678",
  "avatar_url": "https://example.com/avatar.jpg",
  "language": "en",
  "is_active": true,
  "tenant_id": "uuid",
  "clinic_name": "Sunshine Homeopathy Clinic",
  "clinic_address": "123 Main St, Dhaka",
  "division_id": 1,
  "district_id": 2,
  "upazila_id": 3,
  "specializations": ["homeopathy", "ayurveda"],
  "license_number": "BHMS-2020-12345",
  "is_verified": true,
  "verified_at": "2026-01-15T10:00:00Z",
  "plan": "pro",
  "plan_started_at": "2026-01-01T00:00:00Z",
  "plan_expires_at": "2027-01-01T00:00:00Z"
}
```

**Description:** Combines User and Tenant data into single profile view

<!-- AI: This is a virtual model combining two tables -->

---

#### Update Doctor Profile

```http
PATCH /api/v1/doctor/profile
```

**Request Body:** (all fields optional)
```json
{
  "full_name": "Dr. John Updated Doe",
  "phone": "+8801798765432",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "language": "bn",
  "clinic_name": "Updated Clinic Name",
  "clinic_address": "456 New Address",
  "division_id": 2,
  "district_id": 4,
  "upazila_id": 10,
  "license_number": "BHMS-2020-67890"
}
```

**Response:** `200 OK` (updated profile)

**Note:** Only send fields you want to update

---

### Academic Degrees

#### Create Degree

```http
POST /api/v1/doctor/degrees
```

**Request Body:**
```json
{
  "degree_type": "Bachelor",
  "degree_name": "BHMS",
  "specialization": "General Practice",
  "institution_name": "National Medical College",
  "institution_location": "Dhaka, Bangladesh",
  "start_year": 2015,
  "completion_year": 2020,
  "certificate_url": "https://example.com/certificate.pdf",
  "display_order": 1
}
```

**Required Fields:**
- `degree_type` (enum): Bachelor, Master, Diploma, Fellowship
- `degree_name` (string): BHMS, BAMS, BUMS, MD, MS, etc.
- `institution_name` (string)
- `completion_year` (int, 1900-2100)

**Optional Fields:**
- `specialization` (string): Pediatrics, Dermatology, etc.
- `institution_location` (string)
- `start_year` (int)
- `certificate_url` (string): URL to uploaded certificate
- `display_order` (int, default: 0): Sort order

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": "uuid",
  "tenant_id": "uuid",
  "degree_type": "Bachelor",
  "degree_name": "BHMS",
  "specialization": "General Practice",
  "institution_name": "National Medical College",
  "institution_location": "Dhaka, Bangladesh",
  "start_year": 2015,
  "completion_year": 2020,
  "certificate_url": "https://example.com/certificate.pdf",
  "display_order": 1,
  "is_verified": false,
  "verified_at": null,
  "verified_by": null,
  "created_at": "2026-04-28T10:00:00Z",
  "updated_at": null
}
```

**Errors:**
- `400 Bad Request`: Validation error

<!-- AI: user_id and tenant_id automatically set from JWT -->

---

#### List Degrees

```http
GET /api/v1/doctor/degrees
```

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "degree_name": "MD (Homeopathy)",
    "degree_type": "Master",
    "completion_year": 2022,
    "display_order": 0,
    "is_verified": true,
    ...
  },
  {
    "id": 1,
    "degree_name": "BHMS",
    "degree_type": "Bachelor",
    "completion_year": 2020,
    "display_order": 1,
    ...
  }
]
```

**Sort Order:** By `display_order` ascending, then `completion_year` descending (newest first)

---

#### Get Degree

```http
GET /api/v1/doctor/degrees/{degree_id}
```

**Path Parameters:**
- `degree_id` (int, required): Degree ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "degree_name": "BHMS",
  "institution_name": "National Medical College",
  ...
}
```

**Errors:**
- `404 Not Found`: Degree doesn't exist

---

#### Update Degree

```http
PATCH /api/v1/doctor/degrees/{degree_id}
```

**Path Parameters:**
- `degree_id` (int, required): Degree ID

**Request Body:** (partial update supported)
```json
{
  "specialization": "Pediatrics",
  "certificate_url": "https://example.com/new-cert.pdf",
  "display_order": 2
}
```

**Response:** `200 OK` (updated degree)

**Errors:**
- `404 Not Found`: Degree doesn't exist

---

#### Delete Degree

```http
DELETE /api/v1/doctor/degrees/{degree_id}
```

**Path Parameters:**
- `degree_id` (int, required): Degree ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Degree doesn't exist

---

### Professional Training

#### Create Training

```http
POST /api/v1/doctor/trainings
```

**Request Body:**
```json
{
  "training_type": "Certification",
  "title": "Advanced Homeopathic Prescribing",
  "provider": "National Institute of Homeopathy",
  "description": "Advanced techniques for acute and chronic cases",
  "skills": "Acute prescribing, Chronic management, Repertorization",
  "start_date": "2023-01-15",
  "completion_date": "2023-06-15",
  "expiry_date": "2025-06-15",
  "certificate_url": "https://example.com/training-cert.pdf",
  "credential_id": "CERT-2023-12345",
  "display_order": 1
}
```

**Required Fields:**
- `training_type` (enum): Certification, Workshop, Conference, Continuing Education
- `title` (string): Training title
- `provider` (string): Organization name
- `completion_date` (date): Completion date

**Optional Fields:**
- `description` (text)
- `skills` (text): Comma-separated skills
- `start_date` (date)
- `expiry_date` (date): For renewable certifications
- `certificate_url` (string)
- `credential_id` (string): Unique ID from provider
- `display_order` (int, default: 0)

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": "uuid",
  "tenant_id": "uuid",
  "training_type": "Certification",
  "title": "Advanced Homeopathic Prescribing",
  "provider": "National Institute of Homeopathy",
  "description": "Advanced techniques...",
  "skills": "Acute prescribing, Chronic management...",
  "start_date": "2023-01-15",
  "completion_date": "2023-06-15",
  "expiry_date": "2025-06-15",
  "certificate_url": "https://example.com/training-cert.pdf",
  "credential_id": "CERT-2023-12345",
  "display_order": 1,
  "is_verified": false,
  "verified_at": null,
  "verified_by": null,
  "created_at": "2026-04-28T10:00:00Z",
  "updated_at": null
}
```

**Errors:**
- `400 Bad Request`: Validation error

---

#### List Trainings

```http
GET /api/v1/doctor/trainings
```

**Query Parameters:**
- `active_only` (bool, optional): Filter out expired trainings (default: false)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Advanced Homeopathic Prescribing",
    "training_type": "Certification",
    "completion_date": "2023-06-15",
    "expiry_date": "2025-06-15",
    "is_verified": true,
    ...
  }
]
```

**Sort Order:** By `display_order` ascending, then `completion_date` descending (newest first)

**Active Filter:** When `active_only=true`, excludes trainings where `expiry_date < today`

---

#### Get Training

```http
GET /api/v1/doctor/trainings/{training_id}
```

**Path Parameters:**
- `training_id` (int, required): Training ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Advanced Homeopathic Prescribing",
  "provider": "National Institute of Homeopathy",
  ...
}
```

**Errors:**
- `404 Not Found`: Training doesn't exist

---

#### Update Training

```http
PATCH /api/v1/doctor/trainings/{training_id}
```

**Path Parameters:**
- `training_id` (int, required): Training ID

**Request Body:** (partial update supported)
```json
{
  "title": "Updated Title",
  "skills": "Updated skills list",
  "expiry_date": "2026-06-15"
}
```

**Response:** `200 OK` (updated training)

**Errors:**
- `404 Not Found`: Training doesn't exist

---

#### Delete Training

```http
DELETE /api/v1/doctor/trainings/{training_id}
```

**Path Parameters:**
- `training_id` (int, required): Training ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Training doesn't exist

---

## 💡 Examples

### Get Profile (cURL)

```bash
curl -X GET http://localhost:8000/api/v1/doctor/profile \
  -H "Authorization: Bearer $TOKEN"
```

### Update Profile (Python)

```python
import requests

response = requests.patch(
    "http://localhost:8000/api/v1/doctor/profile",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "clinic_name": "New Clinic Name",
        "phone": "+8801712345678",
        "language": "bn"
    }
)
profile = response.json()
```

### Add Degree (JavaScript)

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/doctor/degrees',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      degree_type: 'Bachelor',
      degree_name: 'BHMS',
      institution_name: 'National Medical College',
      completion_year: 2020,
      display_order: 1
    })
  }
)
const degree = await response.json()
```

### List Active Trainings (Python)

```python
response = requests.get(
    "http://localhost:8000/api/v1/doctor/trainings",
    headers={"Authorization": f"Bearer {token}"},
    params={"active_only": True}
)
trainings = response.json()

for training in trainings:
    print(f"{training['title']} - {training['provider']}")
    if training['expiry_date']:
        print(f"  Expires: {training['expiry_date']}")
```

### Add Certification (Python)

```python
response = requests.post(
    "http://localhost:8000/api/v1/doctor/trainings",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "training_type": "Certification",
        "title": "Advanced Prescribing",
        "provider": "National Institute of Homeopathy",
        "completion_date": "2023-06-15",
        "expiry_date": "2025-06-15",
        "skills": "Acute prescribing, Repertorization"
    }
)
training = response.json()
```

---

## ❌ Error Handling

### Unauthorized (401)

```json
{
  "detail": "Could not validate credentials"
}
```

### Not Found (404)

```json
{
  "detail": "Degree not found"
}
```

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "degree_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔒 Verification Workflow

**Admin Verification:**
- Degrees and trainings have `is_verified` flag
- Platform admins can verify credentials
- Sets `verified_at` timestamp and `verified_by` admin ID
- Verified credentials displayed with badge/checkmark in UI

**Future Enhancement:** Email notification when credentials verified

---

## 🤖 AI Quick Reference

**Q: How do I get doctor profile?**
→ GET /doctor/profile (combines User + Tenant data)

**Q: What degree types are supported?**
→ Bachelor, Master, Diploma, Fellowship

**Q: What training types are supported?**
→ Certification, Workshop, Conference, Continuing Education

**Q: How do I filter expired trainings?**
→ GET /doctor/trainings?active_only=true

**Q: How do I control display order?**
→ Set display_order field (lower numbers appear first)

**Q: Can I upload certificates?**
→ Yes, set certificate_url to uploaded file URL

**Q: Who can verify credentials?**
→ Platform admins (feature ready, admin UI pending)

**Q: Are degrees tenant-scoped?**
→ Yes, automatically scoped by tenant_id from JWT

---

**See Also:**
- [Authentication API](authentication.md) - Get JWT token
- [Patients API](patients.md) - Patient management
- [Prescriptions API](prescriptions.md) - Display doctor credentials on prescriptions

---

**Last Updated:** May 1, 2026  
**Endpoints:** 12 ✅  
**Test Coverage:** 36 tests (18 unit + 18 integration), 97% service, 100% routes
