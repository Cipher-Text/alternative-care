# Patient Management Module

Complete patient management system with CRUD operations, tags, diagnoses, search, and filtering capabilities.

## Features

### Core Patient Management
- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Soft delete (preserves patient data)
- ✅ Multi-tenant isolation
- ✅ Comprehensive patient demographics
- ✅ Medical history tracking
- ✅ Contact information management

### Patient Tagging System
- ✅ Categorize patients with tags
- ✅ Tag types: chronic, allergy, special_case, treatment
- ✅ Add notes to tags
- ✅ Multiple tags per patient

### Diagnosis Tracking
- ✅ Record patient diagnoses
- ✅ ICD code support
- ✅ Link diagnoses to visits (optional)
- ✅ Track active/inactive diagnoses
- ✅ Diagnosis history

### Search & Filtering
- ✅ Full-text search by name, phone, or email
- ✅ Filter by active status
- ✅ Filter by upcoming visit
- ✅ Pagination support

## API Endpoints

Base URL: `/api/v1/patients`

### Patient Endpoints

#### Create Patient
```http
POST /api/v1/patients
Content-Type: application/json
Authorization: Bearer {token}

{
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "blood_group": "O+",
  "phone": "+8801712345678",
  "email": "john@example.com",
  "whatsapp": "+8801712345678",
  "address": "123 Main St, Dhaka",
  "division_id": 1,
  "district_id": 2,
  "upazila_id": 3,
  "chief_complaint": "Chronic headache",
  "medical_history": "No significant history",
  "photo_url": "https://example.com/photo.jpg",
  "next_visit_date": "2026-05-01"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "tenant_id": "tenant-uuid",
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "blood_group": "O+",
  "phone": "+8801712345678",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2026-04-28T10:00:00Z",
  "updated_at": null,
  "created_by": "user-uuid",
  "updated_by": "user-uuid"
}
```

#### List Patients
```http
GET /api/v1/patients?search=john&is_active=true&limit=10&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `search` (optional): Search by name, phone, or email (case-insensitive)
- `is_active` (optional): Filter by active status (true/false)
- `has_upcoming_visit` (optional): Filter patients with upcoming visits (true/false)
- `limit` (optional): Maximum results (default: 100, max: 500)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "full_name": "John Doe",
    "phone": "+8801712345678",
    "date_of_birth": "1990-05-15",
    "gender": "male",
    "next_visit_date": "2026-05-01",
    "is_active": true
  }
]
```

#### Get Patient Count
```http
GET /api/v1/patients/count
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "count": 150
}
```

#### Get Patient by ID
```http
GET /api/v1/patients/{patient_id}
Authorization: Bearer {token}
```

**Response:** `200 OK` (full patient details)

#### Update Patient
```http
PATCH /api/v1/patients/{patient_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "full_name": "John Updated Doe",
  "phone": "+8801798765432"
}
```

**Note:** All fields are optional - only send fields you want to update.

**Response:** `200 OK` (updated patient details)

#### Delete Patient (Soft Delete)
```http
DELETE /api/v1/patients/{patient_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "is_active": false,
  ...
}
```

### Patient Tag Endpoints

#### Create Patient Tag
```http
POST /api/v1/patients/{patient_id}/tags
Content-Type: application/json
Authorization: Bearer {token}

{
  "tag_type": "chronic",
  "tag_value": "Diabetes",
  "notes": "Type 2, managed with diet"
}
```

**Tag Types:**
- `chronic` - Chronic conditions
- `allergy` - Allergies
- `special_case` - Special cases requiring attention
- `treatment` - Treatment tags

**Response:** `201 Created`

#### List Patient Tags
```http
GET /api/v1/patients/{patient_id}/tags
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": "uuid",
    "tenant_id": "tenant-uuid",
    "tag_type": "chronic",
    "tag_value": "Diabetes",
    "notes": "Type 2, managed with diet",
    "created_at": "2026-04-28T10:00:00Z",
    "updated_at": null
  }
]
```

#### Update Patient Tag
```http
PATCH /api/v1/patients/tags/{tag_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "tag_value": "Updated Value",
  "notes": "Updated notes"
}
```

**Response:** `200 OK`

