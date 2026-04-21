# AltCare — Alternative Medicine Practice Management System

> A multi-tenant SaaS platform for Homeopathy, Ayurveda, Unani, and Herbal practitioners to manage patients, prescriptions, payments, clinical knowledge, and AI-assisted reference — all in one place.

**🎯 Status:** Backend foundation complete ✅ | Phase 1 Week 1-2 of 14 | [View Full Status](docs/status/current.md)

---

## 🌟 Overview

AltCare is a comprehensive **clinic operating system** built specifically for alternative medicine practitioners. It combines:

- 📋 **Patient Management** - Complete records, visit history, tags, diagnoses
- 💊 **Prescription System** - Builder with PDF export, medicine database
- 💳 **Payment Tracking** - bKash, Nagad, Rocket, card support with invoicing
- 📚 **Medical Library** - EPUB reader with bookmarks and highlights
- 🤖 **AI Assistant** - RAG-powered clinical reference (Phase 4)
- 🌍 **Bilingual** - Full English/Bengali interface

**Key Differentiators:**
- **Multi-specialization** - Supports 1-4 systems (Homeopathy, Ayurveda, Unani, Herbal)
- **Bangladesh-focused** - Division → District → Upazila with Bengali names
- **Multi-tenant SaaS** - Fully isolated data per clinic
- **Complete audit trail** - All transactions logged

---

## 🚀 Quick Start

### For Developers

```bash
# Clone repository
git clone https://github.com/your-org/alternative-care.git
cd alternative-care

# Run automated setup
cd backend && ./quick_start.sh

# Access API documentation
open http://localhost:8000/docs
```

**→ Full guide:** [GETTING_STARTED.md](GETTING_STARTED.md)

### For Stakeholders

- **Project Roadmap:** [docs/planning/roadmap.md](docs/planning/roadmap.md)
- **Current Status:** [docs/status/current.md](docs/status/current.md)
- **UI Prototypes:** [mock/doctor-view.html](mock/doctor-view.html) (open in browser)

---

## 📊 Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **Backend Foundation** | ✅ Complete | 30 models, auth, infrastructure |
| **API Endpoints** | 📋 Next | Authentication module in progress |
| **Frontend** | 📋 Planned | Week 5-6 (Next.js + TypeScript) |
| **Database** | ✅ Ready | PostgreSQL 16 + pgvector |
| **Infrastructure** | ✅ Running | Docker (PostgreSQL, Redis, MinIO) |

**Progress:** 12% complete (Phase 1, Week 1-2 of 14)

