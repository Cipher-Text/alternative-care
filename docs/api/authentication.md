---
title: "Authentication API"
type: "api-reference"
module: "authentication"
version: "0.9.0"
last_updated: "2026-07-12"
ai_summary: "14 endpoints for auth, self-registration, legacy admin compatibility, JWT session lifecycle, and 2FA"
endpoints: 14
authentication: "public + protected"
---

# Authentication API

**Module:** Authentication
**Endpoints:** 14
**Base Path:** `/api/v1/auth`

## Overview

Authentication and onboarding endpoints for:
- Public doctor registration
- Admin client provisioning (tenant + primary doctor)
- Admin tenant approval workflow
- JWT login/refresh/logout
- 2FA setup/verify/disable
- Password change
- Current user profile

## Legacy Admin Compatibility Endpoints

Canonical platform-admin endpoints live under `/api/v1/admin`. The `/api/v1/auth/admin/*` endpoints remain for backwards compatibility.

### List Clients
`GET /api/v1/auth/admin/clients`

Auth: Admin only

Returns all tenant clients with primary doctor summary, doctor count, approval status, and plan.

### Get Client Detail
`GET /api/v1/auth/admin/clients/{tenant_id}`

Auth: Admin only

Returns one tenant/clinic with all attached doctor users and lifecycle metadata.

### Provision Client Account
`POST /api/v1/auth/admin/provision-client`

Auth: Admin only

Creates tenant (clinic) and primary doctor in one request.

### List Pending Tenants
`GET /api/v1/auth/admin/tenants/pending`

Auth: Admin only

Returns tenants with `is_approved = false`.

### Approve Tenant
`POST /api/v1/auth/admin/tenants/{tenant_id}/approve`

Auth: Admin only

Sets tenant approval fields and enables tenant users to log in.

## Public Registration

### Register Doctor
`POST /api/v1/auth/register`

Creates doctor + tenant. New tenant is pending approval by default.

## Session/Auth Endpoints

### Login
`POST /api/v1/auth/login`

Uses `{ email, password, totp_code? }`. If the account has 2FA enabled and
`totp_code` is omitted, returns `200` with `{ requires_2fa: true }` and
`tokens`/`user` omitted (not just falsy) — resubmit to `/auth/login-2fa`
with the code to complete login.

### Complete 2FA Login
`POST /api/v1/auth/login-2fa`

Same request/response shape as `/login`; call this on the second step of a
2FA login, once you have `totp_code`.

### Refresh Token
`POST /api/v1/auth/refresh`

Uses refresh token and rotates session token.

### Logout
`POST /api/v1/auth/logout`

Body: `{ refresh_token? }` (JSON, optional — matches every other endpoint's convention). Omit the body (or `refresh_token`) to revoke **all** sessions for the current user; pass a specific `refresh_token` to revoke only that one session. Until 2026-09-23 this parameter was bound as a query string parameter instead of the request body, so every caller sending it as JSON (the only convention used elsewhere in this API) silently revoked all sessions instead of one — fixed, see `docs/planning/revision-2026-09.md` Stage 0.

### Current User Profile
`GET /api/v1/auth/me`

Returns authenticated user and tenant profile summary.

## 2FA Endpoints

### Setup 2FA
`POST /api/v1/auth/2fa/setup`

### Verify and Enable 2FA
`POST /api/v1/auth/2fa/verify`

### Disable 2FA
`POST /api/v1/auth/2fa/disable`

## Password Endpoints

### Change Password
`POST /api/v1/auth/password/change`

Revokes all active refresh sessions after password change.

### Forgot Password
`POST /api/v1/auth/password/forgot`

Body: `{ email }`. Always returns the same generic `{ message }` whether or
not the email is registered — this is the enumeration protection, don't
branch UI on the response. If the account exists, queues a reset email
(`app/core/system_email.py`) with a link valid for 1 hour.

### Reset Password
`POST /api/v1/auth/password/reset`

Body: `{ token, new_password }`. `token` is the raw value from the emailed
link (stored server-side only as a SHA-256 hash, and single-use — consumed
on success). Revokes every existing session, same as Change Password.

## Email Verification Endpoints

### Verify Email
`POST /api/v1/auth/email/verify`

Body: `{ token }`. Token from the verification email sent at registration,
valid for 24 hours, single-use.

### Resend Verification Email
`POST /api/v1/auth/email/resend`

Body: `{ email }`. Same enumeration-resistant posture as Forgot Password —
identical generic response whether the account exists, is already
verified, or neither.

## Notes

- Source of truth: `backend/app/modules/auth/routes.py` and `backend/app/modules/auth/service.py`.
