# Authentication System - Setup Guide

## ✅ What's Been Implemented

The complete authentication system has been implemented with the following components:

### 1. **Pydantic Schemas** (`app/modules/auth/schemas.py`)
   - Registration, Login, Token, 2FA, Password management
   - Request/Response models with validation
   - Comprehensive error handling

### 2. **Service Layer** (`app/modules/auth/service.py`)
   - `AuthService` class with all business logic:
     - ✅ Doctor registration with tenant creation
     - ✅ Login with JWT (access + refresh tokens)
     - ✅ Token refresh with rotation
     - ✅ Session management and logout
     - ✅ 2FA setup, verify, and disable
     - ✅ Password change
     - ✅ User profile retrieval

### 3. **API Routes** (`app/modules/auth/routes.py`)
   - All authentication endpoints:
     - `POST /api/v1/auth/register` - Doctor registration
     - `POST /api/v1/auth/login` - Login
     - `POST /api/v1/auth/logout` - Logout
     - `POST /api/v1/auth/refresh` - Refresh tokens
     - `POST /api/v1/auth/2fa/setup` - Setup 2FA
     - `POST /api/v1/auth/2fa/verify` - Verify 2FA
     - `POST /api/v1/auth/2fa/disable` - Disable 2FA
     - `POST /api/v1/auth/password/change` - Change password
     - `GET /api/v1/auth/me` - Get profile

### 4. **Integration** (`app/main.py`)
   - Auth router registered with FastAPI app
   - Available at `/api/v1/auth/*` endpoints

### 5. **Documentation** (`app/modules/auth/README.md`)
   - Complete API documentation
   - cURL examples for all endpoints
   - Security features explained
   - RBAC usage guide

---

## 🚀 Next Steps to Run the System

### Step 1: Ensure Database is Running

Make sure PostgreSQL is running (via Docker or locally):

```bash
# If using Docker Compose (from project root)
docker-compose up -d postgres

# Or check if it's running
docker ps | grep postgres
```

### Step 2: Install Dependencies (if not done)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements.txt
```

### Step 3: Create Initial Database Migration

```bash
# From backend directory, with venv activated
cd backend
source venv/bin/activate

# Generate migration
alembic revision --autogenerate -m "Initial migration - all models"

# Apply migration
alembic upgrade head
```

**Alternative (if alembic command not found):**
```bash
python3 -m pip install alembic
# Then try again
```

### Step 4: Create a Platform Admin User (Optional)

Create a seed script or use the API to create the first admin:

```bash
# Create backend/create_admin.py
python3 create_admin.py
```

Example `create_admin.py`:
```python
import asyncio
from app.core.database import get_db_context
from app.shared.models.tenant import User
from app.core.security import get_password_hash
import uuid

async def create_admin():
    async with get_db_context() as db:
        admin = User(
            id=str(uuid.uuid4()),
            tenant_id=None,  # Platform admin
            email="admin@altcare.health",
            password_hash=get_password_hash("AdminPass123"),
            role="admin",
            full_name="Platform Admin",
            language="en",
            is_active=True,
            is_email_verified=True,
        )
        db.add(admin)
        await db.commit()
        print("✅ Admin user created!")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

### Step 5: Start the Server

```bash
# From backend directory
cd backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the quick start script:
```bash
./quick_start.sh
```

### Step 6: Test the API

Visit the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🧪 Testing the Authentication Flow

### 1. Register a Doctor

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "SecurePass123",
    "full_name": "Dr. John Doe",
    "language": "en",
    "specializations": ["homeopathy"],
    "clinic_name": "Healing Clinic"
  }'
```

**Response:**
```json
{
  "message": "Registration successful. Your account is pending admin approval.",
  "user_id": "...",
  "tenant_id": "...",
  "email": "doctor@example.com",
  "requires_approval": true
}
```

### 2. Approve the Doctor (as Admin)

You'll need to manually update the database or create an admin approval endpoint:

```sql
-- Connect to PostgreSQL
UPDATE tenants SET is_approved = true WHERE email = 'doctor@example.com';
```

### 3. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "tokens": {
    "access_token": "eyJ0eXAi...",
    "refresh_token": "eyJ0eXAi...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "user": {
    "id": "...",
    "email": "doctor@example.com",
    "full_name": "Dr. John Doe",
    "role": "doctor",
    ...
  },
  "requires_2fa": false
}
```

### 4. Get Profile (with token)

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Setup 2FA

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/setup \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Change Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/password/change \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123",
    "new_password": "NewSecurePass456"
  }'
```

### 7. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📋 Checklist

- [x] Authentication schemas created
- [x] Authentication service implemented
- [x] API routes defined
- [x] Router registered in main app
- [x] Documentation written
- [ ] Database migration generated
- [ ] Database migration applied
- [ ] Server started
- [ ] Endpoints tested
- [ ] Admin approval workflow tested
- [ ] 2FA flow tested

---

## 🔒 Security Features Implemented

1. **Password Hashing:** Bcrypt with strong cost factor
2. **JWT Tokens:** Access (30min) + Refresh (7 days) tokens
3. **Token Rotation:** Refresh tokens rotated on each refresh
4. **Session Tracking:** IP address and user agent logged
5. **2FA Support:** TOTP (Time-based One-Time Password)
6. **Multi-Tenant Isolation:** Row-level security with tenant context
7. **Role-Based Access Control:** Admin, Doctor, Receptionist roles
8. **Account Approval:** Doctors require admin approval before login

---

## 📝 TODO: Email-Related Features

These features require email service integration (SendGrid/AWS SES):

- [ ] Email verification on registration
- [ ] Resend verification email
- [ ] Password reset via email
- [ ] Welcome email on approval
- [ ] 2FA backup codes via email

---

## 🐛 Common Issues

### "alembic: command not found"
```bash
pip install alembic
# or
python3 -m pip install alembic
```

### "Could not connect to database"
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env` file
- Test connection: `psql $DATABASE_URL`

### "Module not found" errors
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Activate virtual environment: `source venv/bin/activate`

---

## 📚 Next Module to Implement

After authentication is tested and working, the next module should be:

**Week 5-6: Doctor Credentials & Profile**
- Doctor degrees CRUD endpoints
- Doctor trainings/certifications CRUD
- Degree verification workflow (admin)
- Profile page with tabs

See `docs/planning/roadmap-detailed.md` for full roadmap.

---

**Author:** AltCare Development Team  
**Date:** April 22, 2026  
**Status:** ✅ Implementation Complete - Ready for Testing