#### Delete Patient Tag
```http
DELETE /api/v1/patients/tags/{tag_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

### Patient Diagnosis Endpoints

#### Create Patient Diagnosis
```http
POST /api/v1/patients/{patient_id}/diagnoses
Content-Type: application/json
Authorization: Bearer {token}

{
  "description": "Chronic bronchitis",
  "icd_code": "J42",
  "diagnosed_at": "2026-04-15",
  "visit_id": "visit-uuid"  // optional
}
```

**Response:** `201 Created`

#### List Patient Diagnoses
```http
GET /api/v1/patients/{patient_id}/diagnoses?active_only=true
Authorization: Bearer {token}
```

**Query Parameters:**
- `active_only` (optional): Show only active diagnoses (default: true)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": "uuid",
    "visit_id": "visit-uuid",
    "tenant_id": "tenant-uuid",
    "description": "Chronic bronchitis",
    "icd_code": "J42",
    "diagnosed_at": "2026-04-15",
    "is_active": true,
    "created_at": "2026-04-28T10:00:00Z",
    "updated_at": null
  }
]
```

#### Update Patient Diagnosis
```http
PATCH /api/v1/patients/diagnoses/{diagnosis_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "description": "Updated description",
  "icd_code": "A00",
  "is_active": false
}
```

**Response:** `200 OK`

#### Delete Patient Diagnosis (Soft Delete)
```http
DELETE /api/v1/patients/diagnoses/{diagnosis_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "is_active": false,
  ...
}
```

## Data Models

### Patient
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Auto | Primary key |
| tenant_id | UUID | Auto | Tenant isolation |
| full_name | String | Yes | Patient full name |
| date_of_birth | Date | No | Date of birth |
| gender | Enum | No | male, female, other |
| blood_group | Enum | No | A+, A-, B+, B-, AB+, AB-, O+, O- |
| phone | String(20) | No | Phone number |
| email | Email | No | Email address |
| whatsapp | String(20) | No | WhatsApp number |
| address | Text | No | Full address |
| division_id | Int | No | Bangladesh division |
| district_id | Int | No | Bangladesh district |
| upazila_id | Int | No | Bangladesh upazila |
| chief_complaint | Text | No | Primary complaint |
| medical_history | Text | No | Medical history |
| photo_url | String(500) | No | Patient photo URL |
| next_visit_date | Date | No | Next scheduled visit |
| is_active | Boolean | Auto | Active status (soft delete) |
| created_at | Timestamp | Auto | Creation timestamp |
| updated_at | Timestamp | Auto | Update timestamp |
| created_by | UUID | Auto | Creator user ID |
| updated_by | UUID | Auto | Last updater user ID |

### PatientTag
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Int | Auto | Primary key |
| patient_id | UUID | Yes | Patient reference |
| tenant_id | UUID | Auto | Tenant isolation |
| tag_type | Enum | Yes | chronic, allergy, special_case, treatment |
| tag_value | String(255) | Yes | Tag value |
| notes | Text | No | Additional notes |
| created_at | Timestamp | Auto | Creation timestamp |
| updated_at | Timestamp | Auto | Update timestamp |

### PatientDiagnosis
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Int | Auto | Primary key |
| patient_id | UUID | Yes | Patient reference |
| visit_id | UUID | No | Visit reference (optional) |
| tenant_id | UUID | Auto | Tenant isolation |
| description | Text | Yes | Diagnosis description |
| icd_code | String(20) | No | ICD-10 code |
| diagnosed_at | Date | Yes | Diagnosis date |
| is_active | Boolean | Auto | Active status (soft delete) |
| created_at | Timestamp | Auto | Creation timestamp |
| updated_at | Timestamp | Auto | Update timestamp |
| created_by | UUID | Auto | Creator user ID |
| updated_by | UUID | Auto | Last updater user ID |

## Authentication

All endpoints require JWT authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer {access_token}
```

The token must include:
- `sub`: User ID
- `tenant_id`: Tenant ID (for automatic tenant isolation)
- `role`: User role (must be 'doctor', 'receptionist', or 'admin')

## Multi-Tenant Isolation

All patient data is automatically scoped by `tenant_id` from the JWT token. Users can only access patients belonging to their tenant. Cross-tenant access is blocked at the service layer.

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Patient not found"
}
```

