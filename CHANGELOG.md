# Changelog

All notable changes to the AltCare project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Backend Foundation (2026-04-21)

#### Infrastructure
- Docker Compose setup with PostgreSQL 16 + pgvector, Redis 7, and MinIO
- Automated setup script (`backend/quick_start.sh`)
- GitHub Actions workflow for automated testing
- Complete test framework with pytest and async support

#### Database (30 Tables Implemented)
- **Core (3):** tenants, users, user_sessions
- **Doctor (2):** doctor_degrees, doctor_trainings
- **Geographic (3):** divisions, districts, upazilas (Bangladesh)
- **Patient (3):** patients, patient_tags, patient_diagnoses
- **Prescription (2):** prescriptions, prescription_items
- **Payment (2):** payments, invoices
- **Medicine (2):** medicines, medicine_symptoms
- **Library (7):** books, chapters, sections, embeddings, reading_progress, bookmarks, highlights
- **Integration (3):** integration_providers, tenant_integrations, integration_logs
- **System (2):** translations (i18n), usage_tracking

#### Backend Core
- FastAPI application with async support
- SQLAlchemy 2.0 async ORM with all 30 models
- Alembic migrations configured for async
- JWT authentication with access + refresh tokens
- TOTP-based 2FA support (QR code generation)
- Bcrypt password hashing
- Multi-tenant middleware with ContextVar for automatic tenant filtering
- Role-based access control (RBAC) dependencies
- Plan-based feature gating
- Fernet encryption for integration credentials
- Base audit models (created_at, updated_at, created_by, updated_by)
- Bilingual field support (EN/BN) on all content models

#### Documentation
- Complete backend README with setup instructions
- Step-by-step SETUP.md guide
- Backend implementation summary
- Quick status document for project overview
- Updated main README with backend completion status
- Updated ROADMAP with Phase 1 Week 1-2 marked complete
- Updated START_HERE with current status
- GitHub Actions workflow documentation

#### Project Structure
- Modular backend structure with feature-based modules
- Shared models and schemas architecture
- Test directory structure with fixtures
- Environment configuration templates

### Changed
- Updated README.md to reflect backend completion
- Updated ROADMAP.md Phase 1 status (Week 1-2 complete)
- Updated START_HERE.md with backend foundation status
- Updated IMPLEMENTATION_SUMMARY.md with progress
- Revised project status indicators across all docs

---

## Project Milestones

### Phase 0: Planning & Design ✅ Complete
- UI mockups (Admin + Doctor views)
- Database schema design (30 tables)
- Technology stack finalization
- 12-month roadmap creation
- Complete documentation suite

### Phase 1: Core Clinic MVP 🔄 In Progress
- **Week 1-2 ✅ Complete:** Backend foundation with 30 database models
- **Week 3-4 📋 Next:** Authentication & User Management API endpoints
- **Week 5-14 📋 Planned:** Full MVP implementation

### Phase 2-4: 📋 Planned
- Knowledge Base (Medicine database)
- Book Library & Reader
- AI/RAG Intelligence

---

## Statistics

### Lines of Code
- Backend Python: ~2,500+ lines
- Database Models: 30 tables
- Documentation: 10+ markdown files

### Test Coverage
- Target: 80%+
- Framework: pytest + pytest-asyncio
- E2E: To be implemented with Playwright

### Dependencies
- Python packages: 30+ (see pyproject.toml)
- Docker services: 3 (PostgreSQL, Redis, MinIO)

---

**Last Updated:** April 21, 2026  
**Version:** 0.1.0-alpha  
**Status:** Backend foundation complete, ready for API implementation
