# AltCare API Endpoints

**Total:** 127 endpoints across 14 modules
**Base URL:** `http://localhost:8000/api/v1`
**Auth:** Bearer JWT (except `/auth/register` and `/auth/login`)
**Interactive Docs:** http://localhost:8000/docs

> This file is a human-maintained overview. For the authoritative route table, use the live Swagger UI or `docs/api/README.md`.

---

## 1. Authentication (9)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new doctor account | No |
| POST | `/auth/login` | Login and get JWT tokens | No |
| POST | `/auth/refresh` | Refresh access token | Refresh token |
| POST | `/auth/logout` | Logout and invalidate session | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/password/change` | Change password | Yes |
| POST | `/auth/2fa/setup` | Setup 2FA (get QR code) | Yes |
| POST | `/auth/2fa/verify` | Verify 2FA code | Yes |
| POST | `/auth/2fa/disable` | Disable 2FA | Yes |

**Tokens:**
- Access: 30min expiry
- Refresh: 7d expiry

---

## 2. Doctor Profile (12)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
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

## 3. Patients (14)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/patients` | Create new patient | Yes |
| GET | `/patients` | List patients (with filters) | Yes |
| GET | `/patients/count` | Get patient count | Yes |
| GET | `/patients/{patient_id}` | Get patient details | Yes |
| PATCH | `/patients/{patient_id}` | Update patient | Yes |
| DELETE | `/patients/{patient_id}` | Soft delete patient | Yes |
| POST | `/patients/{patient_id}/tags` | Add patient tag | Yes |
| GET | `/patients/{patient_id}/tags` | List patient tags | Yes |
| PATCH | `/patients/tags/{tag_id}` | Update tag | Yes |
| DELETE | `/patients/tags/{tag_id}` | Delete tag | Yes |
| POST | `/patients/{patient_id}/diagnoses` | Add diagnosis | Yes |
| GET | `/patients/{patient_id}/diagnoses` | List diagnoses | Yes |
| PATCH | `/patients/diagnoses/{diagnosis_id}` | Update diagnosis | Yes |
| DELETE | `/patients/diagnoses/{diagnosis_id}` | Delete diagnosis | Yes |

**Query Params:** `search`, `limit`, `offset`, `sort_by`, `sort_order`

---

## 4. Appointments (10)

### Appointments (6)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/appointments` | Create appointment | Yes |
| GET | `/appointments` | List appointments | Yes |
| GET | `/appointments/{id}` | Get appointment details | Yes |
| PATCH | `/appointments/{id}` | Update appointment | Yes |
| POST | `/appointments/{id}/cancel` | Cancel appointment | Yes |
| DELETE | `/appointments/{id}` | Delete appointment | Yes |

### Visits (4)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/appointments/visits` | Create visit record | Yes |
| GET | `/appointments/visits` | List visits | Yes |
| GET | `/appointments/visits/{id}` | Get visit details | Yes |
| PATCH | `/appointments/visits/{id}` | Update visit | Yes |

**Query Params:** `date_from`, `date_to`, `status`, `patient_id`

---

## 5. Prescriptions (8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/prescriptions` | Create prescription (draft) | Yes |
| GET | `/prescriptions` | List prescriptions | Yes |
| GET | `/prescriptions/{prescription_id}` | Get prescription details | Yes |
| PATCH | `/prescriptions/{prescription_id}` | Update (draft only) | Yes |
| POST | `/prescriptions/{prescription_id}/void` | Void prescription | Yes |
| POST | `/prescriptions/{prescription_id}/items` | Add prescription item | Yes |
| DELETE | `/prescriptions/{prescription_id}/items/{item_id}` | Delete item | Yes |
| POST | `/prescriptions/{prescription_id}/generate-pdf` | Generate PDF | Yes |

**Workflow:** draft → issued → voided (immutable after issued)

---

## 6. Payments (12)

### Payments (4)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/payments` | Create manual payment (cash) | Yes |
| GET | `/payments` | List payments | Yes |
| GET | `/payments/summary` | Payment summary stats | Yes |
| GET | `/payments/{payment_id}` | Get payment details | Yes |

