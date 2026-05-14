---
title: "Authentication API"
type: "api-reference"
module: "authentication"
version: "0.9.0"
last_updated: "2026-05-14"
ai_summary: "16 endpoints for auth, self-registration, admin client provisioning, tenant approval, JWT session lifecycle, and 2FA"
endpoints: 16
authentication: "public + protected"
---

# Authentication API

**Module:** Authentication  
**Endpoints:** 16  
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

## Admin Endpoints

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
