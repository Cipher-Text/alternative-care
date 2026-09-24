# Changelog

All notable changes to AltCare are documented here.

---

## [Unreleased] - 2026-09-24

### Backend
- Google Sign-In and registration (`POST /auth/google`, `POST /auth/google/register`), password reset (`POST /auth/password/forgot`, `/password/reset`), and email verification (`POST /auth/email/verify`, `/email/resend`) shipped 2026-09-23 — see `docs/api/authentication.md`. Auth module grew from 19 to 21 endpoints; total module endpoints 133 → 135.
- Test suite grew from 422 to 432 passed (2 xfailed, 0 failed) covering the above.
- Global medicine/symptom creation fixed 2026-09-24 — `medicines`/`symptoms`/`medicine_aliases`/`symptom_aliases`/`medicine_symptom_mappings` moved to a nullable `tenant_id` with a CHECK constraint (migration `ba209a25bf7d`), so `POST /medicines`/`POST /symptoms` with `is_global=true` no longer 500s. See `docs/planning/revision-2026-09.md` Stage 2 (D1).
- Billing enforcement shipped 2026-09-24 — `require_plan()` now checks the tenant's `plan`/`plan_expires_at` in the database instead of the JWT claim, so a downgrade or expiry revokes pro access immediately. `usage_tracking` gets its first writers (`app/core/usage_tracking.py`): prescription issue, SMS send, and AI query. New `GET /admin/tenants/{id}/usage` endpoint; total module endpoints 135 → 136. Migration `ed07cf4aebc7` adds `usage_tracking.sms_sent` and a `(tenant_id, usage_date)` unique constraint. See `docs/planning/revision-2026-09.md` Stage 1.
- Test suite grew from 432 to 442 passed (1 xfailed, 0 failed) — `test_plan_downgrade_revokes_pro_access` is no longer `xfail`.

### Frontend
- next-intl actually wired up (cookie-based locale, no URL routing): `NextIntlClientProvider` in the root layout, `src/i18n/request.ts` request config, `LanguageSwitcher` component in the header, locale synced to the user's stored `language` preference on login. Coverage so far: login card and header user dropdown only — the rest of the app is still hardcoded English.
  - Note: the `[1.0.0]` entry below lists "Bilingual UI (English/Bengali) via next-intl" as shipped — `next-intl` was installed and message files existed, but no provider/middleware/`useTranslations` call existed anywhere in the code until this change. Left the 1.0.0 entry as-is (historical record); noting the correction here instead.
  - Also unsourced in that entry: "MVP Production Ready" and "16/16 tests passing" — no deploy path existed at the time (still none today, see `docs/planning/revision-2026-09.md`), and no cited run backs the 16/16 figure. Left as-is for the same historical-record reason; see the revision doc §1 for the actual, dated numbers.

---

## [1.0.0] - 2026-05-22 — MVP Production Ready

### Backend (11 modules, 89 endpoints, 34 tables)
- Authentication: Login, JWT, refresh tokens, 2FA/TOTP, password security, session management
- Patient Management: CRUD, search, tags, diagnoses
- Appointments: Scheduling, visits
- Prescriptions: CRUD, items, draft→issued→voided workflow, PDF export
- Doctor Profile: Profile, degrees, trainings
- Payments: Processing, bKash integration, invoices
- Integrations: SMS (BulkSMSBD), Email (SMTP), Payment (bKash) — encrypted credentials, audit logs
- Dashboard: Analytics, revenue stats, demographics
- Medicines: CRUD, search, aliases, medicine-symptom mappings
- Symptoms: CRUD, search, aliases
- AI Query: Stub endpoint, pro-plan gated (501 Not Implemented)

### Frontend (110+ source files)
- All MVP modules: auth, dashboard, patients, appointments
- All post-MVP modules: prescriptions (builder + autocomplete), doctor profile, payments, integrations, medicines, symptoms
- Bilingual UI (English/Bengali) via next-intl

### Security
- Multi-tenant row-level isolation (16/16 tests passing)
- Redis-backed rate limiting (login/API/AI tiers)
- HTTP security headers (CSP, X-Frame-Options, HSTS)
- Password complexity enforcement
- Session invalidation on security changes

### Infrastructure
- Docker Compose: PostgreSQL 16 + pgvector, Redis 7, MinIO
- Alembic migrations, Celery background tasks
- Playwright E2E tests, pytest with async support

---

## [0.1.0] - 2026-04-21 — Backend Foundation

- FastAPI application with SQLAlchemy 2.0 async ORM
- Initial 30 database models and Alembic migrations
- JWT authentication, TOTP 2FA, bcrypt passwords
- Multi-tenant middleware with ContextVar isolation
- RBAC and plan-based feature gating
- Fernet encryption for integration credentials
- Docker Compose infrastructure setup