**→ Detailed status:** [docs/status/current.md](docs/status/current.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 Frontend (Tailwind + shadcn/ui)    │
│  English/Bengali • Patient • Prescription • $   │
└──────────────────────┬──────────────────────────┘
                       │ REST API + JWT
┌──────────────────────▼──────────────────────────┐
│  FastAPI Backend (Python 3.12 • Async)         │
│  Multi-tenant • RBAC • 2FA • Plan Limits       │
└──┬───────────┬──────────┬────────────┬─────────┘
   │           │          │            │
┌──▼──┐  ┌────▼─────┐ ┌──▼────┐ ┌─────▼────────┐
│ PG  │  │  Redis   │ │ MinIO │ │ Celery       │
│16+  │  │  Cache   │ │ S3    │ │ PDF/Email/AI │
│pgvec│  │  +Queue  │ │ Files │ │ Workers      │
└─────┘  └──────────┘ └───────┘ └──────────────┘
```

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16 + pgvector
- Frontend: Next.js 14 + Tailwind + shadcn/ui + React Query
- Infrastructure: Docker + Redis + MinIO + Celery

**→ Full architecture:** [docs/architecture/overview.md](docs/architecture/overview.md)  
**→ Database schema:** [docs/architecture/database.md](docs/architecture/database.md) (30 tables)

---

## ✨ Key Features

### Multi-Tenant SaaS
- Row-level data isolation per clinic
- Automatic tenant filtering (ContextVar)
- Platform admin + tenant-scoped users

### Authentication & Security
- JWT access + refresh tokens
- TOTP-based 2FA with QR codes
- Bcrypt password hashing
- Role-based access control (Admin, Operator, Doctor, Receptionist)
- Plan-based feature gating (Free, Plus, Pro)

### Bilingual Support (EN/BN)
- All content models have `_en` and `_bn` fields
- Translation table for UI strings
- Bangladesh geographic data in Bengali
- Language switcher in UI

### Integration Framework
- SMS providers: Twilio, Banglalink, Robi
- Email providers: SendGrid, AWS SES
- Payment gateways: bKash, Nagad, Rocket, Stripe
- Encrypted credentials (Fernet)
- Full audit logging

### Database (30 Tables)
- **Core:** tenants, users, user_sessions
- **Doctor:** degrees, trainings (with verification)
- **Geographic:** divisions, districts, upazilas (Bangladesh)
- **Patient:** patients, tags, diagnoses
- **Prescription:** prescriptions, items (supports free-text)
- **Payment:** payments, invoices
- **Medicine:** medicines, symptoms (bilingual catalog)
- **Library:** books, chapters, sections, embeddings (RAG ready)
- **Integration:** providers, configs, logs
- **System:** translations, usage_tracking

---

## 📋 Roadmap

### Phase 1: Core Clinic MVP (14 weeks, May-July 2026)
- ✅ Week 1-2: Backend foundation (COMPLETE)
- 🔄 Week 3-4: Authentication & User Management
- 📋 Week 5-6: Doctor Profile & Credentials
- 📋 Week 7-8: Patient Management
- 📋 Week 9-10: Prescription System
- 📋 Week 11: Payment & Invoicing
- 📋 Week 12: Dashboard & Analytics
- 📋 Week 13: Integration Framework
- 📋 Week 14: Testing & Launch

**Target Launch:** August 1, 2026

### Phase 2-4 (Aug 2026 - Mar 2027)
- **Phase 2:** Knowledge Base (Medicine database + symptom search)
- **Phase 3:** Book Library (EPUB reader + progress tracking)
- **Phase 4:** AI/RAG (Clinical reference assistant)

**→ Full roadmap:** [docs/planning/roadmap.md](docs/planning/roadmap.md)  
**→ Detailed roadmap:** [docs/planning/roadmap-detailed.md](docs/planning/roadmap-detailed.md)

---

## 💻 Development

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Node.js 18+ (for frontend, coming soon)

### Setup
```bash
# Quick setup (recommended)
cd backend && ./quick_start.sh

# Manual setup
See GETTING_STARTED.md for detailed instructions
```

### Development Commands
```bash
# Start infrastructure
docker compose up -d

# Start backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

**→ Developer guide:** [docs/development/setup.md](docs/development/setup.md)  
**→ Code examples:** [docs/development/quick-reference.md](docs/development/quick-reference.md)

---

## 📚 Documentation

**Start here:** [docs/README.md](docs/README.md) - Complete documentation map

### Quick Links
- **[Getting Started](GETTING_STARTED.md)** - Setup in 30 minutes
- **[Current Status](docs/status/current.md)** - What's done, what's next
- **[Architecture](docs/architecture/overview.md)** - System design
- **[Database Schema](docs/architecture/database.md)** - All 30 tables
- **[Roadmap](docs/planning/roadmap.md)** - Development plan
- **[API Docs](http://localhost:8000/docs)** - Swagger UI (when running)

### By Role
- **Developers:** [docs/development/](docs/development/)
- **Architects:** [docs/architecture/](docs/architecture/)
- **Planners:** [docs/planning/](docs/planning/)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/unit/test_auth.py -v
```

**Test Coverage Target:** 80%+  
**Critical Coverage:** 100% for auth, payment, multi-tenant isolation

---

## 📦 Tech Stack

### Backend
- **FastAPI** - Async Python web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL 16** - Database with pgvector
- **Alembic** - Database migrations
- **Redis** - Cache + Celery broker
- **Celery** - Background tasks (PDF, email, AI)
- **WeasyPrint** - PDF generation
- **pyotp** - 2FA (TOTP)

### Frontend (Coming Soon)
- **Next.js 14** - React framework (App Router)
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Query** - Server state
- **next-intl** - i18n (EN/BN)

### Infrastructure
- **Docker** - Containerization
- **MinIO** - S3-compatible storage
- **Caddy** - Reverse proxy (production)
- **GitHub Actions** - CI/CD

**→ Full stack details:** [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md)

---

## 📸 Screenshots

> UI prototypes in [`/mock/`](./mock/) - Open in browser, no build required

- **[Doctor View](./mock/doctor-view.html)** - Clinic management interface
- **[Admin View](./mock/admin-view.html)** - Platform administration
- **[Marketing Page](./mock/marketing-landing.html)** - Landing page

**Screens:** Dashboard, Patients, Prescriptions, Payments, Medicines, Library, AI Assistant, Settings

---

## 🤝 Contributing

```bash
# 1. Create feature branch
git checkout -b feat/your-feature

# 2. Make changes

# 3. Run tests
pytest

# 4. Commit with conventional commits
git commit -m "feat: add user authentication"

# 5. Push and create PR
git push origin feat/your-feature
```

**Guidelines:**
- Write tests (target 80% coverage)
- Follow PEP 8 for Python
- Use conventional commits
- Test multi-tenant isolation
- Update documentation

---

## 📄 License

Private — All rights reserved. Contact project owner for licensing inquiries.

---

## 📞 Links & Resources

- **Documentation:** [docs/README.md](docs/README.md)
- **API Docs:** http://localhost:8000/docs (when running)
- **Current Status:** [docs/status/current.md](docs/status/current.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Issues:** GitHub Issues

---

**Built with ❤️ for alternative medicine practitioners**

**Last Updated:** April 21, 2026 | **Version:** 0.1.0-alpha | **Status:** Backend foundation complete ✅
