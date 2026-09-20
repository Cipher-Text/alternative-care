# Database Migration Guide

Practical guide for running and verifying Alembic migrations.

**For breaking changes:** See [BREAKING_CHANGES.md](../docs/archive/BREAKING_CHANGES.md)

---

## Quick Migration

```bash
# Check current state
alembic current

# Apply all pending migrations
alembic upgrade head

# Verify tables created
alembic current
```

---

## 1. SETUP

### Install Alembic

```bash
cd backend
source venv/bin/activate
pip install alembic
```

### Configuration

Alembic is pre-configured:
- **Config:** `alembic.ini`
- **Env:** `alembic/env.py`
- **Migrations:** `alembic/versions/`

Database URL loaded from `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://altcare:altcare@localhost:5432/altcare_dev
```

---

## 2. RUNNING MIGRATIONS

### Apply Migrations

```bash
# Apply all pending
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Upgrade to specific revision
alembic upgrade <revision_id>
```

### Check Status

```bash
# Current revision
alembic current

# Migration history
alembic history

# Show SQL without running
alembic upgrade head --sql
```

### Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

---

## 3. CREATING MIGRATIONS

### Auto-Generate from Models

```bash
# After modifying SQLAlchemy models in app/shared/models/
alembic revision --autogenerate -m "Add new table"

# Review generated file in alembic/versions/
# Edit if needed (autogenerate isn't perfect)

# Apply migration
alembic upgrade head
```

### Manual Migration

```bash
# Create empty migration
alembic revision -m "Custom data migration"

# Edit alembic/versions/<hash>_custom_data_migration.py
# Add upgrade() and downgrade() logic

# Apply
alembic upgrade head
```

### Migration Template

```python
"""Add custom field

Revision ID: abc123
Revises: xyz789
Create Date: 2026-05-08 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade():
    # Add column
    op.add_column('patients', 
        sa.Column('custom_field', sa.String(100), nullable=True)
    )
    
    # Create index
    op.create_index('ix_patients_custom_field', 'patients', ['custom_field'])

def downgrade():
    # Reverse operations
    op.drop_index('ix_patients_custom_field', 'patients')
    op.drop_column('patients', 'custom_field')
```

---

## 4. VERIFICATION

### Verify Tables

```sql
-- List all tables
\dt

-- Specific tables
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('patients', 'appointments', 'prescriptions');

-- Table structure
\d+ patients
```

### Verify Indexes

```sql
-- All indexes
\di

-- Specific table indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'patients';
```

### Verify Foreign Keys

```sql
-- All foreign keys
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### Verify Data

```sql
-- Count records
SELECT COUNT(*) FROM patients;

-- Check tenant isolation
SELECT tenant_id, COUNT(*) FROM patients GROUP BY tenant_id;
```

---

## 5. DATA MIGRATION

### Seed Initial Data

```bash
# Run seed script after migrations
./scripts/run_seed.sh
```

**Seeds:**
- Geographic data (divisions, districts, upazilas)
- Integration providers (12 providers)
- UI translations (80 strings)
- Starter medicines and symptoms data
- Sample tenants/users (dev only)

### Populate Alias Tables

```python
# Example: Symptom aliases (critical for Bangladesh search)
from app.shared.models import Symptom, SymptomAlias

# Create symptom
symptom = Symptom(
    name_en="Headache",
    name_bn="মাথা ব্যথা",
    category="neurological",
    is_global=True
)
session.add(symptom)
session.flush()

# Add aliases
aliases = [
    SymptomAlias(
        symptom_id=symptom.id,
        alias_en="matha byatha",
        alias_type="transliteration",
        priority=8
    ),
    SymptomAlias(
        symptom_id=symptom.id,
        alias_en="migraine",
        alias_type="common_name",
        priority=7
    ),
]
session.add_all(aliases)
session.commit()
```

See [ALIAS_DATA_EXAMPLES.md](ALIAS_DATA_EXAMPLES.md) for more examples.

---

## 6. TROUBLESHOOTING

### Migration Failed

```bash
# Check error message
alembic upgrade head

