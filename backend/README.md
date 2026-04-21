# AltCare Backend

FastAPI backend for Alternative Medicine Practice Management System.

## Quick Start

### 1. Start infrastructure services

```bash
# Start PostgreSQL, Redis, MinIO
docker compose up -d postgres redis minio
```

### 2. Set up Python environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Or for development
pip install -e ".[dev]"
```

### 3. Configure environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values (at minimum, database URL should be correct)
```

### 4. Run database migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema with 30 tables"

# Apply migrations
alembic upgrade head
```

### 5. Run the development server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using python
python -m app.main
```

### 6. Access the API

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Settings (Pydantic)
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── security.py        # JWT, password hashing, 2FA
│   │   └── dependencies.py    # FastAPI dependencies (auth, etc.)
│   ├── modules/                # Feature modules
│   │   ├── auth/              # Authentication
│   │   ├── doctor/            # Doctor profile & credentials
│   │   ├── patient/           # Patient management
│   │   ├── prescription/      # Prescription system
│   │   ├── payment/           # Payments & invoices
│   │   ├── medicine/          # Medicine database
│   │   ├── library/           # Book library
│   │   ├── ai/                # AI/RAG (Phase 4)
│   │   ├── notification/      # Email/SMS
│   │   ├── integration/       # Integration framework
│   │   └── dashboard/         # Dashboard & analytics
│   └── shared/
│       ├── models/            # SQLAlchemy models (30 tables)
│       └── schemas/           # Pydantic schemas
├── alembic/                   # Database migrations
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic config
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── pyproject.toml             # Python project config
├── alembic.ini                # Alembic config
└── README.md                  # This file
```

## Database Models (30 Tables)

### Core (3 tables)
- `tenants` - Clinics/doctors
- `users` - Platform and tenant users
- `user_sessions` - Session tracking

### Doctor Credentials (2 tables)
- `doctor_degrees` - Academic degrees
- `doctor_trainings` - Professional training/certifications

### Geographic (3 tables)
- `divisions` - Bangladesh divisions (8)
- `districts` - Districts (64)
- `upazilas` - Sub-districts (490+)

### Patient Management (3 tables)
- `patients` - Patient records
- `patient_tags` - Tags (special case, chronic, treatment, allergy)
- `patient_diagnoses` - Diagnosis records

### Prescription (2 tables)
- `prescriptions` - Prescription records
- `prescription_items` - Medicine items

### Payment (2 tables)
- `payments` - Payment records
- `invoices` - Invoice generation

### Medicine Database (2 tables)
- `medicines` - Medicine catalog (bilingual)
- `medicine_symptoms` - Symptom-to-medicine mapping

### Library (7 tables)
- `books` - Medical books
- `chapters` - Book chapters
- `sections` - Parsed content sections
- `embeddings` - Vector embeddings (pgvector)
- `reading_progress` - User reading progress
- `bookmarks` - User bookmarks
- `highlights` - User highlights

### Integrations (3 tables)
- `integration_providers` - Provider catalog
- `tenant_integrations` - Tenant configurations
- `integration_logs` - Transaction audit logs

### System (2 tables)
- `translations` - i18n key-value pairs (EN/BN)
- `usage_tracking` - Plan limit enforcement

## Development

### Running tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py -v
```

### Code quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy app/
```

### Database migrations

```bash
# Create a new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Generate Fernet key for encryption

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

See `.env.example` for all available configuration options.

**Critical settings to change in production:**
- `SECRET_KEY` - JWT signing key
- `INTEGRATION_ENCRYPTION_KEY` - Fernet key for credentials
- `DATABASE_URL` - Production database
- `CORS_ORIGINS` - Production frontend URL
- All API keys (SendGrid, Twilio, SSLCommerz, Stripe, OpenAI)

## Next Steps

1. ✅ Backend structure created
2. ✅ Database models defined (30 tables)
3. ✅ Core modules implemented (config, database, security)
4. 🔄 Run initial migration
5. 📋 Create authentication module
6. 📋 Create patient management module
7. 📋 Create prescription module

See [ROADMAP.md](../ROADMAP.md) for full development plan.
