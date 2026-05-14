---
title: "Authentication & Security"
type: "architecture"
version: "0.9.0"
last_updated: "2026-05-01"
ai_summary: "JWT authentication with optional TOTP 2FA, bcrypt password hashing, and role-based access control"
---

# Authentication & Security

JWT-based authentication with 2FA support and comprehensive security measures.

---

## 📋 Table of Contents

- [Overview](#overview)
- [JWT Implementation](#jwt-implementation)
- [2FA (TOTP)](#2fa-totp)
- [Password Security](#password-security)
- [Authorization](#authorization)
- [Security Best Practices](#security-best-practices)

---

## 🌐 Overview

**Authentication Method:** JWT (JSON Web Tokens)  
**2FA:** TOTP (Time-based One-Time Password)  
**Password Hashing:** bcrypt (12 rounds)  
**Session Management:** Refresh token rotation  
**Authorization:** Role-based access control (RBAC)

**Security Layers:**
1. Password hashing (bcrypt)
2. JWT token signing (HS256)
3. Token expiration (30 min access, 7 day refresh)
4. Optional 2FA (TOTP)
5. Integration credential encryption (Fernet)

---

## 🔑 JWT Implementation

### Token Structure

**Access Token:**
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "doctor",
  "email": "doctor@clinic.com",
  "plan": "pro",
  "exp": 1234567890,
  "type": "access"
}
```

**Refresh Token:**
```json
{
  "sub": "user-uuid",
  "jti": "session-uuid",
  "exp": 1235194290,
  "type": "refresh"
}
```

**Claims:**
- `sub`: User ID (subject)
- `tenant_id`: Tenant ID (null for platform users)
- `role`: User role (admin, operator, doctor, receptionist)
- `email`: User email
- `plan`: Subscription plan (for feature gating)
- `exp`: Expiration timestamp
- `type`: Token type (access or refresh)
- `jti`: JWT ID (for refresh token tracking)

---

### Token Lifetimes

| Token Type | Lifetime | Purpose | Renewal |
|------------|----------|---------|---------|
| **Access** | 30 minutes | API authentication | Via refresh token |
| **Refresh** | 7 days | Get new access token | Re-login required |

**Why short access tokens?**
- Limits damage if token stolen
- Forces periodic re-validation
- Allows faster permission revocation

**Why long refresh tokens?**
- Better UX (don't force login every 30 min)
- Stored securely (httpOnly cookies recommended)
- Can be revoked server-side

---

### Token Generation

**Implementation:** `app/core/security.py`

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # From env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role,
        "email": user.email,
        "plan": user.tenant.plan if user.tenant else None,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user: User, jti: str) -> str:
    payload = {
        "sub": str(user.id),
        "jti": jti,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

---

### Token Validation

```python
from jose import jwt, JWTError

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload
```

---

## 🔐 2FA (TOTP)

### Setup Flow

```
1. User enables 2FA
   POST /auth/2fa/enable
   ↓
2. Generate TOTP secret
   secret = pyotp.random_base32()
   ↓
3. Generate QR code
   uri = pyotp.totp.TOTP(secret).provisioning_uri(
       name=user.email,
       issuer_name="AltCare"
   )
   qr_code = generate_qr_code(uri)
   ↓
4. Return secret + QR code + backup codes
   {
       "secret": "JBSWY3DPEHPK3PXP",
       "qr_code": "data:image/png;base64,...",
       "backup_codes": ["ABC123", "DEF456", ...]
   }
   ↓
5. User scans QR code in authenticator app
   ↓
6. User verifies with TOTP code
   POST /auth/2fa/verify → {totp_code: "123456"}
   ↓
7. If valid, set user.two_factor_enabled = true
```

---

### Login Flow with 2FA

```
1. User submits email + password
   POST /auth/login → {email, password}
   ↓
2. Verify password
   ↓
3. Check if user.two_factor_enabled
   ↓
4a. If 2FA disabled:
    → Generate JWT tokens
    → Return tokens + user info
    
4b. If 2FA enabled:
    → Frontend retries login with TOTP code in same endpoint
    ↓
5. User submits email + password + TOTP code
   POST /auth/login → {email, password, totp_code}
   ↓
6. Verify password + TOTP code
   ↓
7. Generate JWT tokens
   ↓
8. Return tokens + user info
```

---

### TOTP Verification

```python
import pyotp

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow ±30 seconds
```

**Library:** `pyotp` (Python implementation of RFC 6238)

**Parameters:**
- Secret: Base32 encoded string
- Code: 6-digit code from authenticator app
- Valid window: Allow 1 time step before/after (30 sec each)

---

## 🔒 Password Security

### Hashing Algorithm

**Method:** bcrypt  
**Rounds:** 12  
**Library:** `passlib`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Why bcrypt?**
- Adaptive (can increase rounds over time)
- Salted automatically
- Slow by design (prevents brute force)
- Industry standard

---

### Password Requirements

**Current (Development):**
- Minimum 6 characters

**Production (Recommended):**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

**Implementation:**
```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain number')
        return v
```

---

## 🛡️ Authorization

### Role-Based Access Control (RBAC)

**Roles:**
- `admin`: Platform administrator (tenant_id = NULL)
- `operator`: Platform operator (tenant_id = NULL)
- `doctor`: Clinic doctor (tenant_id = UUID)
- `receptionist`: Clinic receptionist (tenant_id = UUID)

---

### Permission Checks

**Method 1: Dependency Injection**
```python
from app.core.dependencies import RequireDoctor, RequireAdmin, require_role

@router.post("/prescriptions")
async def create_prescription(
    user: RequireDoctor  # Only doctors can access
):
    ...

@router.delete("/users/{id}")
async def delete_user(
    user: RequireAdmin  # Only admins can access
):
    ...

@router.get("/analytics")
async def analytics(
    user: CurrentUser = Depends(require_role("doctor", "admin"))
):
    ...
```

---

**Method 2: Manual Check**
```python
@router.get("/sensitive")
async def sensitive_data(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    ...
```

---

### Plan-Based Gating

**Check subscription plan:**
```python
from app.core.dependencies import require_plan, RequireProPlan

@router.post("/ai/query")
async def ai_query(
    user: RequireProPlan  # Only 'pro' plan users
):
    ...

@router.post("/integrations")
async def add_integration(
    user: CurrentUser = Depends(require_plan("pro", "enterprise"))
):
    ...
```

**Implementation:**
```python
def require_plan(*allowed_plans: str):
    async def plan_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ):
        if current_user.plan not in allowed_plans:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {' or '.join(allowed_plans)} plan"
            )
        return current_user
    return plan_checker
```

---

## 🔐 Security Best Practices

### 1. Token Storage (Frontend)

**✅ DO:**
- Store in httpOnly cookies
- Use secure flag (HTTPS only)
- Set SameSite=Strict

**❌ DON'T:**
- Store in localStorage (XSS vulnerable)
- Store in sessionStorage (XSS vulnerable)
- Expose tokens in URL

---

### 2. Token Transmission

**✅ DO:**
```http
GET /api/patients
Authorization: Bearer eyJhbGc...
```

**❌ DON'T:**
```http
GET /api/patients?token=eyJhbGc...
```

---

### 3. Password Handling

**✅ DO:**
- Hash before storing
- Use bcrypt with 12+ rounds
- Never log passwords
- Enforce minimum length

**❌ DON'T:**
- Store plaintext
- Log password in error messages
- Send password in response
- Reuse passwords across systems

---

### 4. Integration Credentials

**Encryption:** Fernet (symmetric encryption)

```python
from cryptography.fernet import Fernet

# Generate key (do once, store in env)
key = Fernet.generate_key()

# Encrypt credentials
f = Fernet(key)
encrypted = f.encrypt(credentials.encode())

# Decrypt credentials
decrypted = f.decrypt(encrypted).decode()
```

**Store encrypted in database:**
```sql
CREATE TABLE tenant_integrations (
    credentials JSONB NOT NULL  -- Encrypted with Fernet
);
```

---

### 5. Rate Limiting

**Planned (Phase 2):**
- 5 failed login attempts → 15-minute lockout
- 100 requests/minute per user
- DDoS protection via CDN

---

### 6. HTTPS Only

**Production:**
- Force HTTPS
- HSTS header
- Secure cookies
- CSP headers

---

## 🤖 AI Quick Reference

**Q: How long do tokens last?**
→ Access: 30 minutes, Refresh: 7 days

**Q: How is 2FA implemented?**
→ TOTP (RFC 6238) with pyotp, 6-digit codes, 30-second window

**Q: What hashing algorithm for passwords?**
→ bcrypt with 12 rounds

**Q: How are JWT tokens signed?**
→ HS256 algorithm with secret key from env

**Q: Where should tokens be stored?**
→ httpOnly cookies (NOT localStorage)

**Q: How do I check user role?**
→ Use RequireDoctor, RequireAdmin dependencies or check current_user.role

**Q: How are integration credentials stored?**
→ Encrypted with Fernet before storing in JSONB field

---

**See Also:**
- [Authentication API](../api/authentication.md) - Login, 2FA, refresh endpoints
- [Multi-Tenancy](multi-tenancy.md) - Tenant isolation via JWT
- [API Reference](../api/README.md) - Protected endpoints

---

**Last Updated:** May 1, 2026  
**Security:** JWT + 2FA + bcrypt ✅
