---
title: "Authentication API"
type: "api-reference"
module: "authentication"
version: "0.9.0"
last_updated: "2026-05-14"
ai_summary: "Authentication, self-registration, and admin provisioning/approval endpoints"
endpoints: 12
authentication: "public + protected"
---

# Authentication API

**Module:** Authentication  
**Endpoints:** 12  
**Base Path:** `/api/v1/auth`

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [Endpoints](#endpoints)
  - [Login](#login)
  - [Login with 2FA](#login-with-2fa)
  - [Refresh Token](#refresh-token)
  - [Logout](#logout)
  - [Get Current User](#get-current-user)
  - [Enable 2FA](#enable-2fa)
  - [Verify 2FA Setup](#verify-2fa-setup)
  - [Disable 2FA](#disable-2fa)
  - [Update Profile](#update-profile)
- [Security](#security)

---

## 🌐 Overview

Authentication endpoints using **JWT tokens** with optional **TOTP 2FA**.

**Features:**
- ✅ JWT access + refresh tokens
- ✅ TOTP 2FA (optional)
- ✅ Token refresh mechanism
- ✅ Secure logout
- ✅ Profile management
- ✅ Public doctor self-registration (`/register`) with pending approval
- ✅ Admin client provisioning (`/admin/provision-client`)
- ✅ Admin tenant approval workflow (`/admin/tenants/pending`, `/admin/tenants/{tenant_id}/approve`)

**Token Lifetimes:**
- Access Token: 30 minutes
- Refresh Token: 7 days

---

## 🔐 Authentication Flow

### **Standard Login (No 2FA)**

```
1. POST /auth/login (email + password)
   ↓
2. Receive access_token + refresh_token
   ↓
3. Use access_token in Authorization header
```

### **Login with 2FA**

```
1. POST /auth/login (email + password)
   ↓
2. Response: user.two_factor_enabled = true
   ↓
3. POST /auth/login-2fa (email + password + totp_code)
   ↓
4. Receive access_token + refresh_token
```

### **Token Refresh**

```
When access_token expires (30 min):
1. POST /auth/refresh (refresh_token)
   ↓
2. Receive new access_token
```

---

## 📡 Endpoints

### Login

```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "doctor@clinic.com",
  "password": "securepassword"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "doctor@clinic.com",
    "full_name": "Dr. John Doe",
    "role": "doctor",
    "tenant_id": "uuid",
    "plan": "pro",
    "language": "en",
    "two_factor_enabled": false
  }
}
```

**If 2FA enabled:**
```json
{
  "detail": "2FA required",
  "user": {
    "two_factor_enabled": true
  }
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials

<!-- AI: Store access_token in cookies, not localStorage -->

---

### Login with 2FA

```http
POST /api/v1/auth/login-2fa
```

**Request Body:**
```json
{
  "email": "doctor@clinic.com",
  "password": "securepassword",
  "totp_code": "123456"
}
```

**Response:** `200 OK` (same as standard login)

**Errors:**
- `401 Unauthorized`: Invalid credentials or TOTP code

---

### Refresh Token

```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc..."
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token

<!-- AI: Frontend should auto-refresh on 401 responses -->

---

### Logout

```http
POST /api/v1/auth/logout
```

**Authentication:** Required

**Response:** `204 No Content`

<!-- AI: Clear tokens from cookies/storage after logout -->

---

### Get Current User

```http
GET /api/v1/auth/me
```

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "doctor@clinic.com",
  "full_name": "Dr. John Doe",
  "role": "doctor",
  "tenant_id": "uuid",
  "plan": "pro",
  "language": "en",
  "two_factor_enabled": false
}
```

---

### Enable 2FA

```http
POST /api/v1/auth/2fa/enable
```

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "backup_codes": [
    "ABC123",
    "DEF456",
    "GHI789"
  ]
}
```

**Next Step:** User must verify setup with `/auth/2fa/verify`

---

### Verify 2FA Setup

```http
POST /api/v1/auth/2fa/verify
```

**Authentication:** Required

**Request Body:**
```json
{
  "totp_code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "message": "2FA enabled successfully"
}
```

**Errors:**
- `400 Bad Request`: Invalid TOTP code

---

### Disable 2FA

```http
POST /api/v1/auth/2fa/disable
```

**Authentication:** Required

**Request Body:**
```json
{
  "password": "securepassword"
}
```

**Response:** `200 OK`

**Errors:**
- `401 Unauthorized`: Invalid password

---

### Update Profile

```http
PUT /api/v1/auth/profile
```

**Authentication:** Required

**Request Body:**
```json
{
  "full_name": "Dr. Jane Doe",
  "language": "bn"
}
```

**Response:** `200 OK`

---

## 🔒 Security

### **JWT Structure**

**Access Token Claims:**
```json
{
  "sub": "user_id",
  "tenant_id": "uuid",
  "role": "doctor",
  "email": "doctor@clinic.com",
  "plan": "pro",
  "exp": 1234567890,
  "type": "access"
}
```

**Token Storage:**
- ✅ **DO:** Store in httpOnly cookies
- ❌ **DON'T:** Store in localStorage (XSS vulnerable)

### **Password Requirements**

- Minimum 6 characters (production should be 8+)
- Bcrypt hashing (12 rounds)

### **2FA Implementation**

- TOTP algorithm (RFC 6238)
- 6-digit codes
- 30-second time window
- QR code for setup

### **Rate Limiting**

Currently: None  
Planned: 5 failed login attempts → 15-minute lockout

---

## 💡 Examples

### Login Flow (Python)

```python
import requests

# Step 1: Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "doctor@clinic.com", "password": "password"}
)
data = response.json()

# Step 2: Store token
access_token = data["access_token"]

# Step 3: Use token
headers = {"Authorization": f"Bearer {access_token}"}
patients = requests.get(
    "http://localhost:8000/api/v1/patients",
    headers=headers
).json()
```

### Token Refresh (JavaScript)

```javascript
// Auto-refresh on 401
async function apiCall(url) {
  let response = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` }
  })

  if (response.status === 401) {
    // Refresh token
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    })
    
    const { access_token } = await refreshResponse.json()
    accessToken = access_token
    
    // Retry original request
    response = await fetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  }
  
  return response.json()
}
```

---

## 🤖 AI Quick Reference

**Q: How do I get a JWT token?**
→ POST /auth/login with email + password

**Q: How long does the token last?**
→ Access: 30 min, Refresh: 7 days

**Q: How do I enable 2FA?**
→ POST /auth/2fa/enable → scan QR → POST /auth/2fa/verify

**Q: Where should I store tokens?**
→ httpOnly cookies (NOT localStorage)

**Q: How do I logout?**
→ POST /auth/logout + clear local tokens

---

**See Also:**
- [Authentication Design](../architecture/authentication.md) - JWT + 2FA architecture
- [Multi-Tenancy](../architecture/multi-tenancy.md) - Tenant isolation

---

**Last Updated:** May 1, 2026  
**Endpoints:** 9 ✅
