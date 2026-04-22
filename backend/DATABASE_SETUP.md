# Database Setup Guide

## Current Status

✅ Dependencies installed  
✅ Alembic configured  
✅ Migration file ready  
⚠️ **Database not set up yet**

---

## Error Encountered

```
asyncpg.exceptions.InvalidAuthorizationSpecificationError: role "altcare" does not exist
```

This means PostgreSQL is running but the database user/role hasn't been created yet.

---

## Setup Options

### Option 1: Create New Database (Recommended)

```bash
# 1. Connect to PostgreSQL as superuser
psql postgres

# 2. Create user and database
CREATE USER altcare WITH PASSWORD 'your_secure_password';
CREATE DATABASE alternative_care OWNER altcare;

# 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE alternative_care TO altcare;

# 4. Connect to the new database
\c alternative_care

# 5. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram search
CREATE EXTENSION IF NOT EXISTS "pgvector";  -- For AI embeddings

# 6. Grant schema privileges
GRANT ALL ON SCHEMA public TO altcare;

# 7. Exit
\q
```

### Option 2: Use Existing Database

Update `.env` file with your existing PostgreSQL credentials:

```env
DATABASE_URL=postgresql+asyncpg://your_user:your_pass@localhost:5432/your_db
```

---

## Update .env File

Check/update your `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://altcare:your_password@localhost:5432/alternative_care
DATABASE_ECHO=false
```

---

## Run Migration

Once database is set up:

```bash
cd backend
source venv/bin/activate

# Check connection
alembic current

# Run migration
alembic upgrade head

# Verify
alembic current
# Should show: 001_phase1a_tables (head)
```

---

## Verify Tables Created

```bash
psql -U altcare -d alternative_care

# List tables
\dt

# Should see:
# - appointments
# - visits
# - symptoms
# - symptom_aliases
# - medicine_aliases
# - medicine_symptom_mappings
# - (plus existing tables)

# Check table structure
\d+ symptoms
\d+ symptom_aliases

# Exit
\q
```

---

## Troubleshooting

### PostgreSQL Not Installed

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Can't Connect

```bash
# Check if PostgreSQL is running
psql --version
pg_isready

# Check status
brew services list | grep postgres  # macOS
sudo systemctl status postgresql    # Linux
```

### Permission Denied

```bash
# Grant superuser (if needed for extensions)
psql postgres
ALTER USER altcare WITH SUPERUSER;
\q
```

---

## Next Steps

1. ✅ Set up database (follow Option 1 or 2 above)
2. ✅ Run migration: `alembic upgrade head`
3. ✅ Verify tables created
4. Then continue with API development

---

## Quick Test

After migration, test the database:

```python
# test_db.py
import asyncio
import asyncpg

async def test_connection():
    conn = await asyncpg.connect(
        'postgresql://altcare:your_password@localhost:5432/alternative_care'
    )
    
    # Test query
    result = await conn.fetch('SELECT tablename FROM pg_tables WHERE schemaname = $1', 'public')
    print("Tables:", [r['tablename'] for r in result])
    
    await conn.close()

asyncio.run(test_connection())
```

Run: `python test_db.py`
