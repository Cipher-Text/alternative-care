# Backend Setup Guide

Step-by-step guide to set up the AltCare backend for development.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Git

## Step 1: Start Infrastructure Services

```bash
# Navigate to project root
cd /Users/imran/Documents/Repo/Cipher-Text/alternative-care

# Start PostgreSQL, Redis, MinIO
docker compose up -d postgres redis minio

# Verify services are running
docker compose ps

# Expected output:
# altcare_postgres  - running on port 5432
# altcare_redis     - running on port 6379
# altcare_minio     - running on ports 9000, 9001
```

**Access MinIO Console**: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

## Step 2: Set Up Python Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Step 3: Verify Environment

Check that `.env` file exists with correct values:

```bash
# Should already exist, verify DATABASE_URL
cat .env | grep DATABASE_URL

# Expected:
# DATABASE_URL=postgresql+asyncpg://altcare:altcare123@localhost:5432/altcare_dev
```

## Step 4: Install pgvector Extension

```bash
# Connect to PostgreSQL
docker exec -it altcare_postgres psql -U altcare -d altcare_dev

# Inside psql, run:
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
\dx

# Exit psql
\q
```

## Step 5: Create Initial Migration

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema with 30 tables"

# Check the generated migration file
ls -la alembic/versions/

# Review the migration (important!)
# The file will be named something like: 20260421_1200_abc123_initial_schema_with_30_tables.py
```

## Step 6: Apply Migrations

```bash
# Apply all migrations
alembic upgrade head

# Verify tables were created
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "\dt"

# Expected: 30 tables listed
```

## Step 7: Run the Development Server

```bash
# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server should start on: http://localhost:8000
```

## Step 8: Verify Installation

Open your browser and visit:

1. **Health Check**: http://localhost:8000/health
   - Should return: `{"status": "healthy", ...}`

2. **API Docs**: http://localhost:8000/docs
   - Should show Swagger UI

3. **Root Endpoint**: http://localhost:8000/
   - Should return welcome message

## Troubleshooting

### Issue: Database connection error

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart if needed
docker compose restart postgres
```

### Issue: pgvector not installed

```bash
# Recreate database with pgvector image
docker compose down
docker compose up -d postgres

# Wait 10 seconds, then install extension
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "CREATE EXTENSION vector;"
```

### Issue: Alembic migration fails

```bash
# Drop all tables and retry (DEV ONLY!)
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migration
alembic upgrade head
```

### Issue: Port already in use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

## Next Steps

After successful setup:

1. ✅ Backend running on http://localhost:8000
2. ✅ Database with 30 tables created
3. ✅ API documentation available
4. 📋 Create seed data for testing
5. 📋 Build authentication module
6. 📋 Build patient management module

See **backend/README.md** for development workflows.

## Useful Commands

```bash
# Check migration status
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Run tests
pytest

# Format code
black app/

# Lint code
ruff check app/

# Generate Fernet key (for INTEGRATION_ENCRYPTION_KEY)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Development Workflow

1. Make changes to models or add new features
2. Create migration: `alembic revision --autogenerate -m "Description"`
3. Review migration file
4. Apply migration: `alembic upgrade head`
5. Test changes
6. Commit to git

---

**Ready to code!** 🚀
