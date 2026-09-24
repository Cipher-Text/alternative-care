# AltCare API Endpoints

**Total:** 136 endpoints across 14 modules (+ `/`, `/health`, `/metrics`)
**Base URL:** `http://localhost:8000/api/v1`
**Auth:** Bearer JWT (except `/auth/register`, `/auth/login`, `/auth/login-2fa`, `/auth/google`, `/auth/google/register`, `/auth/password/forgot`, `/auth/password/reset`, `/auth/email/verify`, `/auth/email/resend`)
**Interactive Docs:** http://localhost:8000/docs

> This file is a human-maintained overview. For the authoritative route table, use the live Swagger UI or `docs/api/README.md`.

---

## 1. Authentication (21)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new doctor account | No |
| POST | `/auth/admin/provision-client` | Admin: create tenant + primary doctor | Admin |
| GET | `/auth/admin/clients` | Admin: list tenant clients | Admin |
| GET | `/auth/admin/clients/{tenant_id}` | Admin: get client detail | Admin |
| GET | `/auth/admin/tenants/pending` | Admin: list pending tenants | Admin |
| POST | `/auth/admin/tenants/{tenant_id}/approve` | Admin: approve tenant | Admin |
| POST | `/auth/login` | Login and get JWT tokens (or a 2FA challenge) | No |
| POST | `/auth/login-2fa` | Complete login by resubmitting email/password + TOTP code | No |
| POST | `/auth/google` | Sign in with a Google ID token; offers registration if no account exists | No |
| POST | `/auth/google/register` | Complete doctor + tenant registration for a verified Google identity | No |
| POST | `/auth/logout` | Logout and invalidate session | Yes |
| POST | `/auth/refresh` | Refresh access token (rotates refresh token) | Refresh token |
| POST | `/auth/2fa/setup` | Setup 2FA (get TOTP secret + QR code) | Yes |
| POST | `/auth/2fa/verify` | Verify TOTP code and enable 2FA | Yes |
| POST | `/auth/2fa/disable` | Disable 2FA (requires password + TOTP) | Yes |
| POST | `/auth/password/change` | Change password for authenticated user | Yes |
| POST | `/auth/password/forgot` | Request a password reset email (always returns same message) | No |
| POST | `/auth/password/reset` | Reset password using emailed token; invalidates all sessions | No |
| GET | `/auth/me` | Get current user profile with tenant info | Yes |
| POST | `/auth/email/verify` | Verify email address using emailed token | No |
| POST | `/auth/email/resend` | Resend verification email (always returns same message) | No |

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
| DELETE | `/patients/tags/{tag_id}` | Delete tag (hard delete) | Yes |
| POST | `/patients/{patient_id}/diagnoses` | Add diagnosis | Yes |
| GET | `/patients/{patient_id}/diagnoses` | List diagnoses | Yes |
| PATCH | `/patients/diagnoses/{diagnosis_id}` | Update diagnosis | Yes |
| DELETE | `/patients/diagnoses/{diagnosis_id}` | Soft delete diagnosis | Yes |

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
| DELETE | `/appointments/{id}` | Delete appointment (hard delete) | Yes |

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
| POST | `/prescriptions` | Create prescription (draft or issued) with items | Yes |
| GET | `/prescriptions` | List prescriptions | Yes |
| GET | `/prescriptions/{prescription_id}` | Get prescription details | Yes |
| PATCH | `/prescriptions/{prescription_id}` | Update (draft only) | Yes |
| POST | `/prescriptions/{prescription_id}/void` | Void prescription | Yes |
| POST | `/prescriptions/{prescription_id}/items` | Add prescription item (draft only) | Yes |
| DELETE | `/prescriptions/{prescription_id}/items/{item_id}` | Delete item (draft only) | Yes |
| POST | `/prescriptions/{prescription_id}/generate-pdf` | Generate PDF (issued only) | Yes |

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
| POST | `/payments/bkash/create` | Create bKash payment, get payment URL | Yes |
| POST | `/payments/bkash/execute` | Execute bKash payment (stub — returns 501, not implemented) | Yes |
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
| GET | `/integrations/providers` | List all providers (SMS/Email/Payment) | Yes |
| GET | `/integrations/providers/{provider_id}` | Get provider details | Yes |

### Tenant Integrations (7)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/integrations` | Add integration config | Yes |
| GET | `/integrations` | List tenant integrations | Yes |
| GET | `/integrations/{integration_id}` | Get integration details | Yes |
| PATCH | `/integrations/{integration_id}` | Update integration | Yes |
| DELETE | `/integrations/{integration_id}` | Delete integration | Yes |
| POST | `/integrations/{integration_id}/test` | Test integration | Yes |
| POST | `/integrations/{integration_id}/set-primary` | Set as primary | Yes |

### Send Operations (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/integrations/send/sms` | Send SMS via configured provider (queued via Celery) | Yes |
| POST | `/integrations/send/email` | Send email via configured provider (queued via Celery) | Yes |

### Logs (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/integrations/logs` | List integration logs | Yes |

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

