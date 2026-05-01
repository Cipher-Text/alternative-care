# AltCare API Endpoints

**Total:** 71 endpoints across 7 modules  
**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer JWT token (except `/auth/register` and `/auth/login`)

---

## Authentication (9 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new doctor account | No |
| POST | `/auth/login` | Login and get JWT tokens | No |
| POST | `/auth/refresh` | Refresh access token | Yes (refresh token) |
| POST | `/auth/logout` | Logout and invalidate session | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/password/change` | Change password | Yes |
| POST | `/auth/2fa/setup` | Setup 2FA (get QR code) | Yes |
| POST | `/auth/2fa/verify` | Verify 2FA code | Yes |
| POST | `/auth/2fa/disable` | Disable 2FA | Yes |

---

## Doctor Profile (12 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/doctor/profile` | Get doctor profile | Yes |
| PATCH | `/doctor/profile` | Update doctor profile | Yes |
| POST | `/doctor/degrees` | Add medical degree | Yes |
| GET | `/doctor/degrees` | List all degrees | Yes |
| GET | `/doctor/degrees/{degree_id}` | Get degree details | Yes |
| PATCH | `/doctor/degrees/{degree_id}` | Update degree | Yes |
| DELETE | `/doctor/degrees/{degree_id}` | Delete degree | Yes |
| POST | `/doctor/trainings` | Add training/certification | Yes |
| GET | `/doctor/trainings` | List all trainings | Yes |
| GET | `/doctor/trainings/{training_id}` | Get training details | Yes |
| PATCH | `/doctor/trainings/{training_id}` | Update training | Yes |
| DELETE | `/doctor/trainings/{training_id}` | Delete training | Yes |

---

## Patients (14 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/patients` | Create new patient | Yes |
| GET | `/patients` | List patients (with filters) | Yes |
| GET | `/patients/count` | Get patient count | Yes |
| GET | `/patients/{patient_id}` | Get patient details | Yes |
| PATCH | `/patients/{patient_id}` | Update patient | Yes |
| DELETE | `/patients/{patient_id}` | Delete patient | Yes |
| POST | `/patients/{patient_id}/tags` | Add patient tag | Yes |
| GET | `/patients/{patient_id}/tags` | List patient tags | Yes |
| PATCH | `/patients/tags/{tag_id}` | Update tag | Yes |
| DELETE | `/patients/tags/{tag_id}` | Delete tag | Yes |
| POST | `/patients/{patient_id}/diagnoses` | Add diagnosis | Yes |
| GET | `/patients/{patient_id}/diagnoses` | List diagnoses | Yes |
| PATCH | `/patients/diagnoses/{diagnosis_id}` | Update diagnosis | Yes |
| DELETE | `/patients/diagnoses/{diagnosis_id}` | Delete diagnosis | Yes |

---

## Appointments (10 endpoints)

### Appointments (6 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/appointments/appointments` | Create appointment | Yes |
| GET | `/appointments/appointments` | List appointments (with filters) | Yes |
| GET | `/appointments/appointments/{appointment_id}` | Get appointment details | Yes |
| PATCH | `/appointments/appointments/{appointment_id}` | Update appointment | Yes |
| POST | `/appointments/appointments/{appointment_id}/cancel` | Cancel appointment | Yes |
| DELETE | `/appointments/appointments/{appointment_id}` | Delete appointment | Yes |

### Visits (4 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/appointments/appointments/visits` | Create visit record | Yes |
| GET | `/appointments/appointments/visits` | List visits | Yes |
| GET | `/appointments/appointments/visits/{visit_id}` | Get visit details | Yes |
| PATCH | `/appointments/appointments/visits/{visit_id}` | Update visit | Yes |

---

## Prescriptions (8 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/prescriptions` | Create prescription (draft) | Yes |
| GET | `/prescriptions` | List prescriptions | Yes |
| GET | `/prescriptions/{prescription_id}` | Get prescription details | Yes |
| PATCH | `/prescriptions/{prescription_id}` | Update prescription (draft only) | Yes |
| POST | `/prescriptions/{prescription_id}/void` | Void prescription | Yes |
| POST | `/prescriptions/{prescription_id}/items` | Add prescription item | Yes |
| DELETE | `/prescriptions/{prescription_id}/items/{item_id}` | Delete prescription item | Yes |
| POST | `/prescriptions/{prescription_id}/generate-pdf` | Generate PDF | Yes |

---

## Payments (12 endpoints)

### Payments (4 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payments` | Create manual payment (cash) | Yes |
| GET | `/payments` | List payments (with filters) | Yes |
| GET | `/payments/summary` | Get payment summary stats | Yes |
| GET | `/payments/{payment_id}` | Get payment details | Yes |

### bKash Integration (3 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payments/bkash/create` | Create bKash payment | Yes |
| POST | `/payments/bkash/execute` | Execute bKash payment | Yes |
| POST | `/payments/bkash/query` | Query bKash payment status | Yes |

### Invoices (5 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payments/invoices` | Create invoice | Yes |
| GET | `/payments/invoices` | List invoices | Yes |
| GET | `/payments/invoices/{invoice_id}` | Get invoice details | Yes |
| PATCH | `/payments/invoices/{invoice_id}` | Update invoice | Yes |
| POST | `/payments/invoices/{invoice_id}/generate-pdf` | Generate invoice PDF | Yes |

---

## Dashboard (6 endpoints)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/dashboard/overview` | High-level overview stats | Yes |
| GET | `/dashboard/financial` | Financial analytics | Yes |
| GET | `/dashboard/patients` | Patient analytics | Yes |
| GET | `/dashboard/appointments` | Appointment analytics | Yes |
| GET | `/dashboard/visits` | Visit analytics | Yes |
| GET | `/dashboard/prescriptions` | Prescription analytics | Yes |

**Note:** All dashboard endpoints support optional `date_from` and `date_to` query parameters for filtering.

---

## Common Query Parameters

### Pagination
- `limit` (integer): Number of results (default: 100, max: 500)
- `offset` (integer): Skip N results (default: 0)

### Filtering
- `date_from` (date): Start date (YYYY-MM-DD)
- `date_to` (date): End date (YYYY-MM-DD)
- `status` (string): Filter by status
- `patient_id` (uuid): Filter by patient
- `visit_id` (uuid): Filter by visit

---

## Response Formats

### Success Response
```json
{
  "id": "uuid",
  "field1": "value",
  "field2": 123,
  "created_at": "2026-05-01T10:30:00Z",
  "updated_at": "2026-05-01T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

### List Response
```json
[
  {
    "id": "uuid",
    "field1": "value"
  },
  {
    "id": "uuid2",
    "field2": "value2"
  }
]
```

---

## Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `501 Not Implemented` - Feature pending implementation

---

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Token Expiry:**
- Access tokens: 30 minutes
- Refresh tokens: 7 days

**Refresh Flow:**
1. Access token expires (401 Unauthorized)
2. Call `POST /auth/refresh` with refresh token
3. Receive new access token
4. Update Authorization header with new token

---

## Interactive Documentation

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc  
**OpenAPI JSON:** http://localhost:8000/openapi.json

---

**Last Updated:** May 1, 2026  
**API Version:** 0.8.0-alpha  
**For detailed usage examples, see module READMEs in `app/modules/*/README.md`**
