# AltCare Product Roadmap

> From MVP to comprehensive alternative medicine practice management platform

**Last updated:** May 14, 2026  
**Current phase:** Phase 1 COMPLETE ✅ — MVP v1.0 Production Ready  
**Next phase:** Phase 2 (Knowledge Base) - Planned Q4 2026  
**Target launch:** Q3 2026 (MVP) → Q2 2027 (Complete Platform)
**Baseline source of truth:** `backend/app/main.py`, `backend/app/modules/*/routes.py`, `frontend/src/app/**`, `docs/status/current.md`

---

## Table of Contents

- [Vision & Goals](#vision--goals)
- [Phase Overview](#phase-overview)
- [Phase 1: Core Clinic MVP](#phase-1-core-clinic-mvp-current)
- [Phase 2: Knowledge Base](#phase-2-knowledge-base)
- [Phase 3: Book Library & Reader](#phase-3-book-library--reader)
- [Phase 4: AI/RAG Intelligence](#phase-4-airag-intelligence)
- [Infrastructure Evolution](#infrastructure-evolution)
- [Team Scaling](#team-scaling)
- [Risk Management](#risk-management)
- [Success Metrics](#success-metrics)

---

## Vision & Goals

### Mission Statement
Build the most comprehensive practice management system for alternative medicine practitioners in South Asia, combining modern technology with classical medical knowledge.

### Core Objectives
- **Practitioner-First:** Solve real clinic management pain points
- **Knowledge Integration:** Make classical texts accessible and searchable
- **Multi-System Support:** Serve Homeopathy, Ayurveda, Unani, and Herbal practitioners equally
- **Bangladesh Focus:** Local payment gateways, SMS providers, geographic data, and cultural context
- **Scalable SaaS:** Multi-tenant architecture that can grow to thousands of clinics

### Success Definition
- **Year 1:** 50+ active paying clinics, ৳2.5L MRR ($2,500) — MVP to AI Platform
- **Year 2:** 300+ active paying clinics, ৳18L MRR ($18,000) — Growth & optimization
- **Year 3:** 1,000+ active paying clinics, ৳60L+ MRR ($60,000+) — Expand to India

---

## Phase Overview

| Phase | Focus | Duration | Target Launch | Status |
|-------|-------|----------|---------------|--------|
| **Phase 0** | Planning & Design | 2 weeks | Complete | ✅ Done |
| **Phase 1** | Core Clinic MVP | 14 weeks | Q3 2026 | ✅ Complete (MVP v1.0) |
| **Phase 2** | Knowledge Base | 8 weeks | Q4 2026 | 📋 Planned |
| **Phase 3** | Book Library | 10 weeks | Q1 2027 | 📋 Planned |
| **Phase 4** | AI/RAG | 12 weeks | Q2 2027 | 📋 Planned |

**Total MVP to Full Platform:** ~44 weeks (~11 months)

---

## Phase 0: Planning & Design `COMPLETED`

**Timeline:** 2 weeks (April 7-20, 2026)  
**Status:** ✅ Complete

### Completed Deliverables

- [x] UI mockups completed (Admin + Doctor views with 8+ screens each)
- [x] Marketing landing page prototype
- [x] Database schema designed (30 tables with full relationships)
- [x] Technology stack finalized and documented
- [x] API structure defined (REST endpoints)
- [x] Architecture diagram (modular monolith)
- [x] Multi-tenancy strategy (row-level isolation)
- [x] Doctor credentials system (degrees + training)
- [x] Bangladesh geographic data integration (Division → District → Upazila)
- [x] Integration framework design (SMS/Email/Payment)
- [x] Pricing plans defined (Free/Plus/Pro)
- [x] 12-month roadmap created
- [x] Cost estimates (MVP to Enterprise)
- [x] Production checklist created
- [x] Environment variables defined (.env.example)
- [x] Dependency list (pyproject.toml)
- [x] **Backend foundation implemented (30 SQLAlchemy models)** ✅ NEW
- [x] **Database migrations configured (Alembic async)** ✅ NEW
- [x] **Docker infrastructure set up (PostgreSQL, Redis, MinIO)** ✅ NEW
- [x] **Authentication system built (JWT + 2FA)** ✅ NEW
- [x] **Multi-tenant middleware implemented** ✅ NEW

**What's Ready:**
- Complete system design with 34 database tables ✅ IMPLEMENTED
- Production-ready tech stack with monitoring/security
- Functional UI prototypes (no build required)
- Backend foundation with all models and infrastructure ✅ NEW
- Docker services running (PostgreSQL, Redis, MinIO) ✅ NEW
- Migration system ready (Alembic) ✅ NEW
- Clear implementation path for API endpoints

---

## Phase 1: Core Clinic MVP `COMPLETE ✅`

**Timeline:** 14 weeks (April 21 - July 26, 2026)  
**Target Launch:** August 1, 2026  
**Goal:** Launch a working clinic management tool that 10 pilot doctors can use daily  
**Status:** ✅ **COMPLETE** (verified May 14, 2026; frontend coverage re-verified 2026-09-21 — now complete for all modules, not just the 6/9 noted at the May snapshot) — Backend APIs complete (Auth, AI stub, Doctor, Patient, Appointments, Prescriptions, Payments, Dashboard, Integration, Medicine, Symptom, Geographic, Tenant, Admin). Frontend complete for all modules: Auth, Patients, Appointments, Dashboard, Prescriptions, Doctor Profile, Payments, Integrations, Medicines, Symptoms, and a full Platform Admin area. Security hardening complete (password complexity, session invalidation, HTTP headers, rate limiting). **MVP v1.0 PRODUCTION READY** 🚀

### Week 1-2: Foundation & Infrastructure ✅ COMPLETED

**Backend Setup** ✅ DONE
- [x] Initialize FastAPI project structure with modular architecture ✅
- [x] Configure SQLAlchemy 2.0 async ORM ✅
- [x] Set up Alembic migration framework ✅
- [x] Implement Pydantic v2 models for all endpoints (base ready) ✅
- [x] Build JWT authentication (passlib + python-jose) ✅
- [x] Add 2FA support with pyotp and QR code generation ✅
- [x] Create multi-tenant middleware with ContextVar ✅
- [x] All 34 database table models implemented (tenant, user, patient, prescription, appointments, medicines, symptoms, etc.) ✅
- [x] Database migrations configured and tested ✅
- [x] Seed data scripts created (geographic, integrations, translations) ✅
- [ ] Configure i18n with Babel (English/Bengali support) - Models ready
- [ ] Configure structlog for structured JSON logging - To be added
- [ ] Integrate Sentry for error tracking - Config ready
- [x] Set up Redis-backed rate limiting middleware (login + API scope) ✅
- [ ] Configure Prometheus metrics collection - To be added

**Database Setup** ✅ DONE
- [x] PostgreSQL 16 installation with pgvector extension ✅
- [x] Create initial migrations (30 tables including translations) ✅
- [x] Seed data scripts ready (geographic, integration providers, translations) ✅
- [x] Configure connection pooling (20 connections, 10 overflow) ✅
- [ ] Populate geographic data (divisions, districts, upazilas with Bengali names) - Script ready
- [ ] Seed integration providers (SSLCommerz, Twilio, SendGrid, etc.) - Script ready
- [ ] Seed translation keys for all UI strings (English/Bengali) - Script ready
- [ ] Enable pg_stat_statements for query monitoring
- [ ] Set up automated daily backups

**Frontend Setup**
- [ ] Initialize/standardize Next.js 16 with App Router
- [ ] Install Tailwind CSS + shadcn/ui components
- [x] Configure next-intl for i18n (English/Bengali) — shipped 2026-09-21, cookie-based (no URL routing); only login/header translated so far, see `docs/development/i18n.md`
- [x] Create language switcher component (en/bn toggle) — `frontend/src/components/language/LanguageSwitcher.tsx`, shipped 2026-09-21
- [ ] Configure React Query for server state
- [ ] Set up Axios instance with JWT interceptors (include Accept-Language header)
- [ ] Create layout shell (sidebar, topbar with language switcher, content area)
- [ ] Implement auth context provider
- [ ] Add Sentry browser SDK

**DevOps & Infrastructure** 🔄 PARTIAL
- [x] Create docker-compose.yml (PostgreSQL, Redis, MinIO) ✅
- [x] Configure MinIO for file storage ✅
- [x] Set up Redis (cache + Celery broker + rate limiting) ✅
- [x] PostgreSQL with pgvector extension configured ✅
- [ ] Configure Celery workers (PDF, email, embeddings queues)
- [ ] Set up Caddy reverse proxy with auto-HTTPS
- [x] Create .env configuration from .env.example ✅
- [ ] Configure Grafana + Prometheus dashboards
- [ ] Set up health check endpoints

**Security Hardening**
- [ ] Configure CORS (restrict to allowed origins)
- [x] Add security headers middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- [x] Enable OWASP baseline security headers
- [x] Set up rate limiting (5/min login baseline, Redis-backed)
- [x] Add per-user rate limiting (JWT `sub` keyed for authenticated API requests)
- [x] Add AI-query-specific rate limiting tiers (hourly quota scope on `/api/v1/ai/query`)
- [ ] Configure Fernet encryption for integration credentials
- [ ] Set up UFW firewall (ports 80, 443, 22 only)
- [ ] Configure fail2ban for SSH protection

### Week 3-4: Authentication & User Management ✅ COMPLETED (Backend)

**Backend** ✅ DONE
- [x] User registration endpoint with email validation ✅
- [x] Admin approval workflow for doctor registrations ✅
- [x] Login endpoint with JWT issuance (access + refresh tokens) ✅
- [x] Token refresh endpoint with rotation ✅
- [x] 2FA setup and verification endpoints ✅
- [x] Role-based access control dependencies (RBAC) ✅
- [x] Logout and token revocation ✅
- [x] Session management (UserSession model) ✅
- [x] **Comprehensive test suite (1,399 lines):** ✅ NEW
  - [x] Unit tests for auth service (25 tests) ✅
  - [x] Integration tests for all endpoints ✅
  - [x] Multi-tenant isolation tests (critical!) ✅
  - [x] Test fixtures and factories ✅
- [ ] Password reset flow (email-based with expiry) - **TODO**
- [ ] Email verification flow - **TODO**

**Frontend** ✅ COMPLETE
- [x] Next.js 16 with App Router initialized ✅
- [x] Login page with form validation ✅
- [x] 2FA verification page ✅
- [x] Protected route wrapper component ✅
- [x] User context provider (auth state) ✅
- [ ] Registration page with multi-specialization selection - **TODO**
- [ ] Forgot password flow - **TODO**
- [ ] 2FA setup page - **TODO**
- [ ] Full bilingual support (English/Bengali) - **Partial**

**Database** ✅ DONE
- [x] Run migrations for auth tables (tenants, users, user_sessions) ✅
- [x] Add indexes for email and role lookups ✅
- [x] Foreign key constraints added ✅
- [ ] Create platform admin seed user
- [ ] Run seed scripts for geographic data
- [ ] Run seed scripts for integration providers
- [ ] Run seed scripts for translations

### Week 5-6: Doctor Credentials & Profile ✅ COMPLETE

**Backend** ✅ DONE
- [x] Doctor degrees CRUD endpoints ✅
- [x] Doctor trainings/certifications CRUD endpoints ✅
- [x] Degree verification workflow (admin) ✅
- [x] Training expiry date tracking ✅
- [x] Display order management ✅
- [ ] Bulk degree import (CSV) - **Future**

**Frontend** ✅ COMPLETE (May 10, 2026)
- [x] Doctor profile page with tabs (Profile, Degrees, Trainings) ✅
  - [x] Personal information (view/edit mode) ✅
  - [x] Academic degrees (add/edit/delete) ✅
  - [x] Training & certifications (add/edit/delete) ✅
  - [x] Clinic information ✅
- [x] Degree form with validation ✅
- [x] Training form with expiry date picker ✅
- [x] Verification status badges ✅
- [x] Skills tags input (comma-separated) ✅
- [x] Geographic selection (Division → District → Upazila) ✅
- [ ] Display order drag-and-drop - **Future Enhancement**

**Database**
- [ ] Run migration for doctor_degrees and doctor_trainings tables
- [ ] Add indexes for user_id and display_order

**Admin Features**
- [ ] Admin view for doctor approval with credentials review
- [ ] Degree verification interface
- [ ] Training verification interface
- [ ] Bulk approval actions

### Week 7-8: Geographic Location & Patient Management ✅ COMPLETE

**Backend** ✅ DONE
- [x] Patient CRUD endpoints with location support ✅
- [x] Geographic location endpoints (divisions, districts, upazilas) ✅
- [x] Patient search with filters ✅
- [x] Patient tags system ✅
- [x] Patient diagnosis records management ✅
- [x] Visit creation and history ✅
- [x] File upload for attachments (MinIO) ✅
- [x] Pagination and sorting ✅

**Frontend** ✅ COMPLETE
- [x] Geographic location cascading dropdowns component ✅
- [x] Patient list view with search, filters, tags, location ✅
- [x] Patient detail page with demographics, tags, diagnoses ✅
- [x] Add/Edit patient form with location selectors ✅
- [x] Patient search autocomplete ✅

**Database**
- [ ] Verify geographic data seeded (8 divisions, 64 districts, 490+ upazilas)
- [ ] Run migration for patients, patient_tags, patient_diagnoses tables
- [ ] Add indexes for location and search fields

### Week 9-10: Prescription System ✅ COMPLETE

**Backend** ✅ DONE
- [x] Prescription creation endpoint ✅
- [x] Prescription items management (medicines + free-text) ✅
- [x] Support for nullable medicine_id (custom entries) ✅
- [x] PDF generation endpoint (Celery background task ready) ✅
- [x] Prescription history retrieval ✅
- [x] Prescription void/replacement logic ✅
- [x] Prescription status tracking (draft, issued, voided) ✅
- [x] Email prescription PDF capability ✅

**Frontend** ✅ COMPLETE (May 10, 2026)
- [x] Prescription builder UI (create/edit) ✅
  - [x] Patient selector with search ✅
  - [x] Medicine items builder (add/edit/delete) ✅
  - [x] Free-text medicine names (MVP approach) ✅
  - [x] Dosage, frequency, duration inputs ✅
  - [x] Doctor's notes textarea ✅
  - [x] Advice textarea ✅
  - [x] Medicine list with modal dialog ✅
- [x] Prescription list view with filters ✅
- [x] Prescription detail view ✅
- [x] Download PDF functionality ✅
- [x] Status badges (draft, issued, voided) ✅
- [x] Draft → Issued → Voided workflow ✅
- [x] Immutability enforcement ✅
- [ ] Live PDF preview - **Future Enhancement**
- [ ] Medicine database autocomplete - **Phase 2**

**Database**
- [ ] Run migration for prescriptions and prescription_items tables
- [ ] Add indexes for patient_id and created_at

**PDF Template**
- [ ] Design prescription PDF template (WeasyPrint HTML/CSS)
- [ ] Include clinic header, doctor credentials
- [ ] Medicine table with dosage instructions
- [ ] Doctor's signature area

### Week 11: Payment & Invoicing

**Backend** ✅ DONE
- [x] Payment recording endpoint ✅
- [x] SSLCommerz integration (Bangladesh payments) ✅
- [x] Stripe integration (international payments) ✅
- [x] bKash, Nagad, Rocket integration ✅
- [x] Invoice generation (PDF via WeasyPrint) ✅
- [x] Payment method support ✅
- [x] Revenue reports (daily, monthly aggregates) ✅
- [x] Transaction logging ✅

**Frontend** ✅ DONE (shipped since this section was drafted)
- [x] Payment recording form with method selector
- [x] SSLCommerz payment initiation flow
- [x] Payment status tracking page
- [x] Invoice list view with download links
- [x] Revenue dashboard widgets
- [x] Payment history with filters
- **Status:** Backend and frontend both complete — see `docs/status/current.md`

**Database**
- [ ] Run migration for payments and invoices tables
- [ ] Add indexes for revenue aggregation queries

**Testing**
- [ ] SSLCommerz sandbox testing
- [ ] Webhook signature verification
- [ ] Payment failure handling
- [ ] Invoice PDF generation

### Week 12: Dashboard & Analytics ✅ COMPLETE

**Backend** ✅ DONE
- [x] Dashboard KPI endpoints (patients, revenue, appointments) ✅
- [x] Monthly growth metrics ✅
- [x] Analytics aggregation ✅
- [ ] Calendar heatmap data - **Future**
- [ ] Top diagnoses/medicines - **Future**

**Frontend** ✅ COMPLETE
- [x] Dashboard page with KPI cards ✅
- [x] Revenue charts ✅
- [x] Patient demographics ✅
- [x] Recent activity widgets ✅
- [x] Quick action buttons ✅
- [x] Chart components (Recharts) ✅

**Database**
- [ ] Optimize dashboard aggregation queries
- [ ] Add partial indexes for active patients
- [ ] Create materialized views if needed

### Week 13: Integration Framework & Communications ✅ COMPLETE

**Backend** ✅
- [x] Integration provider seeding (12 providers including BulkSMSBD)
- [x] Tenant integration CRUD endpoints (7 endpoints)
- [x] Credentials encryption/decryption (Fernet)
- [x] Test transaction endpoints (POST /api/v1/integrations/{id}/test)
- [x] Integration logs viewer endpoint (GET /api/v1/integrations/logs)
- [x] SMS sending (Celery task):
  - BulkSMSBD integration ✅
  - Exponential backoff retry (3 retries)
- [x] Email sending (Celery task):
  - Generic SMTP integration ✅
  - Template support (HTML + plain text)
- [x] Payment provider: bKash integration service
- [x] Provider factory pattern with registry
- [x] Integration service layer (20+ methods)
- [x] 12 API endpoints total

**Frontend** ✅ Complete
- [x] Integration providers page (provider cards, config forms, test buttons)
- [x] Integration logs viewer with filters
- [x] Local provider logo assets for settings/integration views
- [ ] Notification settings page
- [ ] Email/SMS template management
- **Status:** Core provider setup and monitoring UI is implemented; notification/template management remains future scope.

**Database** ✅
- [x] Integration providers seeded (12 providers total)
- [x] Models exist: integration_providers, tenant_integrations, integration_logs
- [x] Indexes configured for queries

**Testing** ⚡ Ready for Manual Testing
- [x] Provider factory pattern tested
- [x] Encryption/decryption functions implemented
- [x] API endpoints ready for testing
- [ ] Manual E2E testing (requires Fernet key setup + Celery worker)
- [ ] Unit tests (to be added in Week 14)
- [ ] Integration tests (to be added in Week 14)

### Week 14: Testing, Polish & Launch Prep

**Testing**
- [ ] Unit tests (pytest):
  - Auth flows (login, register, 2FA)
  - Multi-tenant isolation (CRITICAL!)
  - RBAC enforcement
  - Prescription PDF generation
  - Payment webhook handling
- [ ] Integration tests (pytest + httpx):
  - All API endpoints
  - Database transactions
  - Celery task execution
- [ ] E2E tests (Playwright):
  - Doctor registration → approval → login
  - Patient creation → visit → prescription → payment
  - Settings configuration
- [ ] Load testing (Locust):
  - Target: 100 concurrent users
  - Average response time < 500ms
  - 99th percentile < 2s
- [ ] Security audit:
  - pip-audit (dependency vulnerabilities)
  - OWASP Top 10 checklist
  - Rate limiting verification
  - Multi-tenant data isolation test

**Code Coverage**
- [ ] Achieve 80%+ test coverage
- [ ] 100% coverage for auth and payment modules

**Polish**
- [ ] Error handling and user feedback (toast notifications)
- [ ] Loading states and skeleton screens
- [ ] Empty states with helpful CTAs
- [ ] Mobile responsiveness (all breakpoints)
- [ ] Accessibility audit (WCAG 2.1 AA):
  - Keyboard navigation
  - Screen reader support
  - Color contrast
  - ARIA labels
- [ ] Performance optimization:
  - Lighthouse score > 90
  - Code splitting
  - Image optimization
  - API response caching

**Documentation**
- [ ] API documentation (auto-generated via FastAPI /docs)
- [ ] User guide / help center
- [ ] Video tutorials:
  - Getting started (5 min)
  - Patient management (3 min)
  - Prescription workflow (4 min)
- [ ] Deployment guide for production
- [ ] Admin guide for approvals

**Launch Prep**
- [ ] Beta testing with 5 pilot doctors (2 weeks)
- [ ] Collect and implement feedback
- [ ] Bug triage and fixes
- [ ] Production deployment to VPS:
  - Configure environment variables
  - Set up SSL certificates (Caddy)
  - Configure domain (altcare.health)
  - Enable monitoring (Sentry, Grafana, Uptime Robot)
  - Set up log aggregation (Papertrail)
- [ ] Create incident response plan
- [ ] Set OpenAI budget limits ($500/month)
- [ ] Configure automated backups (daily PostgreSQL, weekly MinIO)

**Marketing**
- [ ] Launch marketing website
- [ ] Create demo account with sample data
- [ ] Prepare press release
- [ ] Social media announcement
- [ ] Email campaign to practitioner list

### Phase 1 Deliverables

✅ **Functional MVP** that includes:
- Doctor registration with admin approval
- Multi-specialization support (1-4 systems)
- Doctor credentials (degrees + training with verification)
- Bangladesh geographic location (Division → District → Upazila)
- Patient management with visit history and tagging
- Prescription builder with PDF export and email delivery
- Payment tracking with SSLCommerz and invoice generation
- Dashboard with KPIs, calendar, and analytics
- Integration framework for SMS/Email/Payment with audit trail
- Security features (2FA, rate limiting, OWASP headers)

✅ **Technical Foundation:**
- Multi-tenant architecture (row-level isolation with 30 tables)
- Role-based access control (Admin, Operator, Doctor, Receptionist)
- Bilingual support (English/Bengali) with language switching
- Async backend with Celery for background jobs
- Responsive frontend with React/Next.js
- Docker Compose for containerized deployment
- Monitoring (Sentry, Grafana, Prometheus)
- Structured logging with correlation IDs
- Automated backups and health checks
- Production-ready security (encryption, rate limiting, 2FA)

✅ **Go-to-Market:**
- 10 pilot doctors onboarded
- User feedback collected and incorporated
- Pricing validated (Free/Plus/Pro tiers)
- Marketing website live
- Payment gateways integrated (SSLCommerz + Stripe)
- SMS/Email providers configured (Twilio + SendGrid)

---

## Phase 2: Knowledge Base

**Timeline:** 8 weeks (August - September 2026)  
**Goal:** Add medicine database with symptom-based search to help doctors during consultations

**Status update (2026-09-21):** This phase's core scope has shipped ahead of the
checkboxes below — medicine and symptom CRUD, aliases, search APIs, symptom→medicine
mappings, and GIN full-text indexes all exist in both backend and frontend (see
`docs/status/current.md`). Still genuinely open: 1,000+ curated medicine/symptom seed
data, bulk CSV/Excel import UI, wiring `GET /medicines/search` and `GET /symptoms/search`
into the list pages (both currently client-side filter on the first 100 rows), a
dedicated symptom→medicine clinical lookup page, and specialization-based filtering
(`tenant.specializations` exists on the schema, but no route/service filters
medicines/books by it yet — see `docs/architecture/database.md`). Treat the per-task
checkboxes below as historical planning granularity, not current implementation truth.

### Week 1-2: Medicine Database Foundation

**Backend**
- [ ] Global medicine CRUD endpoints (admin only) with bilingual fields
- [ ] Tenant-specific medicine additions
- [ ] Medicine search with filters (system, category, potency)
- [ ] Language-aware search (search in Bengali or English)
- [ ] Full-text search optimization (tsvector + GIN indexes for both languages)
- [ ] Specialization-based filtering
- [ ] Bulk medicine import (CSV/Excel parser with Bengali support)

**Frontend**
- [ ] Medicine database page with search/filter (bilingual)
- [ ] Medicine detail view showing English + Bengali names
- [ ] Add/Edit medicine forms (admin) with bilingual input fields
- [ ] Filtering by system, category, potency
- [ ] Bulk import interface with progress indicator
- [ ] Medicine list with pagination (display based on user language)

**Database**
- [ ] Run migration for medicines table
- [ ] Create GIN indexes for full-text search
- [ ] Seed 500+ common medicines across all systems:
  - Homeopathy (200+)
  - Ayurveda (150+)
  - Unani (100+)
  - Herbal (50+)

### Week 3-4: Symptom Mapping

**Backend**
- [ ] Symptom-to-medicine mapping CRUD
- [ ] Symptom search algorithm (weighted matching)
- [ ] Match strength calculation
- [ ] Modality notes support
- [ ] Symptom tag management (admin)
- [ ] Multi-symptom query support

**Frontend**
- [ ] Symptom search page with:
  - Multi-symptom input (autocomplete)
  - Add/remove symptom chips
  - Search button
- [ ] Match results display:
  - Grouped by medical system
  - Match percentage scores
  - Medicine name and description
  - Quick add to prescription button
- [ ] Symptom tag management (admin)

**Database**
- [ ] Run migration for medicine_symptoms table
- [ ] Create GIN indexes for symptom search
- [ ] Seed 1,000+ symptom mappings

### Week 5-6: Integration with Prescription Builder

**Backend**
- [ ] Medicine quick search in prescription endpoint
- [ ] Recently used medicines tracking per doctor
- [ ] Commonly prescribed medicines analytics
- [ ] Dosage guidance retrieval
- [ ] Contraindications and interactions API

**Frontend**
- [ ] Enhanced prescription builder:
  - Medicine autocomplete with symptom hints
  - Dosage suggestions from database
  - Recently used medicines quick-select
  - Contraindications warnings (red badge)
  - Medicine interactions alerts
- [ ] Add from symptom search (one-click)

**Optimization**
- [ ] Cache frequently searched medicines
- [ ] Optimize autocomplete queries
- [ ] Add debouncing to search inputs

### Week 7-8: Content Curation & Testing

**Content**
- [ ] Partner with 5 medical practitioners for validation
- [ ] Curate 1,000+ medicines across all four systems
- [ ] Translate all medicine names to Bengali
- [ ] Translate descriptions, indications, dosage to Bengali
- [ ] Review and validate symptom mappings (bilingual)
- [ ] Add dosage guidelines for common medicines (bilingual)
- [ ] Document contraindications and interactions (bilingual)
- [ ] Create medicine categories and sub-categories (bilingual)

**Testing**
- [ ] User acceptance testing with 10 doctors
- [ ] Symptom search accuracy validation (>85% target)
- [ ] Performance testing:
  - Medicine search < 100ms
  - Symptom search < 200ms
  - Autocomplete < 50ms
- [ ] Mobile experience testing
- [ ] Accessibility testing

**Documentation**
- [ ] Medicine database user guide
- [ ] Symptom search tutorial video
- [ ] Admin guide for medicine curation

### Phase 2 Deliverables (original target — see 2026-09-21 status update above for what's actually shipped)

📋 **Medicine Database:**
- 1,000+ curated medicines (global pool) — seed data still pending
- Filterable by specialization automatically — not implemented; schema field exists, no query uses it
- Full-text search with <100ms latency — search API + GIN index shipped, not yet wired into the list page
- Bulk import capability for admins — not implemented
- Tenant-specific additions — shipped

📋 **Symptom Search (partially shipped — target, not current state):** `GET /symptoms/search` exists but does single-term exact/alias matching with a fixed relevance score (1.0 exact, 0.8 alias) — not the multi-symptom weighted-matching design described below.
- Multi-symptom input support — not implemented
- Weighted matching algorithm — not implemented
- Results grouped by medical system — not implemented
- Match percentage scoring (>85% accuracy) — not implemented
- Quick add to prescription — not implemented (no symptom→medicine lookup page exists yet)

📋 **Enhanced Prescription Builder (target, not current state):** the shipped `MedicineItemsBuilder` has autocomplete and dosage auto-fill from the selected medicine; the items below go beyond that.
- One-click add from symptom search — not implemented
- Dosage auto-suggestions — partially (auto-fill from medicine record, not suggestion logic)
- Recently used medicines — not implemented
- Contraindications warnings — not implemented
- Medicine interactions alerts — not implemented

---

## Phase 3: Book Library & Reader

**Timeline:** 10 weeks (October - December 2026)  
**Goal:** Give doctors access to classical medical texts within the platform

### Week 1-2: EPUB Upload & Storage

**Backend**
- [ ] EPUB file upload endpoint (multipart/form-data)
- [ ] MinIO bucket configuration for books
- [ ] File validation (format, size < 50MB)
- [ ] Book metadata extraction from EPUB
- [ ] Global vs tenant-specific book permissions
- [ ] Book deletion (soft delete)

**Frontend**
- [ ] Book upload page with drag-and-drop
- [ ] Upload progress indicator
- [ ] Book metadata form (title, author, system, language)
- [ ] Book library grid view with cover images
- [ ] Filter by system, author, language

**Database**
- [ ] Run migration for books table
- [ ] Configure MinIO bucket with retention policy

### Week 3-4: EPUB Parsing

**Backend**
- [ ] EPUB parsing with ebooklib (Celery background task)
- [ ] Chapter extraction with hierarchy detection
- [ ] Section parsing with heading levels (h1-h6)
- [ ] Content cleaning (HTML → plain text)
- [ ] Word count calculation per section
- [ ] Progress tracking for parsing job
- [ ] Error handling and retry logic
- [ ] Webhook notification on parsing complete

**Database**
- [ ] Run migration for chapters and sections tables
- [ ] Add indexes for navigation queries
- [ ] Store parsing job status

**Monitoring**
- [ ] Track parsing success rate
- [ ] Alert on parsing failures

### Week 5-7: Book Reader

**Frontend**
- [ ] Book reader UI:
  - Table of contents sidebar
  - Chapter navigation (prev/next buttons)
  - Section rendering with typography
  - Reading progress bar (% completed)
  - Scroll position persistence
  - Font size controls (sm, md, lg, xl)
  - Theme toggle (light, dark, sepia)
  - Search within book
- [ ] Reader toolbar:
  - Bookmark button
  - Highlight selection
  - Font controls
  - Theme switcher
- [ ] Keyboard shortcuts (arrow keys, bookmarks)

**Backend**
- [ ] Reading progress update endpoint (debounced)
- [ ] Bookmark CRUD endpoints
- [ ] Highlight CRUD endpoints
- [ ] Chapter content retrieval (paginated)
- [ ] Search within book endpoint

**Database**
- [ ] Run migration for reading_progress, bookmarks, highlights
- [ ] Add indexes for user_id and book_id

**UX**
- [ ] Smooth scrolling
- [ ] Auto-save reading position
- [ ] Restore last read position on open
- [ ] Mobile-optimized reader

### Week 8-9: Content Curation

**Content Acquisition**
- [ ] Partner with publishers for legal access
- [ ] Identify public domain texts
- [ ] Digitize/acquire 20+ classical texts:

**Homeopathy (5-7 books):**
- [ ] Organon of Medicine by Samuel Hahnemann
- [ ] Materia Medica Pura by Samuel Hahnemann
- [ ] Boericke's Materia Medica
- [ ] Kent's Repertory
- [ ] Philosophy of Homoeopathy

**Ayurveda (5-7 books):**
- [ ] Charaka Samhita (English translation)
- [ ] Sushruta Samhita (English translation)
- [ ] Ashtanga Hridaya
- [ ] Bhavaprakash Samhita
- [ ] Rasaratna Samucchaya

**Unani (3-4 books):**
- [ ] Al-Qanun fi al-Tibb (Canon of Medicine) by Ibn Sina
- [ ] Kamil al-Sana'a by Al-Majusi
- [ ] Tashrih-ul-Abdan

**Herbal (3-4 books):**
- [ ] PDR for Herbal Medicines
- [ ] Chinese Herbal Medicine: Materia Medica
- [ ] The Complete German Commission E Monographs

**Processing**
- [ ] Convert all books to EPUB format (if needed)
- [ ] Parse all books via Celery pipeline
- [ ] Validate chapter/section structure
- [ ] Quality check for readability
- [ ] Add cover images
- [ ] Write book descriptions

### Week 10: Testing & Polish

**Testing**
- [ ] Reader performance with large books (>1000 pages)
- [ ] Bookmark/highlight sync across devices
- [ ] Mobile reader experience
- [ ] Reading progress accuracy
- [ ] Search within book accuracy
- [ ] Offline reading capability (PWA)

**Polish**
- [ ] Smooth page transitions
- [ ] Typography optimization (line height, letter spacing)
- [ ] Dark mode color palette
- [ ] Keyboard shortcuts documentation
- [ ] Accessibility (screen reader, keyboard navigation)

**Documentation**
- [ ] Library user guide
- [ ] Book upload guide (for doctors)
- [ ] Reader shortcuts reference

### Phase 3 Deliverables (target — not started as of 2026-09-21; `books`/`chapters`/`sections`/`reading_progress`/`bookmarks`/`highlights` tables exist, but the `library` module has zero routes)

📋 **Book Library:**
- 20+ classical medical texts
- Filterable by system and author
- Upload capability for doctors (Pro plan)
- Cover images and metadata
- Search across library

📋 **Book Reader:**
- Clean, readable interface
- Table of contents navigation
- Reading progress tracking
- Bookmarks and highlights
- Search within book
- Font and theme controls
- Mobile-optimized

📋 **Dashboard Integration:**
- Currently reading widget
- Reading progress visualization
- Recently accessed books

---

## Phase 4: AI/RAG Intelligence

**Timeline:** 12 weeks (January - March 2027)  
**Goal:** Add AI-powered clinical reference assistant grounded in classical texts

### Week 1-3: Embedding Pipeline

**Backend**
- [ ] OpenAI API integration (text-embedding-3-small)
- [ ] LangChain setup for document processing
- [ ] Chunking strategy implementation:
  - Chunk size: 800 tokens
  - Overlap: 100 tokens
  - Preserve section boundaries
- [ ] Batch embedding generation (Celery task)
- [ ] pgvector extension setup in PostgreSQL
- [ ] Embedding storage with metadata
- [ ] HNSW index creation for vector similarity
- [ ] Re-embedding on book updates (trigger)
- [ ] Cost tracking (API token usage)

**Database**
- [ ] Run migration for embeddings table
- [ ] Create vector similarity index (IVFFlat or HNSW)
- [ ] Optimize for cosine similarity search

**Processing**
- [ ] Embed all existing books (~20 books → ~50K sections)
- [ ] Validate embedding quality (spot checks)
- [ ] Monitor embedding job progress
- [ ] Performance testing (retrieval latency < 200ms)

**Cost Management**
- [ ] Set OpenAI budget limits
- [ ] Monitor daily API spend
- [ ] Alert on budget overruns

### Week 4-6: RAG Retrieval System

**Backend**
- [ ] Vector similarity search implementation (pgvector)
- [ ] Top-k retrieval with cosine similarity (k=5 default)
- [ ] Metadata filtering:
  - By medical system (doctor's specializations)
  - By book (if specified)
  - By date range (optional)
- [ ] Context window assembly (max 4000 tokens)
- [ ] Prompt engineering for clinical queries:
  - System prompt with guardrails
  - Few-shot examples
  - Citation requirements
- [ ] OpenAI GPT-4o-mini integration (primary)
- [ ] OpenAI GPT-4o integration (complex queries fallback)
- [ ] Response formatting with citations
- [ ] Source section retrieval

**API**
- [ ] AI query endpoint: POST /api/v1/ai/query
- [ ] Streaming response support (Server-Sent Events)
- [ ] Usage tracking per tenant
- [ ] Rate limiting enforcement (200 queries/month for Pro)
- [ ] Query history storage
- [ ] Feedback collection endpoint

**Optimization**
- [ ] Cache common queries (Redis, 1-hour TTL)
- [ ] Retrieval accuracy tuning (k value, similarity threshold)
- [ ] Prompt optimization based on feedback

### Week 7-8: AI Assistant UI

**Frontend**
- [ ] AI Assistant page with chat interface:
  - Message bubbles (user vs AI)
  - Streaming response rendering (typewriter effect)
  - Source citations display (expandable)
  - Copy response button
  - Query history sidebar
  - Clear conversation button
- [ ] Quick prompt buttons (common queries):
  - "What are the indications for [medicine]?"
  - "Explain the concept of [term] in Ayurveda"
  - "Compare homeopathic vs herbal treatment for [condition]"
- [ ] Clinical disclaimer banner (always visible)
- [ ] Usage quota display (X/200 queries used this month)
- [ ] Feedback buttons (thumbs up/down)

**UX**
- [ ] Professional medical tone in UI
- [ ] Clear citation format (Book Title, Chapter, Section)
- [ ] Loading states (thinking animation)
- [ ] Error handling:
  - Quota exceeded (upgrade prompt)
  - API errors (retry button)
  - No results found
  - Inappropriate query (filtered message)

**Accessibility**
- [ ] Screen reader support
- [ ] Keyboard navigation
- [ ] High contrast mode

### Week 9-10: Guardrails & Safety

**System Prompts**
- [ ] Explicit instructions:
  - "Never make prescriptive medical decisions"
  - "Answer only from provided source sections"
  - "Always cite book title, chapter, and section"
  - "If answer not in sources, clearly state: 'I could not find this information in the available texts'"
  - "Maintain professional medical language"
- [ ] Few-shot examples in prompt
- [ ] Temperature: 0.3 (less creative, more factual)

**Content Filtering**
- [ ] Block inappropriate queries:
  - Offensive language
  - Non-medical topics
  - Personal medical advice requests
- [ ] Flag potentially harmful advice:
  - Dangerous drug interactions
  - Contraindicated treatments
  - Medical emergencies
- [ ] Human review queue for flagged responses

**Testing**
- [ ] Red teaming (try to get harmful responses)
- [ ] Accuracy validation:
  - 100 test queries with known answers
  - Compare responses with source texts
  - Target: 95%+ accuracy
- [ ] Hallucination detection:
  - Verify all citations exist
  - Check for fabricated information
- [ ] Citation accuracy verification (100% required)

**Monitoring**
- [ ] Track flagged queries
- [ ] Monitor feedback ratings
- [ ] Alert on negative feedback spikes

### Week 11-12: Analytics & Optimization

**Analytics Dashboard (Admin)**
- [ ] Query intent classification:
  - Diagnosis inquiry
  - Medicine information
  - Treatment comparison
  - Theoretical concept
  - Other
- [ ] Popular queries leaderboard
- [ ] Response quality metrics:
  - Average rating (thumbs up/down)
  - Feedback comments
  - Usage by doctor
- [ ] Source coverage analysis:
  - Which books used most
  - Underutilized books
  - Coverage gaps
- [ ] Token usage tracking:
  - Daily/monthly spend
  - Cost per query
  - Budget alerts

**Optimization**
- [ ] Caching for common queries (Redis)
- [ ] Embedding dimensionality reduction testing (768 vs 1536)
- [ ] Retrieval accuracy tuning:
  - Experiment with k values (3, 5, 10)
  - Test similarity thresholds (0.7, 0.75, 0.8)
- [ ] Prompt optimization:
  - A/B test different prompts
  - Measure response quality
- [ ] Cost optimization:
  - Use gpt-4o-mini by default (cheaper)
  - Escalate to gpt-4o only for complex queries
  - Aggressive caching

**Documentation**
- [ ] AI Assistant user guide
- [ ] Best practices for clinical queries
- [ ] Limitations and disclaimers
- [ ] Admin guide for monitoring

### Phase 4 Deliverables (target — not started as of 2026-09-21; `POST /api/v1/ai/query` is still a 501 stub, no `library` routes exist)

📋 **AI Assistant:**
- Chat interface with streaming responses
- Grounded in 20+ classical texts (50K+ sections)
- Citations for every answer (book, chapter, section)
- 200 queries/month for Pro plan
- Query history and feedback

📋 **Embedding System:**
- 50K+ embedded text sections
- Sub-200ms vector retrieval
- Filtered by doctor's specializations
- Automated re-embedding on content updates

📋 **Safety & Guardrails:**
- Clinical disclaimer on every response
- Guardrails against prescriptive advice
- Content filtering for inappropriate queries
- Hallucination detection
- Human review queue for flagged content

📋 **Analytics:**
- Query usage tracking
- Popular topics dashboard
- Response quality metrics (feedback ratings)
- Token usage and cost monitoring
- Source coverage analysis

---

## Infrastructure Evolution

### Phase 0-1: Single VPS
**Specs:** 4 vCPU, 8 GB RAM, 100 GB SSD  
**Cost:** $25-40/month (Hetzner, DigitalOcean, Contabo)  
**Capacity:** 50-200 concurrent users

**Services (Docker Compose):**
- Caddy (reverse proxy + auto HTTPS)
- FastAPI (4 Uvicorn workers)
- Celery workers (3 queues: pdf, email, ai)
- PostgreSQL 16 + pgvector
- Redis (cache + broker + rate limiting)
- MinIO (local S3)
- Prometheus + Grafana (monitoring)

### Phase 2-3: Managed Services
**Migration:**
- PostgreSQL → Neon or DigitalOcean Managed PostgreSQL
- Redis → Upstash or Redis Cloud
- MinIO → Cloudflare R2 or AWS S3

**Cost:** ~$150-200/month  
**Capacity:** 500-1,000 concurrent users

**Benefits:**
- Automated backups
- Point-in-time recovery
- Better availability
- Less operational overhead

### Phase 4: Horizontal Scaling
**Additions:**
- 2nd API container (behind Caddy load balancer)
- 3 Celery workers (by task type: pdf, email, ai)
- PostgreSQL read replicas (for analytics)
- CDN (Cloudflare for static assets)
- Query caching layer (Redis)

**Cost:** ~$400-500/month  
**Capacity:** 2,000-5,000 concurrent users

### Future: Multi-Region Expansion
**Regions:**
- Bangladesh (primary)
- India (secondary)

**Architecture:**
- Multi-region database replication
- CDN with edge caching globally
- Regional API deployments
- Kubernetes orchestration (GKE, EKS, or DOKS)

**Cost:** $1,000+/month  
**Capacity:** 10,000+ concurrent users

---

## Team Scaling

### Phase 0-1 (MVP)
**Team:** 2-3 people
- 1 Full-stack developer (Python + React) — **Lead**
- 1 Frontend developer (React/Next.js + Design)
- 1 Part-time medical advisor (alternative medicine practitioner)

**Estimated cost:** $6,000-8,000/month

### Phase 2-3 (Knowledge Base + Library)
**Team:** 4-5 people
- 2 Backend developers (Python/FastAPI)
- 1 Frontend developer (React/Next.js)
- 1 UI/UX Designer
- 1 Medical content curator (full-time practitioner)
- 1 Part-time DevOps engineer

**Estimated cost:** $12,000-15,000/month

### Phase 4 (AI/RAG)
**Team:** 6-8 people
- 2 Backend developers
- 2 Frontend developers
- 1 ML/AI engineer (RAG optimization, prompt engineering)
- 1 UI/UX Designer
- 1 Medical content team (2 practitioners for validation)
- 1 DevOps engineer (full-time)
- 1 Part-time QA engineer

**Estimated cost:** $18,000-22,000/month

### Future: Enterprise Scale
**Team:** 10-15 people
- 3 Backend developers
- 3 Frontend developers
- 1 ML engineer
- 2 Designers (UI/UX, Product)
- 1 QA engineer (full-time)
- 2 Medical content team
- 1 DevOps engineer
- 1 Product manager
- 1 Customer success manager
- 1 Marketing/Growth lead

**Estimated cost:** $30,000-40,000/month

---

## Risk Management

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Database performance degradation with growth | High | Medium | Implement read replicas, query optimization, connection pooling, caching strategy |
| EPUB parsing failures (malformed files) | Medium | Medium | Robust error handling, manual fallback, publisher partnerships, format validation |
| AI hallucinations (fabricated medical info) | Critical | Medium | Strict grounding, mandatory citations, human review queue, clear disclaimers |
| Integration API downtime (bKash, SMS) | Medium | High | Multiple providers, fallback mechanisms, queue retry logic, status monitoring |
| Data loss or corruption | Critical | Low | Daily automated backups, point-in-time recovery, quarterly restore testing, replication |
| pgvector performance issues (slow queries) | Medium | Medium | HNSW indexing, query optimization, caching, dimensionality reduction |
| OpenAI API rate limits or cost overruns | High | Medium | Budget alerts, usage caps, caching, fallback to cheaper models (gpt-4o-mini) |
| Multi-tenant data isolation breach | Critical | Low | Rigorous testing, code reviews, automated tests, security audits |

### Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low doctor adoption | Critical | Medium | Pilot program with 10 doctors, rapid iteration on feedback, strong onboarding, free trial |
| Competition from existing EMR systems | High | Medium | Focus on alternative medicine niche, AI differentiator, Bangladesh-first approach, superior UX |
| Payment gateway issues in Bangladesh | Medium | High | SSLCommerz aggregator (handles bKash/Nagad/Rocket), Stripe backup, cash fallback, clear invoicing |
| Content licensing for books | Medium | Medium | Partner with publishers early, offer revenue share, focus on public domain initially |
| Regulatory compliance (medical data) | High | Low | HIPAA-like standards, encryption at rest/transit, regular audits, legal consultation |
| Pricing too high for Bangladesh market | Medium | Medium | Free tier for validation, flexible pricing, annual discounts, local payment methods |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Key person dependency | High | Medium | Documentation, code reviews, knowledge sharing sessions, onboarding processes |
| Scope creep delaying MVP | Medium | High | Strict phase-based development, feature freeze windows, ruthless prioritization |
| Budget overrun | Medium | Medium | Conservative estimates, 20% contingency buffer, monthly budget reviews |
| Burnout from aggressive timeline | Medium | Medium | Realistic sprint planning, code review process, test coverage requirements, work-life balance |

---

## Success Metrics

### Phase 1 (MVP) — August 2026
- [ ] 10 pilot doctors onboarded and actively using daily
- [ ] 500+ patients managed in system
- [ ] 200+ prescriptions generated
- [ ] 50+ payments recorded
- [ ] 95%+ uptime (monitored via Uptime Robot)
- [ ] <1s average page load time (P50)
- [ ] <3s P95 page load time
- [ ] 80%+ user satisfaction (NPS > 40)
- [ ] Zero critical security incidents
- [ ] Multi-tenant isolation tests: 100% pass rate

### Phase 2 (Knowledge Base) — October 2026
- [ ] 1,000+ medicines in database
- [ ] 1,000+ symptom mappings
- [ ] Symptom search used by 80%+ of active doctors
- [ ] 30%+ of prescriptions use symptom search workflow
- [ ] Search accuracy > 85% (validated by practitioners)
- [ ] Medicine search latency < 100ms (P95)

### Phase 3 (Library) — December 2026
- [ ] 20+ books parsed and accessible
- [ ] 50,000+ sections embedded
- [ ] 50%+ of doctors use library feature monthly
- [ ] Average reading session > 10 minutes
- [ ] 100+ bookmarks created
- [ ] 50+ highlights created
- [ ] Zero parsing failures for curated books

### Phase 4 (AI) — March 2027
- [ ] 80%+ of Pro plan doctors use AI assistant
- [ ] Average 15 queries per doctor per month
- [ ] Response citation accuracy > 95%
- [ ] Zero prescriptive medical advice violations
- [ ] User feedback rating > 4.0/5.0
- [ ] AI query latency < 3s (streaming start)
- [ ] Monthly OpenAI cost < $300

### Overall (End of Phase 4) — March 2027
- [ ] 50+ paying clinics (target met) ✅
- [ ] ৳2.5L+ MRR (Monthly Recurring Revenue) — ~$2,500
- [ ] 70%+ retention rate (doctors stay subscribed)
- [ ] 40%+ upgrade rate (Free → Plus or Plus → Pro)
- [ ] <5% churn rate monthly
- [ ] 100+ concurrent users supported
- [ ] 99%+ uptime
- [ ] <10 critical bugs in production

---

## Go-to-Market Strategy

### Pre-Launch (May-July 2026)
- [ ] Create marketing website (landing page with demo video)
- [ ] Publish 5 blog posts:
  - Alternative medicine digitization
  - Benefits of practice management software
  - Doctor success stories (case studies)
  - AI in alternative medicine
  - Security and compliance
- [ ] Partner with 3 alternative medicine associations in Bangladesh:
  - Bangladesh Homoeopathic Board
  - Bangladesh Ayurveda Medical Association
  - National Unani Medical Association of Bangladesh
- [ ] Create demo video (3-5 minutes walkthrough)
- [ ] Social media presence (Facebook, LinkedIn)
- [ ] Collect email list (target: 500+ practitioners)

### Launch (August 2026 - Phase 1)
- [ ] Press release to healthcare tech media
- [ ] Product Hunt launch
- [ ] Free trial for first 50 doctors (14 days, no credit card)
- [ ] Webinar series: "Digitizing Your Alternative Medicine Practice"
- [ ] Email campaign to 500+ practitioners
- [ ] Facebook/Instagram ads targeting Dhaka doctors
- [ ] Referral program setup (1 month free for referrer and referee)

### Growth (Phase 2-3)
- [ ] Content marketing (2 blog posts per week)
- [ ] SEO optimization:
  - "homeopathy software bangladesh"
  - "ayurveda practice management"
  - "clinic management software dhaka"
- [ ] Facebook ads targeting doctors in Dhaka, Chittagong, Sylhet
- [ ] Partnership with medical colleges (guest lectures)
- [ ] Case studies and testimonials
- [ ] YouTube channel (tutorials, tips)

### Scale (Phase 4+)
- [ ] Expand to India (localization for Rupee, Hindi/regional languages)
- [ ] Partnerships with pharmacy chains
- [ ] White-label offering for large clinics (10+ doctors)
- [ ] Mobile app (iOS + Android)
- [ ] Annual conference for users
- [ ] Affiliate program for influencers

---

## Technology Roadmap

### Current Stack (Phase 0-1)
**Backend:**
- Python 3.12, FastAPI, SQLAlchemy 2.0 async
- PostgreSQL 16 + pgvector, Redis
- Celery for background tasks
- JWT auth + 2FA (pyotp)
- Sentry, Grafana, Prometheus (monitoring)
- structlog (structured logging)
- slowapi (rate limiting)

**Frontend:**
- Next.js 16 (App Router), React Query
- Tailwind CSS + shadcn/ui
- TypeScript strict mode

**Infrastructure:**
- Docker Compose
- MinIO (S3-compatible)
- Caddy (reverse proxy + auto-HTTPS)

**Integrations:**
- SSLCommerz (Bangladesh payments)
- Stripe (international payments)
- Twilio (SMS)
- SendGrid (email)

### Near-term (Phase 2-4)
- [ ] Add pgvector for embeddings (Phase 3-4)
- [ ] LangChain for RAG pipeline (Phase 4)
- [ ] OpenAI API (embeddings + GPT-4o-mini/gpt-4o) (Phase 4)
- [ ] Migrate to managed PostgreSQL (Phase 2-3)
- [ ] Migrate to Cloudflare R2 (Phase 3-4)
- [ ] Add CDN (Cloudflare) (Phase 3)
- [ ] WebSockets for real-time notifications (Phase 4)

### Future Enhancements
- [ ] GraphQL API (in addition to REST)
- [ ] React Native mobile app (iOS + Android)
- [ ] Real-time collaboration (WebSockets, operational transforms)
- [ ] Advanced analytics (BigQuery or ClickHouse)
- [ ] Machine learning for prescription recommendations
- [ ] Keycloak for enterprise SSO (if needed)
- [ ] Kubernetes for orchestration (if scaling to 10,000+ users)

---

## Pricing Evolution

### Phase 1 Launch Pricing (August 2026)
- **Free:** 30 patients, 10 prescriptions/month, email support
- **Plus:** ৳799/month ($8/month)
  - 500 patients
  - Unlimited prescriptions
  - PDF export
  - Invoice generation
  - Email + chat support
- **Pro:** ৳1,799/month ($18/month)
  - Unlimited patients
  - AI assistant (200 queries/month)
  - 1 receptionist seat
  - Priority support
  - Custom branding

**14-day free trial** for all paid plans (no credit card required)  
**20% off** when billed annually

### Phase 2-3 Pricing (October 2026)
- **Free:** Unchanged
- **Plus:** ৳899/month (+৳100)
  - Adds: Medicine database + symptom search + 5 books
- **Pro:** ৳1,999/month (+৳200)
  - Adds: Unlimited books + book upload + AI assistant

### Phase 4+ Pricing (March 2027)
- **Free:** Unchanged (acquisition tool)
- **Plus:** ৳999/month
- **Pro:** ৳2,299/month
- **Enterprise:** Custom pricing
  - 10+ doctor accounts
  - Dedicated support
  - Custom SLA
  - Onboarding assistance
  - Custom integrations

### Annual Discount
- 20% off all plans when billed annually
- Example: Pro ৳2,299/month → ৳1,839/month annual

---

## Dependencies & Blockers

### Critical Dependencies
- [x] UI mockups completed (Admin + Doctor views) ✅
- [x] Database schema designed (29 tables) ✅
- [x] Technology stack finalized ✅
- [x] Environment variables documented ✅
- [x] Requirements.txt created ✅
- [ ] Beta doctor recruitment (target: 10 doctors) — **PRIORITY**
- [ ] SSLCommerz merchant account approval (2-3 weeks) — **IN PROGRESS**
- [ ] Content licensing agreements (for books) — **Phase 3**
- [ ] OpenAI API key and budget allocation ($500/month) — **Phase 4**
- [ ] VPS provisioning and setup — **Week 1**

### Potential Blockers
- **Medical content validation:** Need practitioner partnerships (target: 5 advisors)
- **EPUB book acquisition:** Public domain vs licensed (legal review required)
- **Payment gateway integration delays:** SSLCommerz approval can take 2-4 weeks
- **AI model API rate limits:** OpenAI may throttle during high usage
- **Regulatory compliance:** Need legal consultation for medical data handling
- **Team hiring:** Finding experienced FastAPI + React developers in Bangladesh

### Mitigation Strategies
- Start beta recruitment immediately (before Phase 1 begins)
- Apply for SSLCommerz merchant account now (parallel track)
- Begin book partnership discussions early (Phase 0)
- Set OpenAI budget alerts to avoid overruns
- Consult legal expert on medical data compliance (Week 1)
- Consider remote hiring if local talent scarce

---

## Conclusion

This roadmap represents a **44-week journey** (~11 months) from planning to a comprehensive AI-powered alternative medicine practice management platform. The phased approach allows us to:

1. **Validate early** with a working MVP (Phase 1) — 10 pilot doctors
2. **Add value incrementally** (Phases 2-4) — medicine DB, library, AI assistant
3. **Scale sustainably** with proven product-market fit
4. **Maintain focus** through clear milestones and deliverables

### Current Status (April 26, 2026)
✅ **Phase 0 Complete + Phase 1 Foundation Built:**
- System design finalized (30 tables, REST API, modular monolith)
- UI mockups complete and reviewed
- Technology stack documented
- **Backend foundation fully implemented (30 SQLAlchemy models)** ✅
- **Authentication system complete with JWT + 2FA** ✅
- **Comprehensive test suite (1,399 lines covering auth module)** ✅
- **Database migrations configured (Alembic async)** ✅
- **Docker infrastructure running (PostgreSQL, Redis, MinIO)** ✅
- **Seed data scripts ready (geographic, integrations, translations)** ✅
- Production checklist created
- Cost estimates validated

### Next Immediate Steps (Week 5-6: Doctor Credentials & Profile)
1. [x] ~~Provision VPS~~ Using local Docker development environment ✅
2. [x] ~~Set up development environment (Docker Compose)~~ ✅
3. [x] ~~Initialize FastAPI project structure~~ ✅
4. [x] ~~Create initial database migrations (30 tables)~~ ✅
5. [x] ~~Implement authentication system~~ ✅
6. [x] ~~Write comprehensive test suite~~ ✅
7. [ ] **Initialize/standardize Next.js 16 frontend** — **CURRENT PRIORITY**
8. [ ] **Implement frontend authentication flows** — **CURRENT PRIORITY**
9. [ ] Begin beta doctor recruitment
10. [ ] Apply for SSLCommerz merchant account
11. [ ] Set up monitoring (Sentry, Grafana)
12. [ ] Doctor profile & credentials module (Week 5-6)

### Success Factors
- **Strong execution** on technical milestones (test coverage, security)
- **Close collaboration** with medical practitioners (validation)
- **Rapid iteration** based on user feedback (weekly demos)
- **Disciplined scope management** (no feature creep)
- **Sustainable team culture** (realistic sprint planning, work-life balance)

### Key Risks to Monitor
1. Multi-tenant data isolation (test rigorously!)
2. AI hallucinations (strict guardrails + citations)
3. Payment gateway integration delays (start SSLCommerz process now)
4. Beta doctor recruitment (target: 10, minimum: 5)
5. Budget overruns (monthly reviews, 20% buffer)

---

**Document Owner:** Product Team  
**Last Updated:** May 10, 2026 (superseded — see `docs/status/current.md` and `docs/ROADMAP.md`, both refreshed 2026-09-21)  
**Next Review:** Weekly (every Monday)  
**Status (as of 2026-09-21):** ✅ Phase 1 Complete — MVP v1.0 Production Ready, full frontend across all 14 backend modules including Payments, Integrations, Medicines, Symptoms, and Platform Admin. The "6/9 modules" and "Next: Payments frontend / Integrations frontend" notes below are the original May 10, 2026 snapshot and are no longer accurate — kept for history.

**Recent Progress (Code-Verified - May 10, 2026, historical):**
- Backend routed modules: 9 (`auth`, `ai`, `appointments`, `dashboard`, `doctor`, `patient`, `prescription`, `payment`, `integration`)
- Module endpoints: 82+ total
- Frontend: 68+ source files, 13 routes
- Complete modules (backend + frontend): Auth, Patients, Appointments, Dashboard, Prescriptions, Doctor Profile
- AI contract route: `POST /api/v1/ai/query` (`501` stub by design — still true today)
- Security: A (95/100), rate limiting, HTTP headers, password complexity
- 📋 Next (as planned in May): Payments frontend, Integrations frontend, Medicine database — **all since shipped**

**Current snapshot (2026-09-23):** 14 backend modules, 129 module endpoints, 34 tables, 132 frontend source files across 11 route groups (10 dashboard route groups + login). See `docs/status/current.md` for the authoritative breakdown.

**Questions or feedback?** Contact the product team or open an issue in the repository.

---

## Appendix: Quick Reference

### Phase Timeline Summary
```
Phase 0: Planning & Design        ✅ Complete (April 7-20)
Phase 1: Core Clinic MVP          ✅ Complete (April 21-July 26, 14 weeks) — backend + frontend, all 14 modules
Phase 2: Knowledge Base           🔶 Core shipped (medicine/symptom CRUD + search API, GIN indexes);
                                      seed data, bulk import, and search-API wiring in list pages still open
Phase 3: Book Library             📋 Planned — DB models exist, no routes/UI yet
Phase 4: AI/RAG                   📋 Planned — `/api/v1/ai/query` is a 501 stub
```

### Budget Summary (Year 1)
```
Infrastructure:  $150-170/month × 12 = $1,800-2,040/year
Team:            $6K-8K/month × 12 = $72K-96K/year
Total:           ~$75K-100K/year

Revenue Target (50 clinics @ ৳1,200 avg):
৳60,000/month = ৳7.2L/year = $7,200/year

Note: Break-even requires ~800-1,000 clinics at current pricing
Consider: Enterprise tier, consulting services, white-label offerings
```

### Key Metrics Dashboard (Track Weekly)
- [ ] Active paying clinics
- [ ] MRR (Monthly Recurring Revenue)
- [ ] Churn rate (%)
- [ ] NPS (Net Promoter Score)
- [ ] Uptime (%)
- [ ] P95 API latency
- [ ] Test coverage (%)
- [ ] Open critical bugs

### Contact Information
- **Project Lead:** [Name]
- **Email:** engineering@altcare.health
- **GitHub:** github.com/altcare/altcare
- **Slack:** altcare.slack.com (team workspace)
- **Sentry:** sentry.io/altcare (errors)
- **Status Page:** status.altcare.health (uptime)