## 9. Medicines (15)

### Medicine CRUD (5)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/medicines` | List medicines (global + tenant-specific) | Yes |
| POST | `/medicines` | Create medicine (global requires admin role) | Yes |
| GET | `/medicines/{medicine_id}` | Get medicine details | Yes |
| PATCH | `/medicines/{medicine_id}` | Update medicine (tenant-owned only, not global) | Yes |
| DELETE | `/medicines/{medicine_id}` | Deactivate medicine (tenant-owned only, not global) | Yes |

### Search (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/medicines/search` | Autocomplete search by name/alias (English/Bengali) | Yes |

### Aliases (3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/medicines/{medicine_id}/aliases` | Create medicine alias | Yes |
| GET | `/medicines/{medicine_id}/aliases` | List aliases for a medicine | Yes |
| DELETE | `/medicines/aliases/{alias_id}` | Delete medicine alias | Yes |

### Symptom Mappings (4)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/medicines/mappings` | Link medicine to symptom | Yes |
| GET | `/medicines/mappings/{mapping_id}` | Get mapping details | Yes |
| PATCH | `/medicines/mappings/{mapping_id}` | Update mapping (strength, modality) | Yes |
| DELETE | `/medicines/mappings/{mapping_id}` | Delete mapping | Yes |

### Lookups (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/medicines/{medicine_id}/symptoms` | Get symptoms linked to a medicine | Yes |
| GET | `/medicines/symptoms/{symptom_id}/medicines` | Get medicines linked to a symptom | Yes |

**Note:** Only admins can create global medicines (`is_global=true`); doctors can create tenant-specific ones.

---

## 10. Symptoms (9)

### Symptom CRUD (5)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/symptoms` | List symptoms (global + tenant-specific) | Yes |
| POST | `/symptoms` | Create symptom (global requires admin role) | Yes |
| GET | `/symptoms/{symptom_id}` | Get symptom details | Yes |
| PATCH | `/symptoms/{symptom_id}` | Update symptom (tenant-owned only, not global) | Yes |
| DELETE | `/symptoms/{symptom_id}` | Deactivate symptom (tenant-owned only, not global) | Yes |

### Search (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/symptoms/search` | Autocomplete search by name/alias (English/Bengali) | Yes |

### Aliases (3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/symptoms/{symptom_id}/aliases` | Create symptom alias | Yes |
| GET | `/symptoms/{symptom_id}/aliases` | List aliases for a symptom | Yes |
| DELETE | `/symptoms/aliases/{alias_id}` | Delete symptom alias | Yes |

**Note:** Only admins can create global symptoms (`is_global=true`); doctors can create tenant-specific ones.

---

## 11. Geographic (3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/geographic/divisions` | List all Bangladesh divisions (8 total) | Yes |
| GET | `/geographic/divisions/{division_id}/districts` | List districts for a division | Yes |
| GET | `/geographic/districts/{district_id}/upazilas` | List upazilas for a district | Yes |

---

## 12. Tenant/Clinic (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/tenant/profile` | Get clinic/tenant profile | Yes |
| PATCH | `/tenant/profile` | Update clinic profile (doctor role only, 403 otherwise) | Yes |

---

## 13. Platform Admin (11)

### Dashboard (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/dashboard` | Platform KPI dashboard (tenant/user counts, plan breakdown) | Admin |

### Tenant Management (8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/tenants` | List all tenants with primary doctor summaries | Admin |
| POST | `/admin/tenants` | Provision tenant + primary doctor in one operation | Admin |
| GET | `/admin/tenants/pending` | List tenants pending approval | Admin |
| GET | `/admin/tenants/{tenant_id}` | Get tenant detail and all users | Admin |
| GET | `/admin/tenants/{tenant_id}/usage` | Get tenant's month-to-date usage (prescriptions, SMS, AI queries, PDFs) | Admin |
| POST | `/admin/tenants/{tenant_id}/approve` | Approve a pending tenant | Admin |
| PATCH | `/admin/tenants/{tenant_id}` | Change plan, suspend, or reactivate a tenant | Admin |
| POST | `/admin/tenants/{tenant_id}/doctors` | Add another doctor user to an existing tenant | Admin |

### Users (2)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/users` | List all users with role summary (filter by role/tenant/status) | Admin |
| PATCH | `/admin/users/{user_id}` | Update user role or active status (invalidates JWT tokens) | Admin |

---

## 14. AI (1)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/ai/query` | AI query (stub — always returns 501 Not Implemented) | Yes (Pro plan) |

**Status:** Registered but unimplemented. Gated by `RequireProPlan`; the RAG-based assistant over the book library, medicine DB, and symptom DB is planned for a future phase (see `docs/planning/revision-2026-09.md`).

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

**Required:** All endpoints except `/auth/register`, `/auth/login`, `/auth/login-2fa`, `/auth/google`, `/auth/google/register`, `/auth/password/forgot`, `/auth/password/reset`, `/auth/email/verify`, and `/auth/email/resend`

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
