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

Uses `{ email, password, totp_code? }`.

### Refresh Token
`POST /api/v1/auth/refresh`

Uses refresh token and rotates session token.

### Logout
`POST /api/v1/auth/logout`

Revokes one or all refresh sessions for current user.

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

## Password Endpoint

### Change Password
`POST /api/v1/auth/password/change`

Revokes all active refresh sessions after password change.

## Notes

- There is no separate `/login-2fa` endpoint; 2FA code is part of `/login`.
- Source of truth: `backend/app/modules/auth/routes.py` and `backend/app/modules/auth/service.py`.
