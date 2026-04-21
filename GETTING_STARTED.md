# 🚀 Getting Started with AltCare

**Welcome!** This guide will get you up and running with AltCare in 30 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **macOS, Linux, or Windows** with WSL2
- ✅ **Python 3.12+** - [Download](https://www.python.org/downloads/)
- ✅ **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- ✅ **Git** - [Download](https://git-scm.com/downloads)
- ✅ **Code Editor** - VS Code recommended

**Check your versions:**
```bash
python3 --version  # Should be 3.12 or higher
docker --version   # Should be 20.10 or higher
git --version      # Any recent version
```

---

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/alternative-care.git
cd alternative-care
```

### 2. Run Automated Setup

```bash
cd backend
./quick_start.sh
```

**What this does:**
- ✅ Starts Docker services (PostgreSQL, Redis, MinIO)
- ✅ Creates Python virtual environment
- ✅ Installs dependencies
- ✅ Installs pgvector extension
- ✅ Runs database migrations (creates 30 tables)
- ✅ Verifies everything works

**Time:** ~5 minutes

### 3. Verify Installation

Open your browser:

- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **MinIO Console:** http://localhost:9001 (minioadmin / minioadmin)

You should see:
- ✅ Swagger UI with API endpoints
- ✅ Health check returning `{"status": "healthy"}`
- ✅ MinIO login page

**✅ Success!** You're ready to develop.

---

## Manual Setup (Alternative)

If the automated script doesn't work, follow these steps:

### Step 1: Start Infrastructure

```bash
# From project root
docker compose up -d postgres redis minio

# Wait for services to start (15 seconds)
sleep 15

# Verify services are running
docker compose ps
```

### Step 2: Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
```

### Step 3: Install pgvector Extension

```bash
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 4: Run Migrations

```bash
# Generate migration (first time only)
alembic revision --autogenerate -m "Initial schema with 30 tables"

# Apply migrations
alembic upgrade head

# Verify tables created (should show 30 tables)
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "\dt"
```

### Step 5: Start the Development Server

```bash
# Still in backend/ directory with venv activated
uvicorn app.main:app --reload

# Server starts at: http://localhost:8000
```

---

## What's Next?

### For Developers

1. **Read the documentation map**
   - See [docs/README.md](docs/README.md) for full navigation

2. **Check current status**
   - Read [docs/status/current.md](docs/status/current.md) - What's done, what's next

3. **Complete setup guide**
   - Follow [docs/development/setup.md](docs/development/setup.md) for detailed setup

4. **Start coding**
   - Use [docs/development/quick-reference.md](docs/development/quick-reference.md) for code patterns
   - Pick a task from [docs/planning/phase1-tasks.md](docs/planning/phase1-tasks.md)

### For Stakeholders

1. **Understand the project**
   - Read [README.md](README.md) - Project overview

2. **Check the roadmap**
   - See [docs/planning/roadmap.md](docs/planning/roadmap.md) - High-level plan
   - Or [docs/planning/roadmap-detailed.md](docs/planning/roadmap-detailed.md) - Full details

3. **Track progress**
   - Monitor [docs/status/current.md](docs/status/current.md) - Updated weekly

### For Architects

1. **Review architecture**
   - Read [docs/architecture/overview.md](docs/architecture/overview.md) - System design

2. **Study the database**
   - Browse [docs/architecture/database.md](docs/architecture/database.md) - All 30 tables

3. **Understand the stack**
   - Check [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md) - Technology choices

---

## Common Commands

### Development

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f postgres  # PostgreSQL
docker compose logs -f redis     # Redis

# Restart a service
docker compose restart postgres

# Start backend (with auto-reload)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
```

### Database

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# Access database directly
docker exec -it altcare_postgres psql -U altcare -d altcare_dev
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py -v
```

---

## Troubleshooting

### Issue: Docker not running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Start Docker Desktop
# Then verify:
docker info
```

### Issue: Port already in use

**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Find process using the port
lsof -ti:8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Issue: Database connection failed

**Error:** `Could not connect to database`

**Solution:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart it
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Issue: pgvector not installed

**Error:** `Extension "vector" does not exist`

**Solution:**
```bash
# Install the extension
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION vector;"
```

### Issue: Migration failed

**Error:** `Alembic migration failed`

**Solution:**
```bash
# Reset database (DEV ONLY! Will delete all data)
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
alembic upgrade head
```

**Still stuck?** See [docs/development/setup.md](docs/development/setup.md) for detailed troubleshooting.

---

## Development Workflow

### Daily Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Start services (if not running)
docker compose up -d

# 3. Activate virtual environment
cd backend && source venv/bin/activate

# 4. Apply any new migrations
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --reload

# 6. Code, test, commit
# ... (your work here)

# 7. Run tests before commit
pytest

# 8. Commit your changes
git add .
git commit -m "feat: your feature description"
```

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feat/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: description"

# 3. Push to remote
git push origin feat/your-feature-name

# 4. Create pull request on GitHub
```

---

## Useful Resources

### Documentation
- [Full Documentation Index](docs/README.md)
- [Current Status](docs/status/current.md)
- [Backend Guide](docs/development/backend.md)
- [API Docs](http://localhost:8000/docs) (when running)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)

---

## Need Help?

- **Setup Issues:** See [docs/development/setup.md](docs/development/setup.md)
- **Code Examples:** Check [docs/development/quick-reference.md](docs/development/quick-reference.md)
- **Architecture Questions:** Read [docs/architecture/overview.md](docs/architecture/overview.md)
- **Project Status:** View [docs/status/current.md](docs/status/current.md)
- **Everything Else:** Start with [docs/README.md](docs/README.md)

---

**🎉 You're all set!** Happy coding!

**Next Step:** Choose your path in [docs/README.md](docs/README.md)
