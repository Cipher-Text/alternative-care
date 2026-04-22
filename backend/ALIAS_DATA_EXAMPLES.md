# Alias Data Examples - Bangladesh Context

This document provides examples of alias data to populate for effective Bangladesh-first search.

---

## 🎯 Symptom Aliases Examples

### Common Symptoms

#### 1. Headache / মাথা ব্যথা

```python
symptom = Symptom(
    name_en="Headache",
    name_bn="মাথা ব্যথা",
    category="neurological",
    is_global=True
)

aliases = [
    # Transliteration
    SymptomAlias(alias_en="matha byatha", alias_type="transliteration", priority=9),
    SymptomAlias(alias_en="matha betha", alias_type="transliteration", priority=8),
    
    # Common names
    SymptomAlias(alias_en="head pain", alias_type="common_name", priority=7),
    SymptomAlias(alias_en="migraine", alias_type="common_name", priority=6),
    SymptomAlias(alias_en="severe headache", alias_type="common_name", priority=6),
    
    # Regional/colloquial
    SymptomAlias(alias_bn="মাথায় যন্ত্রণা", alias_type="regional", priority=7),
    SymptomAlias(alias_bn="মাথা ঘোরা", alias_type="regional", priority=5),
]
```

#### 2. Fever / জ্বর

```python
symptom = Symptom(
    name_en="Fever",
    name_bn="জ্বর",
    category="general",
    is_global=True
)

aliases = [
    # Transliteration
    SymptomAlias(alias_en="jor", alias_type="transliteration", priority=9),
    SymptomAlias(alias_en="jhor", alias_type="transliteration", priority=8),
    
    # Common names
    SymptomAlias(alias_en="high fever", alias_type="common_name", priority=7),
    SymptomAlias(alias_en="temperature", alias_type="common_name", priority=6),
    
    # Regional
    SymptomAlias(alias_bn="শরীর গরম", alias_type="regional", priority=7),
]
```

#### 3. Stomach Pain / পেট ব্যথা

```python
symptom = Symptom(
    name_en="Stomach Pain",
    name_bn="পেট ব্যথা",
    category="digestive",
    is_global=True
)

aliases = [
    # Transliteration
    SymptomAlias(alias_en="pet byatha", alias_type="transliteration", priority=9),
    SymptomAlias(alias_en="pet betha", alias_type="transliteration", priority=8),
    
    # Common names
    SymptomAlias(alias_en="abdominal pain", alias_type="common_name", priority=7),
    SymptomAlias(alias_en="stomach ache", alias_type="common_name", priority=7),
    SymptomAlias(alias_en="belly pain", alias_type="common_name", priority=6),
    
    # Regional
    SymptomAlias(alias_bn="পেটে ব্যথা", alias_type="regional", priority=8),
    SymptomAlias(alias_bn="পেট কামড়ানো", alias_type="regional", priority=6),
]
```

#### 4. Cough / কাশি

```python
symptom = Symptom(
    name_en="Cough",
    name_bn="কাশি",
    category="respiratory",
    is_global=True
)

aliases = [
    # Transliteration
    SymptomAlias(alias_en="kashi", alias_type="transliteration", priority=9),
    SymptomAlias(alias_en="kasi", alias_type="transliteration", priority=8),
    
    # Common names
    SymptomAlias(alias_en="dry cough", alias_type="common_name", priority=6),
    SymptomAlias(alias_en="wet cough", alias_type="common_name", priority=6),
    
    # Regional
    SymptomAlias(alias_bn="শুকনা কাশি", alias_type="regional", priority=6),
]
```

#### 5. Joint Pain / গাঁটে ব্যথা

```python
symptom = Symptom(
    name_en="Joint Pain",
    name_bn="গাঁটে ব্যথা",
    category="musculoskeletal",
    is_global=True
)

aliases = [
    # Transliteration
    SymptomAlias(alias_en="gante byatha", alias_type="transliteration", priority=9),
    
    # Common names
    SymptomAlias(alias_en="arthritis", alias_type="common_name", priority=6),
    SymptomAlias(alias_en="knee pain", alias_type="common_name", priority=6),
    SymptomAlias(alias_en="joint ache", alias_type="common_name", priority=7),
    
    # Regional
    SymptomAlias(alias_bn="হাড়ের ব্যথা", alias_type="regional", priority=6),
]
```