### 422 Validation Error
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

## Usage Examples

### Python (httpx)
```python
import httpx

async with httpx.AsyncClient() as client:
    # Create patient
    response = await client.post(
        "http://localhost:8000/api/v1/patients",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "John Doe",
            "phone": "+8801712345678",
            "email": "john@example.com"
        }
    )
    patient = response.json()
    
    # Search patients
    response = await client.get(
        "http://localhost:8000/api/v1/patients",
        headers={"Authorization": f"Bearer {token}"},
        params={"search": "john", "limit": 10}
    )
    patients = response.json()
    
    # Add tag
    response = await client.post(
        f"http://localhost:8000/api/v1/patients/{patient['id']}/tags",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tag_type": "allergy",
            "tag_value": "Penicillin"
        }
    )
```

### JavaScript (fetch)
```javascript
// Create patient
const response = await fetch('http://localhost:8000/api/v1/patients', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    full_name: 'John Doe',
    phone: '+8801712345678',
    email: 'john@example.com'
  })
});
const patient = await response.json();

// Search patients
const searchResponse = await fetch(
  'http://localhost:8000/api/v1/patients?search=john&limit=10',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
const patients = await searchResponse.json();
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_patient_service.py -v
```

**Coverage:** 27 tests, 98% code coverage

### Integration Tests
```bash
pytest tests/integration/test_patient_routes.py -v
```

**Coverage:** 24 tests, 98% route coverage

### All Patient Tests
```bash
pytest tests/unit/test_patient_service.py tests/integration/test_patient_routes.py -v
```

**Total:** 51 tests passing

## Service Layer

The patient service layer (`service.py`) provides business logic methods:

```python
from app.modules.patient.service import PatientService

# Initialize with DB session and tenant ID
service = PatientService(db=db_session, tenant_id=tenant_id)

# CRUD operations
patient = await service.create_patient(data, created_by=user_id)
patient = await service.get_patient(patient_id)
patients = await service.list_patients(search="john", limit=10)
updated = await service.update_patient(patient_id, data, updated_by=user_id)
deleted = await service.delete_patient(patient_id, updated_by=user_id)
count = await service.get_patient_count()

# Tags
tag = await service.create_patient_tag(data, created_by=user_id)
tags = await service.list_patient_tags(patient_id)
updated_tag = await service.update_patient_tag(tag_id, data, updated_by=user_id)
await service.delete_patient_tag(tag_id)

# Diagnoses
diagnosis = await service.create_patient_diagnosis(data, created_by=user_id)
diagnoses = await service.list_patient_diagnoses(patient_id, active_only=True)
updated_diag = await service.update_patient_diagnosis(diagnosis_id, data, updated_by=user_id)
deleted_diag = await service.delete_patient_diagnosis(diagnosis_id, updated_by=user_id)
```

## Architecture

```
app/modules/patient/
├── __init__.py          # Module exports
├── routes.py            # FastAPI route handlers (15 endpoints)
├── service.py           # Business logic layer
└── README.md            # This file

app/shared/
├── models/patient.py    # SQLAlchemy models
└── schemas/patient.py   # Pydantic schemas (14 schemas)

tests/
├── unit/test_patient_service.py         # Service layer tests (27 tests)
└── integration/test_patient_routes.py   # API endpoint tests (24 tests)
```

## Development Status

✅ **Complete and Production-Ready**
- All core features implemented
- 51 tests passing (27 unit + 24 integration)
- 98% code coverage
- Multi-tenant isolation verified
- Full API documentation
- Comprehensive error handling

## Next Steps

Recommended enhancements:
1. Add bulk patient import (CSV/Excel)
2. Add patient merge functionality (duplicate handling)
3. Add patient document attachments
4. Add patient consent management
5. Add patient communication preferences
6. Add patient insurance information
7. Add patient emergency contacts

## Related Modules

- **Appointments**: Schedule patient appointments
- **Prescriptions**: Create prescriptions for patients
- **Payments**: Track patient payments and invoices
- **Visits**: Record patient visit details

## Support

For issues or questions:
- Check `/docs` endpoint for interactive API documentation
- Review test files for usage examples
- See CLAUDE.md for project guidelines
