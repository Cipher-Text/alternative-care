# Getting Started with AltCare

Get up and running in 10 minutes.

---

## 1. PREREQUISITES

**Required:**
- Python 3.12+ - [Download](https://www.python.org/downloads/)
- Docker & Docker Compose (for Redis and MinIO) - [Download](https://www.docker.com/products/docker-desktop/)
- PostgreSQL 16 (installed and running locally, e.g. via Homebrew/Postgres.app — **not** containerized in this project)
- Git - [Download](https://git-scm.com/downloads)

**Verify:**
```bash
python3 --version  # 3.12+
docker --version   # 20.10+
git --version
```

**Recommended:**
- VS Code with Python extension
- macOS, Linux, or Windows with WSL2

---

## 2. QUICK START (10 Minutes)

### Clone Repository

```bash
git clone https://github.com/your-org/alternative-care.git
cd alternative-care
```

### Backend Setup (Automated)

```bash
cd backend
./quick_start.sh
```

**This script:**
- Starts Docker services (Redis 7, MinIO) — assumes a local PostgreSQL 16 instance is already running on port 5432
- Creates Python virtual environment
- Installs dependencies
- Installs pgvector extension
- Runs database migrations (creates 34 tables)

**Duration:** ~5-10 minutes

**Then seed initial data** (the script above does not do this automatically):

```bash
./scripts/run_seed.sh
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Frontend runs at:** http://localhost:3000

### Verify Installation

**Open in browser:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Should see:**
- Frontend login page
- Swagger UI with 133 API endpoints
- Health check: `{"status": "healthy"}`

**Success!** You're ready to develop.

---

## 3. MANUAL SETUP (If Automated Fails)

### Step 1: Start Infrastructure

`docker-compose.yml` manages Redis and MinIO only — PostgreSQL is **not** containerized and must already be installed and running locally (matching `DATABASE_URL` in `backend/.env`).

```bash
# From project root
docker compose up -d

# Verify services running (redis, minio)
docker compose ps
```

### Step 2: Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Install pgvector on your local PostgreSQL
psql -U altcare -d altcare_dev -h localhost \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
alembic upgrade head

# Seed data
./scripts/run_seed.sh

# Start server
uvicorn app.main:app --reload
```

### Step 3: Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 4. DAILY WORKFLOW

### Start Development

```bash
# 1. Start services (if not running)
docker compose up -d

# 2. Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# 3. Frontend (separate terminal)
cd frontend && npm run dev

# 4. Celery (optional, for background tasks)
celery -A app.core.celery:celery_app worker --loglevel=info
```

### Before Committing

```bash
# Run tests
cd backend && pytest --cov=app

# Run frontend E2E tests
cd frontend && npx playwright test

# Format code
cd backend && black app && ruff check app
```

---

## 5. NEXT STEPS

### Understand the Codebase

1. **Read CLAUDE.md** - Architecture, patterns, conventions
2. **Browse API Docs** - http://localhost:8000/docs (Swagger with all 133 API endpoints)
3. **Browse frontend/src/** - Component structure
4. **Check docs/** - Detailed documentation by area (setup, architecture, API)

### Start Coding

**Backend:**
- Add new endpoint: See CLAUDE.md § 5.1
- Add database table: See CLAUDE.md § 5.2
- Module structure: `backend/app/modules/<module>/`

**Frontend:**
- Add new page: See CLAUDE.md § 5.3
- API client: `frontend/src/lib/api/`
- Components: `frontend/src/components/`

### Test Your Changes

```bash
# Backend unit tests
pytest tests/unit/test_<module>.py -v

# Backend integration tests
pytest tests/integration/ -v

# Frontend E2E tests
cd frontend && npx playwright test --ui
```

---

## 6. TROUBLESHOOTING

### Docker Not Running

```bash
# Start Docker Desktop, then verify:
docker info
```

### Port Already in Use

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Failed

PostgreSQL runs locally, not in Docker — `docker compose` only manages Redis and MinIO.

```bash
# Check if your local PostgreSQL is running and reachable
pg_isready -h localhost -p 5432
psql -U altcare -d altcare_dev -h localhost -c "SELECT 1;"

# macOS (Homebrew): restart if needed
brew services restart postgresql@16
```

### pgvector Not Installed

```bash
# Install extension on your local PostgreSQL
psql -U altcare -d altcare_dev -h localhost \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Migration Failed

```bash
# Reset database (DEV ONLY - destroys all data)
psql -U altcare -d altcare_dev -h localhost \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
alembic upgrade head
```

### Frontend Module Not Found

```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

---

## 7. REFERENCE

### Essential Commands

```bash
# Database
alembic upgrade head              # Apply migrations
alembic revision --autogenerate   # Create migration
./scripts/run_seed.sh             # Seed data

# Testing
pytest --cov=app                  # Backend tests
npx playwright test               # Frontend E2E

# Code Quality
black backend/app                 # Format
ruff check backend/app            # Lint
mypy backend/app                  # Type check
```

### Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger), http://localhost:8000/redoc
- **Database:** localhost:5432 (user: altcare, db: altcare_dev, local install — not in Docker)
- **Redis:** localhost:6379 (Docker)
- **MinIO:** http://localhost:9001 (minioadmin/minioadmin, Docker)

### Key Files

- **CLAUDE.md** - Main documentation (architecture, patterns, how-tos)
- **docs/** - Detailed documentation by area (API, architecture, setup, planning)
- **backend/.env** - Backend environment variables
- **frontend/.env.local** - Frontend environment variables
- **docker-compose.yml** - Infrastructure setup

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes, commit
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feat/your-feature
```

---

## Need Help?

1. **Architecture & Patterns:** See CLAUDE.md
2. **API Documentation:** http://localhost:8000/docs
3. **Troubleshooting:** CLAUDE.md § 6
4. **Breaking Changes:** See docs/archive/BREAKING_CHANGES.md

**You're all set!** Start coding with CLAUDE.md as your guide.
