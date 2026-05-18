# AltCare Backend

FastAPI backend for multi-tenant alternative medicine practice management.

**Full Documentation:** See [../CLAUDE.md](../CLAUDE.md) for architecture, patterns, and detailed guides.

---

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Run automated setup
./quick_start.sh

# 3. Start development server
source venv/bin/activate
uvicorn app.main:app --reload
```

**API Docs:** http://localhost:8000/docs

---

## Project Structure

```
backend/app/
├── main.py              # FastAPI app entry point
├── core/                # Infrastructure
│   ├── config.py       # Settings (env vars)
│   ├── database.py     # SQLAlchemy async engine
│   ├── security.py     # JWT, bcrypt, TOTP, Fernet
│   ├── celery.py       # Background tasks
│   └── dependencies.py # Auth, RBAC, plan checks
├── modules/             # Feature modules (87 endpoints)
│   ├── auth/           # Login, refresh, 2FA (16)
│   ├── ai/             # Query stub (1)
│   ├── doctor/         # Profile, degrees (12)
│   ├── patient/        # CRUD, search, tags (14)
│   ├── appointments/   # Scheduling, visits (6)
│   ├── prescription/   # Builder, PDF (8)
│   ├── payment/        # Processing, bKash (12)
│   ├── integration/    # SMS/Email/Payment (12)
│   └── dashboard/      # Analytics, stats (6)
└── shared/
    ├── models/         # SQLAlchemy models (34 table models)
    └── schemas/        # Pydantic schemas

**Note:** Module API docs are in `../docs/api/` directory
```

**Implemented:** 9 modules, 87 endpoints, 34 table models  
**Placeholder:** medicine, library, notification (not implemented)

---

## Database (34 Tables)

**Core:** tenants, users, user_sessions  
**Doctor:** doctor_degrees, doctor_trainings  
**Geographic:** divisions, districts, upazilas (Bangladesh)  
**Patient:** patients, patient_tags, patient_diagnoses  
**Appointments:** appointments, visits  
**Prescription:** prescriptions, prescription_items  
**Payment:** payments, invoices  
**Medicine:** medicines, medicine_aliases  
**Symptom:** symptoms, symptom_aliases, medicine_symptom_mappings  
**Library:** books, chapters, sections, embeddings, reading_progress, bookmarks, highlights  
**Integration:** integration_providers, tenant_integrations, integration_logs  
**System:** translations, usage_tracking

**Pattern:** All tenant-scoped tables have `tenant_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` (soft deletes)

See [../CLAUDE.md § 4.3](../CLAUDE.md) for schema details.

---

## Development

### Essential Commands

```bash
# Database
alembic upgrade head                        # Apply migrations
alembic revision --autogenerate -m "desc"   # Create migration
alembic downgrade -1                        # Rollback
./scripts/run_seed.sh                       # Seed data

# Testing
pytest --cov=app --cov-report=html          # All tests with coverage
pytest tests/unit/test_auth.py -v           # Specific test
pytest tests/integration/ -v                # Integration tests

# Code Quality
black app/                                  # Format
ruff check app/                             # Lint
mypy app/                                   # Type check

# Server
uvicorn app.main:app --reload               # Development server
uvicorn app.main:app --reload --port 8001   # Different port

# Celery (background tasks)
celery -A app.core.celery:celery_app worker --loglevel=info
```

### Generate Encryption Key

```bash
# For INTEGRATION_ENCRYPTION_KEY in .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Adding Features

**See [../CLAUDE.md § 5](../CLAUDE.md) for complete implementation guides:**

- Add Backend Endpoint → CLAUDE.md § 5.1
- Database Migration → CLAUDE.md § 5.2
- Test Multi-Tenant Isolation → CLAUDE.md § 5.3

**Pattern:**
1. Define Pydantic schemas in `modules/<module>/schemas.py`
2. Create routes in `modules/<module>/router.py`
3. Register router in `app/main.py`
4. Add tests in `tests/`

---

## Environment Variables

**Critical Settings:**

```bash
# Security
SECRET_KEY=<generate-random-string>
INTEGRATION_ENCRYPTION_KEY=<fernet-key>

# Database
DATABASE_URL=postgresql+asyncpg://altcare:altcare@localhost:5432/altcare_dev

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Integrations (optional)
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
OPENAI_API_KEY=
```

See `.env.example` for all options.

---

## Key Files

- **app/main.py** - FastAPI app, router registration
- **app/core/dependencies.py** - Auth, CurrentUser, RBAC
- **app/core/security.py** - JWT, encryption, password hashing
- **alembic/versions/** - Database migrations
- **tests/conftest.py** - Test fixtures
- **API_ENDPOINTS.md** - All endpoints overview
- **../docs/api/** - Detailed API documentation by module
- **../CLAUDE.md** - Main documentation (architecture, patterns, guides)

---

## Troubleshooting

**pgvector missing:**
```bash
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Port in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Migration failed:**
```bash
# DEV ONLY - destroys data
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

See [../CLAUDE.md § 6](../CLAUDE.md) for more troubleshooting.

---

## API Documentation

**Local:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

**Reference:**
- API Overview: [API_ENDPOINTS.md](API_ENDPOINTS.md)
- Detailed API Docs: [../docs/api/](../docs/api/)
- Architecture & Patterns: [../CLAUDE.md](../CLAUDE.md)
- Breaking Changes: [../BREAKING_CHANGES.md](../BREAKING_CHANGES.md)
