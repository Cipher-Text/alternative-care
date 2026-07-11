# Breaking Changes - Migration 001

**Migration**: 001_phase1a_tables  
**Date**: 2026-04-23  
**Type**: BREAKING - No Backward Compatibility  
**Impact**: `medicine_symptoms` table → 3 normalized tables (`symptoms`, `symptom_aliases`, `medicine_symptom_mappings`)

---

## 1. OVERVIEW

### What Changed

**REMOVED:**
- `medicine_symptoms` table (symptom text stored per medicine)
- `MedicineSymptom` model

**ADDED:**
- `symptoms` table (master symptom list)
- `symptom_aliases` table (search aliases)
- `medicine_symptom_mappings` table (medicine ↔ symptom relationships)

### Why

**Old Problems:**
- Duplicated data ("Headache" stored 100+ times)
- Inconsistent text ("headache" vs "Headache" vs "Head ache")
- No alias support (can't search "matha byatha" → "Headache")
- Poor search performance (full-text on duplicated fields)

**New Benefits:**
- Single source of truth (one "Headache" entry)
- Alias support (multiple search terms per symptom)
- Categorization (symptoms grouped by system)
- Better search (indexed aliases + trigram)
- Scalable (easy to add symptoms/aliases)

---

## 2. OLD vs NEW

### Database Schema

**OLD (Deleted):**
```sql
CREATE TABLE medicine_symptoms (
    id INTEGER PRIMARY KEY,
    medicine_id INTEGER,
    symptom_en VARCHAR(500),      -- ❌ Text (duplicated)
    symptom_bn VARCHAR(500),       -- ❌ Text (duplicated)
    modality_en TEXT,
    modality_bn TEXT,
    strength INTEGER
);
```

**NEW (Current):**
```sql
-- Master symptom list
CREATE TABLE symptoms (
    id INTEGER PRIMARY KEY,
    name_en VARCHAR(500),
    name_bn VARCHAR(500),
    description_en TEXT,
    description_bn TEXT,
    category VARCHAR(100),         -- ✅ "neurological", "respiratory"
    is_global BOOLEAN
);

-- Search aliases
CREATE TABLE symptom_aliases (
    id INTEGER PRIMARY KEY,
    symptom_id INTEGER REFERENCES symptoms(id),  -- ✅ FK
    alias_en VARCHAR(500),         -- ✅ "matha byatha", "migraine"
    alias_bn VARCHAR(500),
    alias_type VARCHAR(50),        -- ✅ "transliteration", "common_name"
    priority INTEGER
);

-- Medicine ↔ Symptom relationships
CREATE TABLE medicine_symptom_mappings (
    id INTEGER PRIMARY KEY,
    medicine_id INTEGER REFERENCES medicines(id),  -- ✅ FK
    symptom_id INTEGER REFERENCES symptoms(id),    -- ✅ FK (normalized!)
    modality_en TEXT,
    modality_bn TEXT,
    strength INTEGER
);
```

### Python Models

**OLD (Deleted):**
```python
class MedicineSymptom(TenantScopedModel):
    symptom_en: Mapped[str]  # Free text
    symptom_bn: Mapped[str | None]
    medicine: Mapped["Medicine"] = relationship(...)
```

**NEW (Current):**
```python
class Symptom(TenantScopedModel):
    name_en: Mapped[str]
    name_bn: Mapped[str | None]
    category: Mapped[str]
    aliases: Mapped[list["SymptomAlias"]] = relationship(...)

class SymptomAlias(TenantScopedModel):
    symptom_id: Mapped[int]  # FK
    alias_en: Mapped[str | None]
    alias_bn: Mapped[str | None]
    alias_type: Mapped[str]

class MedicineSymptomMapping(TenantScopedModel):
    medicine_id: Mapped[int]  # FK
    symptom_id: Mapped[int]   # FK (normalized!)
    strength: Mapped[int]
```

---

## 3. MIGRATION PATH

### Update Imports

**OLD (Will Fail):**
```python
from app.shared.models import MedicineSymptom

symptom = MedicineSymptom(
    medicine_id=1,
    symptom_en="Headache",  # ❌ Text-based
    symptom_bn="মাথা ব্যথা"
)
```

**NEW (Use This):**
```python
from app.shared.models import Symptom, SymptomAlias, MedicineSymptomMapping

# 1. Create or find symptom (one time)
symptom = Symptom(
    name_en="Headache",
    name_bn="মাথা ব্যথা",
    category="neurological"
)
session.add(symptom)

# 2. Add aliases (optional)
alias = SymptomAlias(
    symptom_id=symptom.id,
    alias_en="matha byatha",
    alias_type="transliteration"
)
session.add(alias)

# 3. Create medicine-symptom mapping
mapping = MedicineSymptomMapping(
    medicine_id=1,
    symptom_id=symptom.id,  # ✅ FK reference
    strength=8
)
session.add(mapping)
```

### Update Queries

**OLD (Will Fail):**
```python
# Search by symptom text
results = session.query(Medicine).join(MedicineSymptom).filter(
    MedicineSymptom.symptom_en.ilike("%headache%")
).all()
```

**NEW (Use This):**
```python
# Basic search
results = (
    session.query(Medicine)
    .join(MedicineSymptomMapping)
    .join(Symptom)
    .filter(Symptom.name_en.ilike("%headache%"))
    .all()
)

# Search with alias support
from sqlalchemy import or_

results = (
    session.query(Medicine)
    .join(MedicineSymptomMapping)
    .join(Symptom)
    .outerjoin(SymptomAlias)  # Include aliases
    .filter(
        or_(
            Symptom.name_en.ilike("%headache%"),
            SymptomAlias.alias_en.ilike("%headache%")
        )
    )
    .distinct()
    .all()
)
```

### Pre-Migration Checklist

- [ ] No code imports `MedicineSymptom`
- [ ] No API endpoints reference `medicine_symptoms` table
- [ ] No frontend code depends on old symptom structure
- [ ] Ready to seed new `symptoms` and `symptom_aliases` tables

### Post-Migration Verification

- [ ] Old table `medicine_symptoms` is gone
- [ ] New tables created: `symptoms`, `symptom_aliases`, `medicine_symptom_mappings`
- [ ] All FK constraints working
- [ ] Indexes created

---

## 4. DATA MIGRATION

### Step 1: Run Migration

```bash
alembic upgrade head
```

### Step 2: Populate Symptoms

```python
# Seed common symptoms (one time)
symptoms = [
    Symptom(
        name_en="Headache",
        name_bn="মাথা ব্যথা",
        category="neurological",
        is_global=True
    ),
    Symptom(
        name_en="Fever",
        name_bn="জ্বর",
        category="general",
        is_global=True
    ),
    Symptom(
        name_en="Cough",
        name_bn="কাশি",
        category="respiratory",
        is_global=True
    ),
]
session.add_all(symptoms)
session.commit()
```

### Step 3: Populate Aliases

```python
# Add search aliases (critical for Bangladesh users)
aliases = [
    # Headache aliases
    SymptomAlias(
        symptom_id=1,
        alias_en="matha byatha",
        alias_type="transliteration",
        priority=1
    ),
    SymptomAlias(
        symptom_id=1,
        alias_en="migraine",
        alias_type="common_name",
        priority=2
    ),
    # Fever aliases
    SymptomAlias(
        symptom_id=2,
        alias_en="jor",
        alias_type="transliteration",
        priority=1
    ),
]
session.add_all(aliases)
session.commit()
```

### Step 4: Create Mappings

```python
# Link medicines to symptoms
mappings = [
    MedicineSymptomMapping(
        medicine_id=1,
        symptom_id=1,  # Headache
        strength=9,
        modality_en="Worse from noise, light"
    ),
    MedicineSymptomMapping(
        medicine_id=2,
        symptom_id=1,  # Headache
        strength=7,
        modality_en="Better from pressure"
    ),
]
session.add_all(mappings)
session.commit()
```

---

## 5. REFERENCE

### Rollback

**If needed, rollback to old structure:**
```bash
alembic downgrade -1
```

**Warning:** All data in new tables (`symptoms`, `symptom_aliases`, `medicine_symptom_mappings`) will be lost.

### Support Resources

- **MIGRATION_GUIDE.md** - Detailed migration instructions
- **ALIAS_DATA_EXAMPLES.md** - Sample data for aliases
- **CLAUDE.md** - Architecture patterns

### Design Decision

This migration **intentionally breaks** backward compatibility to:
- Enforce clean, normalized data structure from day one
- Enable Bangladesh-first search (Bengali transliterations)
- Prevent maintaining two parallel systems
- Improve search performance and data quality

The old text-based approach is **completely removed**. All new code must use the normalized structure.
