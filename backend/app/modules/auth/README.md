# Authentication Module

Complete authentication system with JWT tokens, 2FA, and session management.

## Features

- ✅ User registration with doctor/tenant creation
- ✅ Login with JWT access + refresh tokens
- ✅ Token refresh with rotation
- ✅ 2FA (TOTP) setup and verification
- ✅ Password change
- ✅ Session management and logout
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenant isolation
- 🚧 Email verification (TODO)
- 🚧 Password reset via email (TODO)

## API Endpoints

### Registration

**POST** `/api/v1/auth/register`

Register a new doctor account. Creates both a User and Tenant.

```json
{
  "email": "doctor@example.com",
  "password": "SecurePass123",
  "full_name": "Dr. John Doe",
  "phone": "+8801712345678",
  "language": "en",
  "clinic_name": "Healing Clinic",
  "clinic_address": "123 Main St, Dhaka",
  "division_id": 1,
  "district_id": 1,
  "upazila_id": 1,
  "specializations": ["homeopathy", "ayurveda"],
  "license_number": "BMDC-12345"
}
```

**Response** (201 Created):
```json
{
  "message": "Registration successful. Your account is pending admin approval.",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "email": "doctor@example.com",
  "requires_approval": true
}
```

**Notes:**
- Password must be at least 8 characters with letters and numbers
- Specializations: 1-4 from `["homeopathy", "ayurveda", "unani", "herbal"]`
- Account requires admin approval before login is allowed

---

### Login

**POST** `/api/v1/auth/login`

Authenticate user and receive JWT tokens.

```json
{
  "email": "doctor@example.com",
  "password": "SecurePass123",
  "totp_code": "123456"  // Optional, required if 2FA enabled
}
```

**Response** (200 OK):
```json
{
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "user": {
    "id": "uuid",
    "tenant_id": "uuid",
    "email": "doctor@example.com",
    "full_name": "Dr. John Doe",
    "phone": "+8801712345678",
    "role": "doctor",
    "language": "en",
    "is_active": true,
    "is_email_verified": false,
    "is_2fa_enabled": false,
    "last_login_at": "2026-04-22T10:00:00Z"
  },
  "requires_2fa": false
}
```

**Errors:**
- 401: Invalid credentials
- 403: Account not approved or deactivated

---

### Refresh Token

**POST** `/api/v1/auth/refresh`

Get new access token using refresh token. Implements token rotation.

```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // New refresh token
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Notes:**
- Old refresh token is invalidated (token rotation)
- Session is updated with new refresh token

---

### Logout

**POST** `/api/v1/auth/logout`

Logout user by revoking session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body (optional):**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // Optional: revoke specific session
}
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

**Notes:**
- If no refresh_token provided, all sessions are revoked
- If refresh_token provided, only that session is revoked

---

### Get Profile

**GET** `/api/v1/auth/me`

Get current user profile with tenant information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "user": {
    "id": "uuid",
    "tenant_id": "uuid",
    "email": "doctor@example.com",
    "full_name": "Dr. John Doe",
    "role": "doctor",
    "language": "en",
    "is_active": true,
    "is_2fa_enabled": false
  },
  "tenant": {
    "id": "uuid",
    "name": "Dr. John Doe",
    "email": "doctor@example.com",
    "clinic_name": "Healing Clinic",
    "specializations": ["homeopathy", "ayurveda"],
    "plan": "free",
    "is_verified": true,
    "is_approved": true,
    "is_active": true
  }
}
```

---

## 2FA (Two-Factor Authentication)

### Setup 2FA

**POST** `/api/v1/auth/2fa/setup`

Generate TOTP secret and QR code URI.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_uri": "otpauth://totp/AltCare:doctor@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AltCare",
  "backup_codes": null
}
```

**Notes:**
- Use `qr_code_uri` to generate QR code for authenticator apps
- 2FA is NOT enabled yet - requires verification

---

### Verify and Enable 2FA

**POST** `/api/v1/auth/2fa/verify`

Verify TOTP code and enable 2FA.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "totp_code": "123456"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "2FA enabled successfully"
}
```

**Notes:**
- 2FA is now enabled for the account
- Future logins will require TOTP code

---

### Disable 2FA

**POST** `/api/v1/auth/2fa/disable`

Disable 2FA after verification.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "password": "SecurePass123",
  "totp_code": "123456"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "2FA disabled successfully"
}
```

---

## Password Management

### Change Password

**POST** `/api/v1/auth/password/change`

Change password for authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## Testing the Endpoints

### 1. Register a Doctor

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "SecurePass123",
    "full_name": "Dr. John Doe",
    "language": "en",
    "specializations": ["homeopathy"]
  }'
```

### 2. Login (after admin approval)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "SecurePass123"
  }'
```

### 3. Get Profile

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 4. Setup 2FA

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/setup \
  -H "Authorization: Bearer <access_token>"
```

### 5. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

## Security Features

### JWT Tokens

- **Access Token:** Short-lived (30 minutes), contains user claims
- **Refresh Token:** Long-lived (7 days), used to get new access tokens
- **Token Rotation:** Refresh tokens are rotated on each refresh
- **Session Tracking:** All refresh tokens stored with IP and user agent

### Password Security

- **Bcrypt Hashing:** Passwords hashed with bcrypt (cost factor 12)
- **Strength Validation:** Minimum 8 characters, letters + numbers required
- **No Plain Text:** Passwords never stored or logged in plain text

### 2FA Security

- **TOTP Algorithm:** Time-based One-Time Password (RFC 6238)
- **6-Digit Codes:** Standard authenticator app codes
- **1-Step Tolerance:** Allows ±30 seconds clock drift

### Multi-Tenant Isolation

- **Row-Level Security:** Tenant context injected into queries
- **Automatic Filtering:** All queries filtered by tenant_id
- **No Cross-Tenant Access:** Users can only access their own tenant data

---

## Role-Based Access Control

### Roles

- **admin** - Platform administrator (no tenant_id)
- **operator** - Platform operator (no tenant_id)
- **doctor** - Clinic doctor (tenant-scoped)
- **receptionist** - Clinic staff (tenant-scoped)

### Usage

```python
from app.core.dependencies import RequireDoctor, RequireAdmin

@router.post("/prescriptions")
async def create_prescription(
    user: RequireDoctor,  # Only doctors can access
    db: AsyncSession = Depends(get_db)
):
    ...
```

---

## Next Steps

- [ ] Implement email verification flow
- [ ] Implement password reset via email
- [ ] Add rate limiting to login endpoint (5/min)
- [ ] Add account lockout after failed attempts
- [ ] Add backup codes for 2FA
- [ ] Add session management UI (view/revoke sessions)

---

## Database Models

### User Table
- id, tenant_id, email, password_hash
- role, full_name, phone, avatar_url
- is_2fa_enabled, totp_secret
- language, is_active, is_email_verified
- last_login_at

### Tenant Table
- id, name, email, phone
- clinic_name, clinic_address
- division_id, district_id, upazila_id
- specializations (array)
- license_number, is_verified, is_approved
- plan, is_active

### UserSession Table
- id, user_id
- refresh_token_hash
- ip_address, user_agent
- expires_at, last_activity_at
- is_revoked, revoked_at
