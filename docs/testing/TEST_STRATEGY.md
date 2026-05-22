# AltCare Testing Strategy (Single Source of Truth)

**Last Updated:** May 23, 2026  
**Scope:** MVP v1.0 backend + frontend quality gates

## Purpose

This document is the canonical reference for:
- test principles
- required test types
- module-wise ownership
- CI quality gates
- MVP testing gaps and priorities

Roadmap files should track progress only and link back here for standards.

## Principles

- Risk-first: protect auth, tenancy, prescription, and payment flows first.
- Shift-left: validate logic in unit tests before API/E2E.
- Isolation-first: every tenant boundary and role boundary must be testable.
- Deterministic: tests must be repeatable, data-seeded, and CI-safe.
- Fast feedback: keep smoke suites short and required on every PR.

## Test Pyramid

- Unit tests: service/business logic and schema validation.
- Integration tests: API routes + DB + auth/rbac behavior.
- E2E tests: critical user paths across frontend + backend.
- Security tests: negative auth/authorization/rate-limit/header cases.
- Performance tests: benchmark critical endpoints and query patterns.
- Migration tests: alembic upgrade/downgrade safety.
- Contract tests: schema/response-shape compatibility for critical APIs.

## Backend Module Matrix

Standard per-module template:
- unit tests
- integration tests (happy + negative)
- authorization + tenant isolation tests
- contract/schema checks

Current module status (MVP):
- `auth`: covered (unit + integration + security). Contract checks pending.
- `patient`: covered (unit + integration). Contract checks pending.
- `appointment`: covered (unit + integration). Contract checks pending.
- `prescription`: covered (unit + integration + tenant isolation). Contract checks pending.
- `payment`: covered (unit + integration). Contract checks pending.
- `doctor`: covered (unit + integration). Contract checks pending.
- `dashboard`: covered (unit + integration). Contract checks pending.
- `integration`: partial for MVP test standards; needs dedicated unit/integration/tenant tests.
- `ai`: out of MVP scope (stub endpoint), no full module test pack yet.
- `library`: out of MVP scope, no module tests yet.
- `medicine`: out of MVP core test scope, no module tests yet.

## Frontend Module Matrix

Standard per-module template:
- component tests (critical states + validation)
- page-level integration tests (fetch/submit/error states)
- route protection + role/tenant access checks
- API failure handling tests (4xx/5xx/timeout)

MVP current reality:
- E2E coverage exists for auth, dashboard access, patient CRUD, tenant-isolation path.
- E2E coverage now includes:
  - smoke login and dashboard redirect checks
  - 2FA UI flow (mocked auth responses)
  - token refresh retry behavior (mocked 401 + refresh)
  - patient CRUD flow (create/read/update/delete)
  - cross-tenant patient access blocked (API-level E2E assertion)
- Component/integration test harness is not yet established as a required CI gate.

## Cross-Cutting Required Suites

- Multi-tenant isolation
- Auth + token security negatives
- Rate limiting behavior
- Security headers baseline
- Critical smoke flow:
  - login
  - create patient
  - create appointment or prescription
  - record payment

## CI/CD Quality Gates (Required)

- Backend required suites must pass on every PR.
- Frontend required suites must pass on every PR.
- Coverage threshold enforced for backend module scope.
- Smoke E2E suite is blocking for merge.
- Migration safety check is blocking for merge.

## Test Organization

- Backend tests: `backend/tests/unit`, `backend/tests/integration`, `backend/tests/performance`
- Frontend/E2E tests: `tests/e2e/specs`
- Conventions:
  - file pattern: `test_*.py` for backend, `*.spec.ts` for e2e
  - one module per test file where practical
  - keep fixtures centralized in `conftest.py` or e2e `fixtures/`

## MVP Gaps To Close Now

1. Add `integration` module test pack (unit + integration + tenant isolation).
2. Add migration safety automation (`upgrade head`, downgrade sanity, re-upgrade).
3. Add contract/schema checks for critical backend APIs.
4. Enforce CI gates for required suites and backend coverage threshold.
5. Add frontend component/page integration test baseline and make it required.

## Backend Missing Tests (MVP Scope, Actionable)

- [x] `integration` module unit tests:
  - [x] provider factory selection and fallback behavior
  - [x] credential encryption/decryption validation
  - [x] provider config validation errors
- [x] `integration` module integration/API tests:
  - [x] create/update/list tenant integrations
  - [x] test endpoint success/failure responses
  - [x] enable/disable integration status transitions
  - [x] integration log/usage access behavior
- [x] `integration` tenant isolation tests:
  - [x] tenant A cannot read/update/test tenant B integration configs
  - [x] tenant A cannot read tenant B integration logs/usage
- [x] Contract/schema checks for critical backend endpoints:
  - [x] `auth` (`/login`, `/me`)
  - [x] `patient` (create)
  - [x] `appointment` (create)
  - [x] `prescription` (create)
  - [x] `payment` (create)
- [x] Migration safety tests in CI:
  - [x] clean DB `alembic upgrade head`
  - [x] downgrade sanity `alembic downgrade -1`
  - [x] re-upgrade validation after downgrade
- [x] CI enforcement gaps:
  - [x] backend test job required on PR
  - [x] backend coverage threshold required on PR
  - [x] migration safety job required on PR

## Frontend Missing Tests (MVP Scope, Actionable)

- [ ] Add component tests for critical auth and patient components:
  - `LoginForm`, `TwoFactorForm`, `PatientForm`, `PatientCard`
- [ ] Add page integration tests (non-E2E) for key routes:
  - `/login`, `/patients`, `/patients/new`, `/dashboard`
- [ ] Add API error-state tests in UI (4xx/5xx/timeout rendering behavior)
- [ ] Add required CI frontend test job (component/integration + e2e smoke)
- [ ] Add i18n and accessibility baseline checks for critical screens

## Run Commands (Reference)

Backend:
- `cd backend && pytest`

E2E:
- `npx playwright test -c tests/e2e/playwright.config.ts`

Frontend unit/integration (to add with harness):
- `npm -C frontend run test`

## PR Checklist (Testing)

- [ ] Changed module has unit tests updated/added
- [ ] Changed API route has integration tests updated/added
- [ ] Tenant/authz behavior verified for sensitive changes
- [ ] No regression in smoke flow
- [ ] CI gates pass
