# AltCare Documentation Index

**Last Updated:** May 19, 2026  
**Project Status:** MVP v1.0 - Production Ready (7/9 modules complete)

---

## 📚 Primary Documentation

### Getting Started
- **[README.md](README.md)** - Project overview, quick start, feature snapshot
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Detailed setup guide
- **[CLAUDE.md](CLAUDE.md)** - Architecture, conventions, implementation guide (SOURCE OF TRUTH)

### Planning & Roadmap
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Product roadmap, phases, timeline, priorities

### Status Reports
- **[PAYMENTS_COMPLETE.md](PAYMENTS_COMPLETE.md)** - Payments module completion (100%)
- **[PAYMENTS_POLISH_COMPLETE.md](PAYMENTS_POLISH_COMPLETE.md)** - Final polish details (toasts, build fixes)

---

## 🗂️ By Topic

### Architecture & Setup
- [CLAUDE.md](CLAUDE.md) - Full architecture guide
  - Multi-tenant security
  - Database schema (34 tables)
  - Backend module structure (9 modules, 87 endpoints)
  - Frontend structure (90+ files)
  - Authentication & authorization
  - Critical patterns

- [FRONTEND_SETUP.md](FRONTEND_SETUP.md) - Frontend-specific setup
  - Next.js 16 + React 19 configuration
  - TypeScript setup
  - Component library (shadcn/ui)
  - State management (Zustand, React Query)

### Security
- [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) - Security audit results
  - Score: A (95/100)
  - Password complexity
  - Session management
  - Rate limiting
  - HTTP security headers
  - Multi-tenant isolation tests

### Changes & History
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [BREAKING_CHANGES.md](BREAKING_CHANGES.md) - Breaking changes log
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - Code cleanup history

---

## 📦 Module Documentation

### ✅ Complete Modules (Backend + Frontend)

#### 1. Authentication
**Status:** ✅ Complete  
**Features:** Login, 2FA/TOTP, JWT, refresh tokens, password security  
**Routes:** `/login`  
**Endpoints:** 16  
**Docs:** See [CLAUDE.md](CLAUDE.md) section 4.2

#### 2. Patient Management
**Status:** ✅ Complete  
**Features:** CRUD, search, tags, diagnoses, demographics  
**Routes:** `/patients`, `/patients/[id]`, `/patients/new`  
**Endpoints:** 14  
**Docs:** See [CLAUDE.md](CLAUDE.md) section 3.4.3

#### 3. Dashboard Analytics
**Status:** ✅ Complete  
**Features:** Stats, revenue charts, patient demographics  
**Routes:** `/dashboard`  
**Endpoints:** 6  
**Docs:** See [CLAUDE.md](CLAUDE.md) section 3.4.4

#### 4. Appointments
**Status:** ✅ Complete  
**Features:** Calendar view, scheduling, visits, status tracking  
**Routes:** `/appointments`, `/appointments/[id]`, `/appointments/new`  
**Endpoints:** 6  
**Docs:** See [CLAUDE.md](CLAUDE.md) section 3.4.3

#### 5. Prescriptions
**Status:** ✅ Complete  
**Features:** CRUD, builder, medicine items, draft/issue/void workflow  
**Routes:** `/prescriptions`, `/prescriptions/[id]`, `/prescriptions/new`  
**Endpoints:** 8  
**Docs:** See [CLAUDE.md](CLAUDE.md) sections 3.4.6, 4.6

#### 6. Doctor Profile
**Status:** ✅ Complete  
**Features:** Profile, degrees, trainings, clinic info  
**Routes:** `/profile`  
**Endpoints:** 12  
**Docs:** See [CLAUDE.md](CLAUDE.md) section 3.4.4

#### 7. Payments & Billing
**Status:** ✅ Complete (May 19, 2026)  
**Features:** Dashboard, transactions, invoices, payment recording, CSV export  
**Routes:** `/payments`, `/payments/transactions`, `/payments/invoices/*`  
**Endpoints:** 12  
**Docs:** 
- [PAYMENTS_COMPLETE.md](PAYMENTS_COMPLETE.md) - Implementation details
- [PAYMENTS_POLISH_COMPLETE.md](PAYMENTS_POLISH_COMPLETE.md) - Polish details