---

## 💊 Medicine Aliases Examples

### Homeopathy Medicines

#### 1. Arnica Montana

```python
medicine = Medicine(
    name_en="Arnica Montana",
    name_bn="আর্নিকা মন্টানা",
    system="homeopathy"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="arnika", alias_type="transliteration", priority=8),
    MedicineAlias(alias_en="arnica", alias_type="transliteration", priority=9),
    MedicineAlias(alias_bn="আর্নিকা", alias_type="transliteration", priority=8),
    
    # Common names
    MedicineAlias(alias_en="leopard's bane", alias_type="common_name", priority=5),
    MedicineAlias(alias_en="mountain tobacco", alias_type="common_name", priority=5),
    
    # Short forms
    MedicineAlias(alias_en="arn", alias_type="common_name", priority=6),
]
```

#### 2. Belladonna

```python
medicine = Medicine(
    name_en="Belladonna",
    name_bn="বেলাডোনা",
    system="homeopathy"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="beladonna", alias_type="transliteration", priority=8),
    MedicineAlias(alias_bn="বেল্লাডোনা", alias_type="transliteration", priority=7),
    
    # Common names
    MedicineAlias(alias_en="deadly nightshade", alias_type="common_name", priority=5),
    
    # Short forms
    MedicineAlias(alias_en="bell", alias_type="common_name", priority=7),
]
```

#### 3. Nux Vomica

```python
medicine = Medicine(
    name_en="Nux Vomica",
    name_bn="নাক্স ভমিকা",
    system="homeopathy"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="nux vom", alias_type="transliteration", priority=8),
    MedicineAlias(alias_en="nux", alias_type="transliteration", priority=7),
    
    # Common names
    MedicineAlias(alias_en="poison nut", alias_type="common_name", priority=5),
    
    # Short forms
    MedicineAlias(alias_en="nux-v", alias_type="common_name", priority=7),
]
```

### Ayurveda Medicines

#### 4. Ashwagandha

```python
medicine = Medicine(
    name_en="Ashwagandha",
    name_bn="অশ্বগন্ধা",
    system="ayurveda"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="ashwagandha", alias_type="transliteration", priority=9),
    MedicineAlias(alias_en="aswagandha", alias_type="transliteration", priority=8),
    
    # Common names (English)
    MedicineAlias(alias_en="indian ginseng", alias_type="common_name", priority=7),
    MedicineAlias(alias_en="winter cherry", alias_type="common_name", priority=6),
    
    # Scientific
    MedicineAlias(alias_en="withania somnifera", alias_type="common_name", priority=5),
]
```

#### 5. Triphala

```python
medicine = Medicine(
    name_en="Triphala",
    name_bn="ত্রিফলা",
    system="ayurveda"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="triphala", alias_type="transliteration", priority=9),
    MedicineAlias(alias_en="tripala", alias_type="transliteration", priority=7),
    
    # Common names
    MedicineAlias(alias_en="three fruits", alias_type="common_name", priority=6),
]
```

### Unani Medicines

#### 6. Habbe Muqil

```python
medicine = Medicine(
    name_en="Habbe Muqil",
    name_bn="হাব্বে মুকিল",
    system="unani"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="habb e muqil", alias_type="transliteration", priority=8),
    MedicineAlias(alias_en="habbe mukil", alias_type="transliteration", priority=7),
]
```

### Herbal Medicines

#### 7. Tulsi / Holy Basil

```python
medicine = Medicine(
    name_en="Tulsi",
    name_bn="তুলসী",
    system="herbal"
)

aliases = [
    # Transliteration
    MedicineAlias(alias_en="tulsi", alias_type="transliteration", priority=9),
    MedicineAlias(alias_en="tulshi", alias_type="transliteration", priority=7),
    
    # Common names
    MedicineAlias(alias_en="holy basil", alias_type="common_name", priority=8),
    MedicineAlias(alias_en="sacred basil", alias_type="common_name", priority=7),
    
    # Scientific
    MedicineAlias(alias_en="ocimum sanctum", alias_type="common_name", priority=5),
]
```

