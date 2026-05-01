---
title: "AltCare API Overview"
type: "api-reference"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "71 REST endpoints across 7 modules with JWT authentication"
base_url: "http://localhost:8000/api/v1"
---

# AltCare API Documentation

**Base URL:** `http://localhost:8000/api/v1`  
**Total Endpoints:** 71  
**Authentication:** JWT Bearer Token  
**Format:** JSON

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Modules](#modules)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🌐 Overview

**7 API Modules:**

| Module | Endpoints | Purpose | Docs |
|--------|-----------|---------|------|
| **Authentication** | 9 | Login, 2FA, tokens | [authentication.md](authentication.md) |
| **Patients** | 14 | Patient CRUD, search | [patients.md](patients.md) |
| **Appointments** | 10 | Scheduling, visits | [appointments.md](appointments.md) |
| **Prescriptions** | 8 | Prescription builder | [prescriptions.md](prescriptions.md) |
| **Payments** | 12 | Payments, invoices | [payments.md](payments.md) |
| **Dashboard** | 6 | Analytics, charts | [dashboard.md](dashboard.md) |
| **Doctor** | 12 | Profile, credentials | [doctor.md](doctor.md) |

**Total:** 71 endpoints

---

## 🔐 Authentication

All endpoints (except login/register) require authentication.

### **Getting a Token:**

```bash
POST /auth/login
{
  "email": "doctor@clinic.com",
  "password": "password"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

### **Using the Token:**

```bash
GET /patients
Authorization: Bearer eyJ...
```

**See:** [authentication.md](authentication.md) for full auth flow

---

## 📦 Modules

### 1. Authentication (9 endpoints)
- Login (password + 2FA)
- Token refresh
- Logout
- User management

**Docs:** [authentication.md](authentication.md)

### 2. Patients (14 endpoints)
- CRUD operations
- Search & filter
- Tags & diagnoses
- Visit history

**Docs:** [patients.md](patients.md)

### 3. Appointments (10 endpoints)
- Create/update appointments
- Conflict detection
- Visit management
- Status tracking

**Docs:** [appointments.md](appointments.md)

### 4. Prescriptions (8 endpoints)
- Prescription builder
- Add/remove items
- PDF generation
- Immutable workflow (draft → issued → voided)

**Docs:** [prescriptions.md](prescriptions.md)

### 5. Payments (12 endpoints)
- Manual payments (cash)
- bKash integration
- Invoice generation
- Payment tracking

**Docs:** [payments.md](payments.md)

### 6. Dashboard (6 endpoints)
- Overview stats
- Financial analytics
- Patient analytics
- Charts & trends

**Docs:** [dashboard.md](dashboard.md)

### 7. Doctor (12 endpoints)
- Profile management
- Degrees & certifications
- Training records
- Verification

**Docs:** [doctor.md](doctor.md)

---

## 🔄 Common Patterns

### **Pagination**

```bash
GET /patients?skip=0&limit=20
```

### **Search**

```bash
GET /patients?search=john
GET /patients/search?q=john
```

### **Filtering**

```bash
GET /patients?gender=male
GET /payments?status=paid&method=cash
```

### **Date Ranges**

```bash
GET /dashboard/overview?date_from=2026-01-01&date_to=2026-12-31
```

### **Sorting**

```bash
GET /patients?sort_by=created_at&order=desc
```

---

## ❌ Error Handling

### **Standard Error Response:**

```json
{
  "detail": "Error message here"
}
```

### **Common Status Codes:**

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Resource retrieved |
| 201 | Created | New resource created |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Validation Error | Invalid input data |
| 500 | Server Error | Internal server error |

### **Validation Errors:**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🚦 Rate Limiting

**Current:** No rate limiting  
**Planned:** 100 requests/minute per user (Phase 2)

---

## 🔗 Quick Links

**Module Docs:**
- [Authentication](authentication.md) - Login, 2FA, tokens
- [Patients](patients.md) - Patient management
- [Appointments](appointments.md) - Scheduling
- [Prescriptions](prescriptions.md) - Prescription builder
- [Payments](payments.md) - Payment processing
- [Dashboard](dashboard.md) - Analytics
- [Doctor](doctor.md) - Doctor profile

**Architecture:**
- [Authentication Design](../architecture/authentication.md)
- [Multi-Tenancy](../architecture/multi-tenancy.md)
- [Database Schema](../architecture/database-schema.md)

**Setup:**
- [Backend Setup](../setup/backend.md)
- [API Testing](../development/testing.md)

---

## 🤖 AI Quick Reference

**Common Questions:**

**Q: How do I authenticate?**
→ POST /auth/login → Use access_token in Authorization header

**Q: How do I create a patient?**
→ POST /patients with required fields (see patients.md)

**Q: How do I get analytics?**
→ GET /dashboard/overview (see dashboard.md)

**Q: How do I handle errors?**
→ Check status code + detail message

**Q: Are requests tenant-scoped?**
→ Yes, automatically filtered by tenant_id from JWT

---

**Last Updated:** May 1, 2026  
**API Version:** 0.9.0  
**Total Endpoints:** 71 ✅
