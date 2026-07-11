---
title: "AltCare Documentation Index"
type: "navigation"
last_updated: "2026-07-12"
ai_purpose: "Fast navigation map for AI assistants"
version: "1.1.0"
---

# AltCare Documentation Index (Code-Aligned)

Purpose: quick navigation for developers and AI assistants using only currently existing docs.

## Quick Start

1. `../README.md` - project overview and current scope
2. `../GETTING_STARTED.md` - local setup and run commands
3. `api/README.md` - API module map
4. `status/current.md` - current implementation status

## By Area

### Setup
- `setup/backend.md`
- `setup/frontend.md`

### API
- `api/README.md`
- `api/authentication.md`
- `api/patients.md`
- `api/doctor.md`
- `api/appointments.md`
- `api/prescriptions.md`
- `api/payments.md`
- `api/dashboard.md`
- `api/integrations.md`

### Architecture
- `architecture/README.md`
- `architecture/roles-access.md` — **Roles, RBAC guards, platform vs tenant access** *(updated 2026-07-11)*
- `architecture/database.md`
- `architecture/database-schema.md`
- `architecture/authentication.md`
- `architecture/multi-tenancy.md`
- `architecture/tech-stack.md`

### Development
- `development/quick-reference.md`
- `development/i18n.md`
- `development/theme-system.md`

### Planning and Status
- `ROADMAP.md` — product roadmap with Platform Admin Phase A/B added
- `status/current.md` — current implementation status *(updated 2026-07-11)*
- `planning/admin-module.md` — **Platform Admin Phase A spec** *(new 2026-07-11)*
- `planning/role-distribution.md` — **Role distribution & user management spec** *(new 2026-07-11)*
- `testing/TEST_STRATEGY.md`
- `planning/roadmap-detailed.md`

## Code-Verified Snapshot (2026-07-11)

- Backend routers registered in `backend/app/main.py`: `admin`, `auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`, `medicine`, `symptom`, `tenant`, `geographic`
- API endpoints: 127 module endpoints
- Database table models: 34 (plus 3 base classes)
- System endpoints: `/`, `/health`, `/metrics`
- Frontend stack: Next.js 16 + React 19
- Frontend implemented pages: login, dashboard, patients, appointments, prescriptions, profile, payments, medicines, symptoms, settings/integrations, admin/clients, admin/dashboard, admin/users
- Roles: `admin` (platform, full), `operator` (platform, stub), `doctor` (tenant, full), `receptionist` (tenant, stub)
- Platform admin endpoints: 9 canonical endpoints in `admin/routes.py`; legacy compatibility endpoints remain under `auth/routes.py`
- AI module status: `/api/v1/ai/query` is wired as a `501 Not Implemented` stub endpoint

## AI Assistant Notes

When answering implementation questions, prefer these sources in order:
1. `backend/app/main.py` for what is actually exposed
2. `backend/app/modules/*/routes.py` for endpoint truth
3. `frontend/src/app/**` for current UI coverage
4. `status/current.md` for narrative status

## Related Root Files

- `../CLAUDE.md` - codebase guidance for AI coding agents
- `../README.md` - public project overview
- `../CHANGELOG.md` - release notes
- `../SECURITY_AUDIT_REPORT.md` - security review summary