---

## 📊 Alias Type Guidelines

### Priority Levels (1-10)

- **9-10**: Exact transliteration or primary common name
- **7-8**: Close variations, common alternatives
- **5-6**: Secondary names, scientific names
- **3-4**: Rare variations
- **1-2**: Very rare or regional-specific

### Alias Types

1. **transliteration**: Bangla → English phonetic spelling
2. **common_name**: Widely used alternative names
3. **brand_name**: Commercial/manufacturer names
4. **regional**: Regional variations in Bangladesh
5. **colloquial**: Everyday informal terms

---

## 🔍 Search Testing Examples

### Test Cases to Validate

```python
# Test 1: English → Medicine
search("headache") 
# Should find: Belladonna, Nux Vomica, etc.

# Test 2: Bengali → Medicine
search("মাথা ব্যথা") 
# Should find: Same medicines

# Test 3: Transliteration → Medicine
search("matha byatha") 
# Should find: Same medicines

# Test 4: Partial match
search("matha") 
# Should find: Headache-related symptoms

# Test 5: Medicine transliteration
search("arnika") 
# Should find: Arnica Montana

# Test 6: Common name
search("indian ginseng") 
# Should find: Ashwagandha
```

---

## 📝 Data Population Workflow

### Step 1: Core Symptoms (High Priority)

Start with 20-30 most common symptoms:
- Headache, Fever, Cough, Cold
- Stomach pain, Diarrhea, Constipation
- Joint pain, Back pain
- Skin rash, Itching
- Anxiety, Insomnia

### Step 2: Add Aliases

For each symptom, add:
- 2-3 transliteration variants
- 3-5 common name variants
- 1-2 regional variants

### Step 3: Common Medicines

Add 50-100 commonly prescribed medicines per system:
- Homeopathy: Arnica, Belladonna, Nux Vomica, etc.
- Ayurveda: Ashwagandha, Triphala, Brahmi, etc.
- Unani: Habbe Muqil, Arq-e-Gulab, etc.
- Herbal: Tulsi, Neem, Turmeric, etc.

### Step 4: Add Medicine Aliases

For each medicine:
- 1-2 transliteration variants
- 1-2 common names
- Brand names (if applicable)

### Step 5: Test & Iterate

- Test with real doctors
- Collect search queries that fail
- Add missing aliases
- Adjust priority scores

---

## 🎯 Quick Import Script Template

```python
# scripts/populate_aliases.py

from app.shared.models import Symptom, SymptomAlias, Medicine, MedicineAlias

SYMPTOMS_DATA = [
    {
        "name_en": "Headache",
        "name_bn": "মাথা ব্যথা",
        "category": "neurological",
        "aliases": [
            ("matha byatha", "transliteration", 9),
            ("matha betha", "transliteration", 8),
            ("head pain", "common_name", 7),
        ]
    },
    # ... more symptoms
]

async def populate_symptoms():
    for data in SYMPTOMS_DATA:
        symptom = Symptom(
            tenant_id="GLOBAL",
            name_en=data["name_en"],
            name_bn=data["name_bn"],
            category=data["category"],
            is_global=True
        )
        db.add(symptom)
        await db.flush()
        
        for alias_en, alias_type, priority in data["aliases"]:
            alias = SymptomAlias(
                tenant_id="GLOBAL",
                symptom_id=symptom.id,
                alias_en=alias_en,
                alias_type=alias_type,
                priority=priority,
                is_global=True
            )
            db.add(alias)
    
    await db.commit()
```

---

## ✅ Success Metrics

Your alias data is sufficient when:

- [ ] 90%+ of doctor searches return results
- [ ] Bengali search works as well as English
- [ ] Transliteration search works
- [ ] Common misspellings are handled
- [ ] Regional terms are recognized

---

This is the **critical work** that makes the Bangladesh-first search actually work!
