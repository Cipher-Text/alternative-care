# Changelog

All notable changes to AltCare are documented here.

---

## [Unreleased] - 2026-09-21

### Frontend
- next-intl actually wired up (cookie-based locale, no URL routing): `NextIntlClientProvider` in the root layout, `src/i18n/request.ts` request config, `LanguageSwitcher` component in the header, locale synced to the user's stored `language` preference on login. Coverage so far: login card and header user dropdown only — the rest of the app is still hardcoded English.
  - Note: the `[1.0.0]` entry below lists "Bilingual UI (English/Bengali) via next-intl" as shipped — `next-intl` was installed and message files existed, but no provider/middleware/`useTranslations` call existed anywhere in the code until this change. Left the 1.0.0 entry as-is (historical record); noting the correction here instead.

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