# If stuck, check current state
alembic current
alembic history

# Manual fix in database, then stamp revision
alembic stamp <revision_id>
```

### Tables Already Exist

```bash
# If migration says "table already exists"
# Option 1: Drop and recreate (DEV ONLY) — PostgreSQL runs locally, not in Docker
psql -U altcare -d altcare_dev -h localhost \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head

# Option 2: Stamp current state
alembic stamp head
```

### Alembic Out of Sync

```bash
# Reset to specific revision
alembic downgrade <revision_id>
alembic upgrade head

# Or stamp to current schema
alembic stamp head
```

### pgvector Extension Missing

```bash
# Install on your local PostgreSQL instance (not containerized)
psql -U altcare -d altcare_dev -h localhost \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Multiple Migration Branches

```bash
# Check for heads
alembic heads

# Merge branches
alembic merge <rev1> <rev2> -m "Merge branches"
alembic upgrade head
```

---

## 7. BEST PRACTICES

### Before Creating Migration

1. **Test models locally** - Ensure SQLAlchemy models work
2. **Check existing schema** - Avoid duplicate tables/columns
3. **Review autogenerate output** - Always review before applying

### Autogenerate Limitations

**May miss:**
- Data migrations
- Index changes on existing columns
- Constraint modifications
- Enum type changes
- Table/column renames (creates drop+add instead)

**Always review and edit generated migrations!**

### Migration Guidelines

1. **One concern per migration** - Don't mix schema + data changes
2. **Make reversible** - Implement proper `downgrade()`
3. **Test rollback** - Ensure `downgrade()` works
4. **Document** - Add clear description and comments
5. **Small migrations** - Easier to debug and rollback

### Multi-Tenant Safety

**Always include in tenant-scoped tables:**
```python
op.add_column('new_table', sa.Column('tenant_id', sa.UUID(), nullable=False))
op.create_foreign_key('fk_new_table_tenant', 'new_table', 'tenants', ['tenant_id'], ['id'])
op.create_index('ix_new_table_tenant_id', 'new_table', ['tenant_id'])
```

---

## 8. CHECKLIST

### Pre-Migration

- [ ] Database backup (production)
- [ ] Review migration file
- [ ] Test in dev environment
- [ ] Document breaking changes

### Post-Migration

- [ ] Verify tables created (`\dt`)
- [ ] Verify indexes created (`\di`)
- [ ] Verify foreign keys working
- [ ] Run tests (`pytest`)
- [ ] Seed data if needed
- [ ] Update API documentation

---

## 9. REFERENCE

### Commands Cheatsheet

```bash
# Status
alembic current                    # Current revision
alembic history                    # All revisions
alembic heads                      # Latest revisions

# Upgrade
alembic upgrade head              # All pending
alembic upgrade +1                # Next one
alembic upgrade <rev>             # To specific

# Downgrade
alembic downgrade -1              # Previous one
alembic downgrade <rev>           # To specific
alembic downgrade base            # All the way back

# Create
alembic revision --autogenerate -m "msg"   # Auto from models
alembic revision -m "msg"                  # Manual

# Utilities
alembic stamp <rev>               # Mark as current
alembic merge <rev1> <rev2>       # Merge branches
alembic show <rev>                # Show migration
```

### Files

- **Config:** `alembic.ini`
- **Environment:** `alembic/env.py`
- **Migrations:** `alembic/versions/`
- **Models:** `app/shared/models/`

### Resources

- **Breaking Changes:** [BREAKING_CHANGES.md](../docs/archive/BREAKING_CHANGES.md)
- **Alias Examples:** [ALIAS_DATA_EXAMPLES.md](ALIAS_DATA_EXAMPLES.md)
- **Architecture:** [../CLAUDE.md](../CLAUDE.md)
- **Alembic Docs:** https://alembic.sqlalchemy.org
