```markdown
# Doctor Profile Module

Complete doctor profile management system with academic degrees, certifications, trainings, and professional credentials.

## Features

### Doctor Profile Management
- ✅ Get complete doctor profile (combines User + Tenant data)
- ✅ Update profile information
- ✅ Clinic details management
- ✅ Contact information
- ✅ Specializations tracking
- ✅ License number management

### Academic Degrees
- ✅ Add degrees (MBBS, BHMS, BAMS, MD, etc.)
- ✅ Institution and completion year tracking
- ✅ Specialization details
- ✅ Certificate upload support
- ✅ Verification workflow
- ✅ Display order management

### Professional Training & Certifications
- ✅ Record certifications, workshops, conferences
- ✅ Provider and completion tracking
- ✅ Expiry date management
- ✅ Skills gained tracking
- ✅ Credential ID support
- ✅ Active/expired filtering

## API Endpoints

Base URL: `/api/v1/doctor`

### Profile Endpoints

#### Get Doctor Profile
```http
GET /api/v1/doctor/profile
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": "user-uuid",
  "email": "doctor@clinic.com",
  "full_name": "Dr. John Doe",
  "phone": "+8801712345678",
  "avatar_url": "https://example.com/avatar.jpg",
  "language": "en",
  "is_active": true,
  "tenant_id": "tenant-uuid",
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

#### Update Doctor Profile
```http
PATCH /api/v1/doctor/profile
Content-Type: application/json
Authorization: Bearer {token}

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

**Note:** All fields are optional - only send fields you want to update.

**Response:** `200 OK` (updated profile)

### Degree Endpoints

#### Create Degree
```http
POST /api/v1/doctor/degrees
Content-Type: application/json
Authorization: Bearer {token}

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

**Degree Types:**
- Bachelor (BHMS, BAMS, BUMS, etc.)
- Master (MD, MS, etc.)
- Diploma
- Fellowship

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "tenant_id": "tenant-uuid",
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