### 📋 Backend-Only Modules

#### 8. Integrations
**Status:** Backend complete, frontend pending  
**Features:** SMS/Email providers, credential encryption, integration logs  
**Endpoints:** 12  
**Next Priority:** HIGH  
**Estimated:** 4-6 hours frontend

#### 9. AI Query
**Status:** Stub endpoint  
**Features:** Plan-gated, rate limited  
**Endpoints:** 1  
**Status:** Planned

---

## 🏗️ Technical Documentation

### Backend
- **Framework:** FastAPI (async/await)
- **Database:** PostgreSQL 16 + pgvector
- **ORM:** SQLAlchemy 2.0 (AsyncSession)
- **Auth:** JWT (python-jose), Bcrypt, TOTP (pyotp)
- **Tasks:** Celery
- **Migrations:** Alembic
- **Testing:** pytest

### Frontend
- **Framework:** Next.js 16 (App Router)
- **UI:** React 19, TypeScript
- **Styling:** Tailwind CSS 4, shadcn/ui
- **State:** Zustand (client), React Query (server)
- **Forms:** React Hook Form, Zod validation
- **i18n:** next-intl (English/Bengali)
- **Testing:** Playwright

### Infrastructure
- **Containers:** Docker Compose
- **Cache:** Redis 7
- **Storage:** MinIO (S3-compatible)

---

## 📊 Project Metrics

**As of May 19, 2026:**

| Metric | Value |
|--------|-------|
| Modules (Backend) | 9 routed modules |
| Endpoints | 87 API endpoints |
| Database Tables | 34 models |
| Frontend Files | 90+ source files |
| Frontend Routes | 17+ pages |
| Modules Complete (Full Stack) | 7/9 (78%) |
| Security Score | A (95/100) |
| Test Coverage | Multi-tenant isolation 100% |
| Build Status | ✅ Passing |
| Production Status | ✅ Ready |

---

## 🗄️ Archived Documentation

### Feature Completion Reports
- [docs/archive/PAYMENTS_PROGRESS_2026-05-19.md](docs/archive/PAYMENTS_PROGRESS_2026-05-19.md) - Payments progress tracking
- [docs/archive/PAYMENTS_IMPLEMENTATION_PLAN_2026-05-19.md](docs/archive/PAYMENTS_IMPLEMENTATION_PLAN_2026-05-19.md) - Implementation plan

*(Note: Check `docs/archive/` directory for historical documentation)*

---

## 🎯 Quick Reference

### Start Development
```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Key Commands
```bash
# Database migration
alembic upgrade head

# Seed data
./scripts/run_seed.sh

# Run tests
pytest --cov=app

# Frontend build
npm run build
```

---

## 📝 Documentation Maintenance

### When to Update
- ✅ New feature completed → Update CLAUDE.md, README.md, ROADMAP.md
- ✅ Architecture changes → Update CLAUDE.md
- ✅ Security updates → Update SECURITY_AUDIT_REPORT.md
- ✅ Breaking changes → Update BREAKING_CHANGES.md
- ✅ Version releases → Update CHANGELOG.md

### Update Checklist
When completing a new module:
1. [ ] Update [CLAUDE.md](CLAUDE.md) - Add to implemented list
2. [ ] Update [README.md](README.md) - Update feature list
3. [ ] Update [docs/ROADMAP.md](docs/ROADMAP.md) - Mark complete
4. [ ] Create completion report (e.g., MODULE_COMPLETE.md)
5. [ ] Update this index
6. [ ] Archive progress docs to `docs/archive/`

---

## 🔗 External Resources

### GitHub
- Repository: (Add your repo URL here)
- Issues: (Add issues URL here)
- Discussions: (Add discussions URL here)

### Deployment
- Production: (Add production URL here)
- Staging: (Add staging URL here)

---

## 📞 Support

For questions or issues:
1. Check [CLAUDE.md](CLAUDE.md) for architecture details
2. Review [GETTING_STARTED.md](GETTING_STARTED.md) for setup help
3. Check [docs/ROADMAP.md](docs/ROADMAP.md) for planned features
4. Create a GitHub issue

---

**Document Maintained By:** Development Team  
**Last Major Update:** May 19, 2026  
**Next Review:** June 1, 2026
