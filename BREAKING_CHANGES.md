# Breaking Changes - Migration 001

**Migration**: 001_phase1a_tables  
**Date**: 2026-04-23  
**Type**: BREAKING - No Backward Compatibility

---

## ⚠️ Breaking Change: medicine_symptoms Table Dropped

### What Was Removed

**Table**: `medicine_symptoms`

**Old Structure** (DELETED):
```sql
CREATE TABLE medicine_symptoms (
    id INTEGER PRIMARY KEY,
    medicine_id INTEGER,
    symptom_en VARCHAR(500),      -- ❌ Text field (duplicated)
    symptom_bn VARCHAR(500),       -- ❌ Text field (duplicated)
    modality_en TEXT,
    modality_bn TEXT,
    strength INTEGER
);
```

**Old Model** (DELETED):
```python
class MedicineSymptom(TenantScopedModel):
    symptom_en: Mapped[str]  # Free text
    symptom_bn: Mapped[str | None]
    medicine: Mapped["Medicine"] = relationship(...)
```

---

## ✅ What Replaces It

### New Normalized Structure

**3 New Tables**:

1. **`symptoms`** - Master symptom list
```sql
CREATE TABLE symptoms (
    id INTEGER PRIMARY KEY,
    name_en VARCHAR(500),
    name_bn VARCHAR(500),
    description_en TEXT,
    description_bn TEXT,
    category VARCHAR(100),
    is_global BOOLEAN
);
```

2. **`symptom_aliases`** - Search aliases
```sql
CREATE TABLE symptom_aliases (
    id INTEGER PRIMARY KEY,
    symptom_id INTEGER REFERENCES symptoms(id),
    alias_en VARCHAR(500),
    alias_bn VARCHAR(500),
    alias_type VARCHAR(50),
    priority INTEGER
);
```

3. **`medicine_symptom_mappings`** - Relationships
```sql
CREATE TABLE medicine_symptom_mappings (
    id INTEGER PRIMARY KEY,
    medicine_id INTEGER REFERENCES medicines(id),
    symptom_id INTEGER REFERENCES symptoms(id),  -- ✅ FK instead of text
    modality_en TEXT,
    modality_bn TEXT,
    strength INTEGER
);
```

**New Models**:
```python
class Symptom(TenantScopedModel):
    name_en: Mapped[str]
    name_bn: Mapped[str | None]
    aliases: Mapped[list["SymptomAlias"]] = relationship(...)

class SymptomAlias(TenantScopedModel):
    symptom_id: Mapped[int]  # FK
    alias_en: Mapped[str | None]
    alias_bn: Mapped[str | None]

class MedicineSymptomMapping(TenantScopedModel):
    medicine_id: Mapped[int]  # FK
    symptom_id: Mapped[int]   # FK (normalized!)
    strength: Mapped[int]
```

---

## 🔄 Migration Impact

### Code That Will Break

**Old Code** (will fail):
```python
from app.shared.models import MedicineSymptom

# This import no longer exists
symptom = MedicineSymptom(
    medicine_id=1,
    symptom_en="Headache",  # ❌ Text-based approach
    symptom_bn="মাথা ব্যথা"
)
```

**New Code** (use this):
```python
from app.shared.models import Symptom, MedicineSymptomMapping

# 1. Create or find symptom
symptom = Symptom(
    name_en="Headache",
    name_bn="মাথা ব্যথা",
    category="neurological"
)

# 2. Create mapping
mapping = MedicineSymptomMapping(
    medicine_id=1,
    symptom_id=symptom.id,  # ✅ FK reference
    strength=8
)
```

### Queries That Need Update

**Old Query** (will fail):
```python
# Search by symptom text
results = session.query(Medicine).join(MedicineSymptom).filter(
    MedicineSymptom.symptom_en.ilike("%headache%")
).all()
```

**New Query** (use this):
```python
# Search by symptom FK
results = session.query(Medicine).join(MedicineSymptomMapping).join(Symptom).filter(
    Symptom.name_en.ilike("%headache%")
).all()

# Or with alias support
results = session.query(Medicine).join(MedicineSymptomMapping).join(Symptom).join(SymptomAlias).filter(
    or_(
        Symptom.name_en.ilike("%headache%"),
        SymptomAlias.alias_en.ilike("%headache%")
    )
).all()
```

---

## 📋 Migration Checklist

Before running migration, check:

- [ ] No existing code imports `MedicineSymptom`
- [ ] No API endpoints reference `medicine_symptoms` table
- [ ] No frontend code depends on old symptom structure
- [ ] Ready to populate new `symptoms` and `symptom_aliases` tables

After running migration:

- [ ] Old table `medicine_symptoms` is gone
- [ ] New tables `symptoms`, `symptom_aliases`, `medicine_symptom_mappings` exist
- [ ] All FK constraints working
- [ ] Indexes created

---

## 💡 Why This Change?

### Problems with Old Approach

1. **Duplicated Data**: "Headache" stored 100+ times
2. **Inconsistent**: "headache" vs "Headache" vs "Head ache"
3. **No Aliases**: Can't search "matha byatha" → "Headache"
4. **Poor Search**: Full-text search on duplicated text fields
5. **No Categories**: Can't group symptoms

### Benefits of New Approach

1. **Single Source**: "Headache" stored once
2. **Consistent**: One canonical name per symptom
3. **Alias Support**: Multiple search terms per symptom
4. **Better Search**: Indexed aliases + trigram search
5. **Categorized**: Symptoms grouped by system
6. **Scalable**: Easy to add new symptoms/aliases

---

## 🎯 Data Migration Strategy

Since this is a **fresh start** (no data preservation):

### Step 1: Run Migration
```bash
alembic upgrade head
```

### Step 2: Populate Symptoms
```python
# Seed common symptoms
symptoms = [
    Symptom(name_en="Headache", name_bn="মাথা ব্যথা", category="neurological"),
    Symptom(name_en="Fever", name_bn="জ্বর", category="general"),
    Symptom(name_en="Cough", name_bn="কাশি", category="respiratory"),
    # ... more
]
```

### Step 3: Populate Aliases
```python
# Critical for Bangladesh search
aliases = [
    SymptomAlias(symptom_id=1, alias_en="matha byatha", alias_type="transliteration"),
    SymptomAlias(symptom_id=1, alias_en="migraine", alias_type="common_name"),
    # ... more
]
```

### Step 4: Create Mappings
```python
# Link medicines to symptoms
mappings = [
    MedicineSymptomMapping(medicine_id=1, symptom_id=1, strength=9),
    MedicineSymptomMapping(medicine_id=2, symptom_id=1, strength=7),
    # ... more
]
```

---

## 🚨 Rollback Instructions

If you need to rollback:

```bash
# This will recreate medicine_symptoms table
# and drop new symptom tables
alembic downgrade -1
```

**Note**: Any data in new tables will be lost.

---

## 📞 Support

If you encounter issues:

1. Check this document for migration patterns
2. Review `MIGRATION_GUIDE.md` for detailed instructions
3. See `ALIAS_DATA_EXAMPLES.md` for data examples

---

## ✅ Confirmed: No Backward Compatibility

This migration **intentionally breaks** backward compatibility to:
- Enforce clean, normalized data structure
- Enable Bangladesh-first search from day one
- Prevent maintaining two parallel systems

The old approach is **completely removed**. All code must use the new normalized structure.
