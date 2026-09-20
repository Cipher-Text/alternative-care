---
title: "Backend Setup Guide"
type: "setup"
difficulty: "intermediate"
time: "20-30 minutes"
last_updated: "2026-05-01"
ai_summary: "Complete FastAPI backend setup with PostgreSQL, Redis, MinIO, and Alembic migrations"
---

# Backend Setup Guide

Complete guide to set up the AltCare FastAPI backend for development.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Automated)](#quick-start-automated)
- [Manual Setup](#manual-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Development Workflow](#development-workflow)

---

## ✅ Prerequisites

**Required Software:**
- Python 3.12+
- Docker & Docker Compose (for Redis and MinIO — PostgreSQL is not containerized, see below)
- PostgreSQL 16 (installed and running locally, e.g. via Homebrew/Postgres.app)
- Git

**Check Versions:**
```bash
python3 --version  # Should be 3.12+
docker --version   # Should be 20.10+
git --version      # Any recent version
```

---

## 🚀 Quick Start (Automated)

**Recommended method - runs all setup steps automatically:**

```bash
# 1. Navigate to backend
cd backend

# 2. Run automated setup
./quick_start.sh
```

**What this does:**
1. ✅ Starts Docker services (Redis, MinIO) — assumes a local PostgreSQL 16 instance is already running on port 5432
2. ✅ Creates Python virtual environment
3. ✅ Installs dependencies
4. ✅ Creates `.env` file
5. ✅ Installs pgvector extension
6. ✅ Runs database migrations (creates 34 tables)
7. ✅ Seeds initial data
8. ✅ Verifies installation

**Time:** ~5 minutes

**If successful, skip to** [Verification](#verification)

---

## 🔧 Manual Setup

If automated setup doesn't work, follow these steps:

### Step 1: Start Infrastructure Services

`docker-compose.yml` manages Redis and MinIO only — PostgreSQL is **not** containerized in this project and must already be installed and running locally.

```bash
# Navigate to project root
cd alternative-care

# Start Redis and MinIO
docker compose up -d

# Verify services are running
docker compose ps
```

**Expected Output:**
- `altcare_redis` - running on port 6379
- `altcare_minio` - running on ports 9000, 9001

Make sure a local PostgreSQL 16 server is also running on port 5432 (matching `DATABASE_URL` in `backend/.env`), and that the `altcare` role/database exist.

**Access MinIO Console:** http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

---

### Step 2: Set Up Python Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e .

# Or with dev dependencies (for testing/linting)
pip install -e ".[dev]"
```

---

### Step 3: Verify Environment Configuration

Check that `.env` file exists with correct values:

```bash
# View DATABASE_URL
cat .env | grep DATABASE_URL

# Expected:
# DATABASE_URL=postgresql+asyncpg://altcare:altcare123@localhost:5432/altcare_dev
```

**If `.env` doesn't exist, create it:**
```bash
cp .env.example .env
```

---

### Step 4: Install pgvector Extension

```bash
# Connect to your local PostgreSQL and install extension
psql -U altcare -d altcare_dev -h localhost \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify installation
psql -U altcare -d altcare_dev -h localhost \
  -c "\dx"

# Should show pgvector extension
```

---

### Step 5: Run Database Migrations

```bash
# Generate initial migration (first time only)
alembic revision --autogenerate -m "Initial schema"

# Check generated migration
ls -la alembic/versions/

# Apply migrations
alembic upgrade head

# Verify tables were created (should show 34 tables)
psql -U altcare -d altcare_dev -h localhost \
  -c "\dt"
```

**34 Tables Created:**
- Core: `tenants`, `users`, `user_sessions`
- Doctor: `doctor_degrees`, `doctor_trainings`
- Geographic: `divisions`, `districts`, `upazilas`
- Patient: `patients`, `patient_tags`, `patient_diagnoses`
- Appointments: `appointments`, `visits`
- Prescription: `prescriptions`, `prescription_items`
- Payment: `payments`, `invoices`
- Medicine: `medicines`, `medicine_aliases`, `symptoms`, `symptom_aliases`, `medicine_symptom_mappings`
- Library: `books`, `chapters`, `sections`, `embeddings`, `reading_progress`, `bookmarks`, `highlights`
- Integration: `integration_providers`, `tenant_integrations`, `integration_logs`
- System: `translations`, `usage_tracking`

---

### Step 6: Seed Initial Data (Optional)

```bash
# Run seed script
./scripts/run_seed.sh
```

**Seed Data:**
- Bangladesh geographic data (8 divisions, 64 districts, 495 upazilas)
- Integration providers (12 providers: SMS, Email, Payment; local logo paths)
- UI translations (80+ English/Bengali strings)
- Sample tenants and users for development

---

### Step 7: Start Development Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server starts at: http://localhost:8000
```

**Server Options:**
- `--reload`: Auto-restart on code changes
- `--host 0.0.0.0`: Accept connections from any IP
- `--port 8000`: Port number (default: 8000)

---

## ✅ Verification

Open your browser and verify:

### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Expected:**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "0.9.0"
}
```

### 2. API Documentation
Visit: http://localhost:8000/docs

**Should see:** Swagger UI with 128 API endpoints across 14 modules

### 3. Root Endpoint
Visit: http://localhost:8000/

**Should see:** Welcome message with API version

---

## 🐛 Troubleshooting

### Database Connection Error

PostgreSQL runs locally, not in Docker — `docker compose ps`/`logs`/`restart` only apply to Redis and MinIO.

```bash
# Check if your local PostgreSQL is running and reachable
pg_isready -h localhost -p 5432
# Or:
psql -U altcare -d altcare_dev -h localhost -c "SELECT 1;"

# macOS (Homebrew): restart if needed
brew services restart postgresql@16
```

---

### pgvector Not Installed

```bash
# Install extension on your local PostgreSQL
psql -U altcare -d altcare_dev -h localhost \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### Alembic Migration Fails

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# If stuck, reset database (DEV ONLY - destroys all data!)
psql -U altcare -d altcare_dev -h localhost \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
alembic upgrade head
```

---

### Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

### Import Error: Module Not Found

```bash
# Reinstall dependencies
pip install -e ".[dev]"

# Or install specific package
pip install <package-name>
```

---

## 🛠️ Development Workflow

### Making Code Changes

```bash
# 1. Make changes to models or add features
# Edit files in backend/app/

# 2. Create migration if models changed
alembic revision --autogenerate -m "Description of changes"

# 3. Review generated migration
# Check file in backend/alembic/versions/

# 4. Apply migration
alembic upgrade head

# 5. Test changes
pytest

# 6. Commit to git
git add .
git commit -m "Description"
```

---

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=app --cov-report=html
```

---

### Code Quality

```bash
# Format code with Black
black app/

# Lint code with Ruff
ruff check app/

# Type checking with MyPy
mypy app/
```

---

### Useful Commands

```bash
# Check migration status
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Generate Fernet key (for INTEGRATION_ENCRYPTION_KEY)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Access PostgreSQL directly (local instance)
psql -U altcare -d altcare_dev -h localhost

# View database tables
psql -U altcare -d altcare_dev -h localhost \
  -c "\dt"

# Stop Redis/MinIO
docker compose down

# Stop and remove volumes (clears Redis/MinIO data only — PostgreSQL is unaffected)
docker compose down -v
```

---

## 🤖 AI Quick Reference

**Q: How do I start the backend?**
→ `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

**Q: How do I run migrations?**
→ `alembic upgrade head`

**Q: How do I reset the database?**
→ `docker compose down -v` then `docker compose up -d` then `alembic upgrade head`

**Q: Where are the API docs?**
→ http://localhost:8000/docs

**Q: How do I add a new model?**
→ Create in `app/shared/models/`, then `alembic revision --autogenerate -m "Add model"`

---

**See Also:**
- [Getting Started](../../GETTING_STARTED.md) - local setup flow
- [API Reference](../api/README.md) - API documentation
- [Architecture](../architecture/README.md) - System design

---

**Last Updated:** September 21, 2026  
**Difficulty:** Intermediate  
**Time Required:** 20-30 minutes ✅