### bKash Integration (3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/payments/bkash/create` | Create bKash payment | Yes |
| POST | `/payments/bkash/execute` | Execute bKash payment | Yes |
| POST | `/payments/bkash/query` | Query payment status | Yes |

### Invoices (5)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/payments/invoices` | Create invoice | Yes |
| GET | `/payments/invoices` | List invoices | Yes |
| GET | `/payments/invoices/{invoice_id}` | Get invoice details | Yes |
| PATCH | `/payments/invoices/{invoice_id}` | Update invoice | Yes |
| POST | `/payments/invoices/{invoice_id}/generate-pdf` | Generate PDF | Yes |

---

## 7. Integration (12)

### Providers (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/integration/providers` | List all providers (SMS/Email/Payment) | Yes |
| GET | `/integration/providers/{provider_id}` | Get provider details | Yes |

### Tenant Integrations (7)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/integration/integrations` | Add integration config | Yes |
| GET | `/integration/integrations` | List tenant integrations | Yes |
| GET | `/integration/integrations/{integration_id}` | Get integration details | Yes |
| PATCH | `/integration/integrations/{integration_id}` | Update integration | Yes |
| DELETE | `/integration/integrations/{integration_id}` | Delete integration | Yes |
| POST | `/integration/integrations/{integration_id}/test` | Test integration | Yes |
| POST | `/integration/integrations/{integration_id}/set-primary` | Set as primary | Yes |

### Send Operations (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/integration/send-sms` | Send SMS via configured provider | Yes |
| POST | `/integration/send-email` | Send email via configured provider | Yes |

### Logs (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/integration/logs` | List integration logs | Yes |

**Providers:** bKash, BulkSMSBD, SMTP (credentials encrypted with Fernet)

---

## 8. Dashboard (6)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/dashboard/overview` | High-level overview stats | Yes |
| GET | `/dashboard/financial` | Financial analytics | Yes |
| GET | `/dashboard/patients` | Patient analytics | Yes |
| GET | `/dashboard/appointments` | Appointment analytics | Yes |
| GET | `/dashboard/visits` | Visit analytics | Yes |
| GET | `/dashboard/prescriptions` | Prescription analytics | Yes |

**Query Params:** All endpoints support `date_from` and `date_to` (YYYY-MM-DD)

---

## Common Patterns

### Pagination

```
GET /patients?limit=50&offset=0
```

- `limit`: Results per page (default: 100, max: 500)
- `offset`: Skip N results (default: 0)

### Filtering

```
GET /appointments?date_from=2026-05-01&date_to=2026-05-31&status=scheduled
```

- `date_from`, `date_to`: Date range (YYYY-MM-DD)
- `status`: Filter by status
- `patient_id`: Filter by patient UUID

### Sorting

```
GET /patients?sort_by=created_at&sort_order=desc
```

- `sort_by`: Field name
- `sort_order`: `asc` or `desc`

---

## Response Formats

### Success (200/201)

```json
{
  "id": "uuid",
  "name": "John Doe",
  "created_at": "2026-05-01T10:30:00Z",
  "updated_at": "2026-05-01T10:30:00Z"
}
```

### List (200)

```json
[
  { "id": "uuid1", "name": "Patient 1" },
  { "id": "uuid2", "name": "Patient 2" }
]
```

### Error (4xx/5xx)

```json
{
  "detail": "Error message or validation details"
}
```

---

## Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Success (read/update) |
| 201 | Created | Resource created |
| 204 | No Content | Success with no body (delete) |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |
| 501 | Not Implemented | Feature pending |

---

## Authentication

**Required:** All endpoints except `/auth/register` and `/auth/login`

**Header:**
```
Authorization: Bearer <access_token>
```

**Token Refresh Flow:**
1. Access token expires → 401 Unauthorized
2. Call `POST /auth/refresh` with refresh token
3. Get new access token
4. Retry request with new token

**Frontend:** Auto-refresh implemented in Axios interceptor (`frontend/src/lib/api/client.ts`)

---

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

**See [CLAUDE.md](../CLAUDE.md) for architecture and implementation details.**
