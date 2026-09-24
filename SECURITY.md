# 🔒 Security Guide - AltCare Platform

This document outlines the security features, configurations, and best practices for deploying AltCare securely.

---

## ⚠️ **Critical Security Checklist**

Before deploying to production, ensure ALL items are completed:

### Required Environment Variables

- [ ] `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] `INTEGRATION_ENCRYPTION_KEY` - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [ ] `DATABASE_URL` - Use strong password, never default
- [ ] `MINIO_ROOT_USER` - Change from default `minioadmin`
- [ ] `MINIO_ROOT_PASSWORD` - Use strong random password (min 32 chars)

### Security Configuration

- [ ] Set `ENVIRONMENT=production` in backend/.env
- [ ] Update `CORS_ORIGINS` to match your production domain (remove localhost)
- [ ] Enable HSTS headers (`SECURITY_HSTS_ENABLED=True`)
- [ ] Review and adjust CSP policy if needed
- [ ] Configure rate limiting appropriately:
  - `RATE_LIMIT_LOGIN_PER_MINUTE=5` (recommended)
  - `RATE_LIMIT_PER_MINUTE=60` (general API)
  - `RATE_LIMIT_AI_PER_HOUR=20` (AI features)

### Infrastructure

- [ ] Use SSL/TLS certificates (Let's Encrypt recommended)
- [ ] Enable database encryption at rest
- [ ] Configure Redis with password authentication
- [ ] Set up firewall rules (allow only necessary ports)
- [ ] Enable audit logging for database
- [ ] Configure backup retention policy

---

## 🛡️ **Security Features**

### 1. **Authentication & Authorization**

**JWT Tokens:**
- Access tokens: 30-minute expiry
- Refresh tokens: 7-day expiry
- Token validation on every request
- Type checking (`access` vs `refresh`)

**Password Security:**
- Bcrypt hashing (12 rounds)
- Complexity requirements:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
- Password change invalidates sessions

**Two-Factor Authentication (2FA):**
- TOTP-based (compatible with Google Authenticator, Authy)
- QR code generation for easy setup
- Required verification on login if enabled

### 2. **Multi-Tenant Isolation**

**Row-Level Security:**
- Every tenant-scoped table has `tenant_id`
- Explicit per-query filtering: the JWT's `tenant_id` is passed into each service, and `BaseTenantService`'s shared query helpers add the `tenant_id` filter — **not** an automatic session-level filter. A `tenant_id_ctx` ContextVar is set from the JWT but nothing reads it; a hand-written query that skips `BaseTenantService` is a tenant-isolation bug the type system won't catch. See `CLAUDE.md` §4.1.
- Platform users (admin, operator): `tenant_id = NULL`
- Tenant users (doctor, receptionist): scoped to their tenant
- Isolation-suite results are part of the whole-suite count in `docs/planning/revision-2026-09.md` Stage 0 (`pytest -q`: 432 passed / 2 xfailed / 0 failed) — the historical "16/16 passing" figure was never sourced to a specific run and shouldn't be quoted

**Testing:**
```bash
pytest tests/integration/test_mvp_tenant_isolation.py -v
```

### 3. **Rate Limiting**

**Circuit Breaker Pattern:**
- Primary: Redis-backed atomic counters
- Fallback: In-memory rate limiting (process-local)
- **Security:** Fails safe, not open (prevents abuse if Redis crashes)

**Rate Limits (per IP or user):**
- Login endpoint: 5 requests/minute (configurable)
- General API: 60 requests/minute
- AI queries: 20 requests/hour (plan-gated)

**Headers returned:**
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `Retry-After` (on 429 Too Many Requests)

### 4. **HTTP Security Headers**

Automatically applied to all responses:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: [configurable]
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**CSP Policy (balanced):**
- Allows Next.js, API calls, and necessary resources
- Prevents XSS via inline script restrictions
- Blocks clickjacking via `frame-ancestors 'none'`

### 5. **Data Encryption**

**At Rest:**
- Integration credentials: Fernet encryption (AES-128-CBC)
- Passwords: Bcrypt (12 rounds)
- Database: Recommend enabling PostgreSQL encryption

**In Transit:**
- HTTPS/TLS required in production
- HSTS enabled (forces HTTPS)
- Secure cookies (httpOnly, secure, sameSite)

### 6. **Soft Deletes (Clinical Data Protection)**

All clinical data uses soft deletes:
- Patient records
- Prescriptions
- Payments
- Medical notes

**Never hard delete** - set `deleted_at` timestamp instead. Allows:
- Audit trails
- Recovery from accidental deletion
- Compliance with medical record retention laws

---

## 🚨 **Security Fixes Applied (2026-05-30)**

### Critical Issues Fixed

1. **Hardcoded Credentials Removed**
   - Moved dev credentials to environment variable
   - Only loaded in development mode
   - Production builds contain no credentials

2. **Rate Limiting Fail-Safe**
   - Added circuit breaker pattern
   - In-memory fallback when Redis unavailable
   - Prevents unlimited requests on Redis failure

3. **CSP Policy Fixed**
   - Changed from `default-src 'none'` (broken)
   - To balanced policy allowing Next.js + API
   - Still prevents XSS and clickjacking

4. **Environment Variable Validation**
   - Startup validation for required secrets
   - Fails fast with clear error messages
   - Warns about weak/default credentials

5. **Docker Security**
   - Added environment variable overrides
   - Security warnings for default credentials
   - Required secrets enforcement

6. **Frontend Error Boundaries**
   - Added error.tsx for graceful error handling
   - Prevents blank screens on crashes
   - Dev-only error details

---

## 🔐 **Deployment Checklist**

### Pre-Deployment

```bash
# 1. Generate strong secrets
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export INTEGRATION_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export MINIO_ROOT_USER=$(openssl rand -base64 16)
export MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)