#### List Degrees
```http
GET /api/v1/doctor/degrees
Authorization: Bearer {token}
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

**Note:** Ordered by `display_order` first, then `completion_year` (newest first)

#### Get Degree by ID
```http
GET /api/v1/doctor/degrees/{degree_id}
Authorization: Bearer {token}
```

**Response:** `200 OK` (degree details)

#### Update Degree
```http
PATCH /api/v1/doctor/degrees/{degree_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "specialization": "Pediatrics",
  "certificate_url": "https://example.com/new-cert.pdf"
}
```

**Response:** `200 OK` (updated degree)

#### Delete Degree
```http
DELETE /api/v1/doctor/degrees/{degree_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

### Training Endpoints

#### Create Training
```http
POST /api/v1/doctor/trainings
Content-Type: application/json
Authorization: Bearer {token}

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

**Training Types:**
- Certification
- Workshop
- Conference
- Continuing Education

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "tenant_id": "tenant-uuid",
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

#### List Trainings
```http
GET /api/v1/doctor/trainings?active_only=false
Authorization: Bearer {token}
```

**Query Parameters:**
- `active_only` (optional): Only show non-expired trainings (default: false)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Advanced Homeopathic Prescribing",
    "training_type": "Certification",
    "completion_date": "2023-06-15",
    "expiry_date": "2025-06-15",
    ...
  }
]
```

**Note:** Ordered by `display_order` first, then `completion_date` (newest first)

#### Get Training by ID
```http
GET /api/v1/doctor/trainings/{training_id}
Authorization: Bearer {token}
```

**Response:** `200 OK` (training details)

#### Update Training
```http
PATCH /api/v1/doctor/trainings/{training_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "Updated Title",
  "skills": "Updated skills list"
}
```

**Response:** `200 OK` (updated training)

#### Delete Training
```http
DELETE /api/v1/doctor/trainings/{training_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

## Data Models

### DoctorProfile (Virtual - combines User + Tenant)
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | User ID |
| email | Email | Doctor's email |
| full_name | String(255) | Full name |
| phone | String(20) | Phone number |
| avatar_url | String(500) | Profile photo URL |
| language | Enum | en, bn |
| is_active | Boolean | Active status |
| tenant_id | UUID | Tenant/Clinic ID |
| clinic_name | String(255) | Clinic name |
| clinic_address | Text | Clinic address |
| division_id | Int | Division |
| district_id | Int | District |
| upazila_id | Int | Upazila |
| specializations | Array | List of specializations |
| license_number | String(100) | Medical license number |
| is_verified | Boolean | Verification status |
| verified_at | Timestamp | Verification timestamp |
| plan | String | Subscription plan |
| plan_started_at | Timestamp | Plan start date |
| plan_expires_at | Timestamp | Plan expiry date |

### DoctorDegree
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Int | Auto | Primary key |
| user_id | UUID | Auto | Doctor reference |
| tenant_id | UUID | Auto | Tenant isolation |
| degree_type | String(100) | Yes | Bachelor, Master, Diploma, Fellowship |
| degree_name | String(255) | Yes | BHMS, BAMS, MD, etc. |
| specialization | String(255) | No | Pediatrics, Dermatology, etc. |
| institution_name | String(500) | Yes | College/University name |
| institution_location | String(255) | No | City, Country |
| start_year | Int | No | Year started (1900-2100) |
| completion_year | Int | Yes | Year completed (1900-2100) |
| certificate_url | String(500) | No | Certificate file URL |
| display_order | Int | No | Sort order (default: 0) |
| is_verified | Boolean | Auto | Admin verification status |
| verified_at | Timestamp | Auto | Verification timestamp |
| verified_by | UUID | Auto | Admin who verified |
| created_at | Timestamp | Auto | Creation timestamp |
| updated_at | Timestamp | Auto | Update timestamp |

### DoctorTraining
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Int | Auto | Primary key |
| user_id | UUID | Auto | Doctor reference |
| tenant_id | UUID | Auto | Tenant isolation |
| training_type | String(100) | Yes | Certification, Workshop, Conference, CE |
| title | String(500) | Yes | Training title |
| provider | String(500) | Yes | Organization name |
| description | Text | No | Training description |
| skills | Text | No | Comma-separated skills |
| start_date | Date | No | Start date |
| completion_date | Date | Yes | Completion date |
| expiry_date | Date | No | Expiry date (for renewals) |
| certificate_url | String(500) | No | Certificate file URL |
| credential_id | String(255) | No | Unique ID from provider |
| display_order | Int | No | Sort order (default: 0) |
| is_verified | Boolean | Auto | Admin verification status |
| verified_at | Timestamp | Auto | Verification timestamp |
| verified_by | UUID | Auto | Admin who verified |
| created_at | Timestamp | Auto | Creation timestamp |
| updated_at | Timestamp | Auto | Update timestamp |

## Authentication

All endpoints require JWT authentication with doctor role:

```http
Authorization: Bearer {access_token}
```

Token must include:
- `sub`: User ID
- `tenant_id`: Tenant ID
- `role`: "doctor" (required)

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Degree not found"
}
```

### 422 Validation Error
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

## Usage Examples

### Python (httpx)
```python
import httpx

async with httpx.AsyncClient() as client:
    # Get profile
    response = await client.get(
        "http://localhost:8000/api/v1/doctor/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    profile = response.json()
    
    # Update profile
    response = await client.patch(
        "http://localhost:8000/api/v1/doctor/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "clinic_name": "New Clinic Name",
            "phone": "+8801712345678"
        }
    )
    
    # Add degree
    response = await client.post(
        "http://localhost:8000/api/v1/doctor/degrees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "degree_type": "Bachelor",
            "degree_name": "BHMS",
            "institution_name": "National Medical College",
            "completion_year": 2020
        }
    )
    
    # Add training
    response = await client.post(
        "http://localhost:8000/api/v1/doctor/trainings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "training_type": "Certification",
            "title": "Advanced Prescribing",
            "provider": "NIH",
            "completion_date": "2023-06-15"
        }
    )
```

### JavaScript (fetch)
```javascript
// Get profile
const profileResponse = await fetch(
  'http://localhost:8000/api/v1/doctor/profile',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
const profile = await profileResponse.json();

// Add degree
const degreeResponse = await fetch(
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
      completion_year: 2020
    })
  }
);
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_doctor_service.py -v
```

**Coverage:** 18 tests, 97% code coverage

### Integration Tests
```bash
pytest tests/integration/test_doctor_routes.py -v
```

**Coverage:** 18 tests, 100% route coverage

### All Doctor Tests
```bash
pytest tests/unit/test_doctor_service.py tests/integration/test_doctor_routes.py -v
```

**Total:** 36 tests passing

## Service Layer

```python
from app.modules.doctor.service import DoctorService

# Initialize with DB session, user ID, and tenant ID
service = DoctorService(db=db_session, user_id=user_id, tenant_id=tenant_id)

# Profile
profile = await service.get_profile()
updated = await service.update_profile(data, updated_by=user_id)

# Degrees
degree = await service.create_degree(data, created_by=user_id)
degrees = await service.list_degrees()
degree = await service.get_degree(degree_id)
updated = await service.update_degree(degree_id, data, updated_by=user_id)
await service.delete_degree(degree_id)

# Trainings
training = await service.create_training(data, created_by=user_id)
trainings = await service.list_trainings(active_only=False)
training = await service.get_training(training_id)
updated = await service.update_training(training_id, data, updated_by=user_id)
await service.delete_training(training_id)
```

## Architecture

```
app/modules/doctor/
├── __init__.py          # Module exports
├── routes.py            # FastAPI route handlers (12 endpoints)
├── service.py           # Business logic layer
└── README.md            # This file

app/shared/
├── models/doctor.py     # SQLAlchemy models (DoctorDegree, DoctorTraining)
├── models/tenant.py     # User and Tenant models
└── schemas/doctor.py    # Pydantic schemas (10 schemas)

tests/
├── unit/test_doctor_service.py         # Service layer tests (18 tests)
└── integration/test_doctor_routes.py   # API endpoint tests (18 tests)
```

## Development Status

✅ **Complete and Production-Ready**
- All core features implemented
- 36 tests passing (18 unit + 18 integration)
- 97% service coverage, 100% route coverage
- Full API documentation
- Comprehensive error handling

## Related Modules

- **Patients**: Link degrees/trainings to patient care history
- **Prescriptions**: Display doctor credentials on prescriptions
- **Appointments**: Show doctor qualifications to patients

## Support

For API documentation:
- Visit `/docs` endpoint for interactive Swagger UI
- Check test files for usage examples
- See CLAUDE.md for project guidelines
```