# 2. Update .env files (NEVER commit to git!)
echo "SECRET_KEY=$SECRET_KEY" >> backend/.env
echo "INTEGRATION_ENCRYPTION_KEY=$INTEGRATION_ENCRYPTION_KEY" >> backend/.env
echo "MINIO_ROOT_USER=$MINIO_ROOT_USER" >> backend/.env
echo "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" >> backend/.env

# 3. Set environment to production
echo "ENVIRONMENT=production" >> backend/.env

# 4. Update CORS origins
echo "CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com" >> backend/.env

# 5. Test configuration validation
cd backend && python -c "from app.core.config import settings; print('✅ Config valid')"
```

### Post-Deployment

1. **Run security tests:**
   ```bash
   pytest tests/integration/test_auth_security.py -v
   pytest tests/integration/test_mvp_tenant_isolation.py -v
   pytest tests/integration/test_rate_limiting.py -v
   ```

2. **Verify security headers:**
   ```bash
   curl -I https://yourdomain.com/api/v1/health
   ```

3. **Test rate limiting:**
   ```bash
   # Should return 429 after 5 attempts
   for i in {1..6}; do
     curl -X POST https://yourdomain.com/api/v1/auth/login \
       -H "Content-Type: application/json" \
       -d '{"email":"test@test.com","password":"wrong"}'
   done
   ```

4. **Monitor logs for security events:**
   - Failed login attempts
   - Rate limit violations
   - JWT validation failures
   - Redis circuit breaker activations

---

## 📊 **Security Monitoring**

### Key Metrics to Track

1. **Authentication:**
   - Failed login attempts (high = possible attack)
   - 2FA bypass attempts
   - Password reset requests

2. **Rate Limiting:**
   - 429 responses (rate limit hits)
   - Redis failures (circuit breaker activations)
   - Top rate-limited IPs/users

3. **Authorization:**
   - Tenant isolation violations (should be zero)
   - Invalid JWT tokens
   - Role elevation attempts

4. **Data Access:**
   - Unusual query patterns
   - Bulk data exports
   - Soft delete recoveries

### Recommended Tools

- **Application:** Sentry (error tracking)
- **Infrastructure:** Datadog, Prometheus + Grafana
- **Database:** pgAudit for PostgreSQL
- **Security:** OWASP ZAP, Burp Suite (pen testing)

---

## 🐛 **Reporting Security Issues**

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, email: **sadman.sobhan@americatechinc.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We aim to respond within 48 hours.

---

## 📚 **Security Best Practices**

### For Developers

1. **Never commit secrets to git**
   - Use `.env` files (gitignored)
   - Use environment variables in CI/CD
   - Rotate secrets regularly

2. **Validate all inputs**
   - Use Pydantic schemas (backend)
   - Use Zod schemas (frontend)
   - Never trust user input

3. **Follow least privilege principle**
   - Users only get necessary permissions
   - Roles: admin, operator, doctor, receptionist
   - Plan-based feature gating

4. **Test security features**
   - Write tests for auth flows
   - Test tenant isolation thoroughly
   - Verify rate limiting works

5. **Keep dependencies updated**
   ```bash
   # Backend
   pip list --outdated
   pip install --upgrade <package>

   # Frontend
   npm outdated
   npm update
   ```

### For Operators

1. **Regular backups**
   - Database: Daily automated backups
   - MinIO: Versioning enabled
   - Retention: 30 days minimum

2. **Access control**
   - Limit database access to backend only
   - Use VPN/firewall for admin access
   - Review user permissions quarterly

3. **Incident response plan**
   - Document breach response procedures
   - Test backup restoration
   - Have rollback plan ready

4. **Compliance**
   - HIPAA/medical data regulations
   - GDPR (if EU users)
   - Local data protection laws

---

## 🔄 **Security Update Log**

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-30 | 1.0.1 | Initial security hardening (rate limiting, CSP, validation) |
| 2026-05-22 | 1.0.0 | MVP launch (authentication, 2FA, tenant isolation) |

---

**Last Updated:** 2026-05-30  
**Security Contact:** sadman.sobhan@americatechinc.com
