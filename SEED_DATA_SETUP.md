# 🌱 Seed Data Setup - Complete

## ✅ What Was Created

### 1. Seed Data Files (`backend/seed_data/`)

| File | Content | Records |
|------|---------|---------|
| `geographic_data.json` | Bangladesh divisions, districts, upazilas | 8 + 64 + 10 |
| `integration_providers.json` | SMS, Email, Payment providers | 11 providers |
| `translations.json` | Bilingual UI strings (EN/BN) | 80+ keys |
| `sample_data.json` | Test tenants, users | 3 clinics, 6 users |
| `README.md` | Documentation for seed data | - |

### 2. Seed Scripts (`backend/scripts/`)

| File | Purpose |
|------|---------|
| `seed.py` | Main Python seed script (idempotent) |
| `run_seed.sh` | Helper bash script for easy execution |

---

## 📊 Seed Data Details

### Geographic Data
- **8 Divisions**: All Bangladesh divisions with Bengali names
- **64 Districts**: Complete district list with division mappings
- **10 Upazilas**: Sample upazilas from major cities (expandable to 490+)
- **Includes**: Latitude/longitude coordinates for each location

### Integration Providers

**SMS (3 providers):**
- Twilio (international)
- Banglalink SMS Gateway (Bangladesh)
- Robi SMS Gateway (Bangladesh)

**Email (3 providers):**
- SendGrid
- Amazon SES
- Generic SMTP

**Payment (5 providers):**
- bKash (Bangladesh)
- Nagad (Bangladesh)
- Rocket (Bangladesh)
- SSLCommerz (Bangladesh)
- Stripe (international)

### Translations
- **80+ UI strings** in English and Bengali
- **Categories**: common, dashboard, patient, prescription, payment, appointment, medicine, settings, auth, error, success
- **Format**: Dot notation (e.g., `dashboard.welcome`)

### Sample Data

**3 Test Clinics:**
1. **Dr. Rahman's Homeopathy Clinic** (Dhaka, Pro plan)
   - Specialization: Homeopathy
   - Location: Dhanmondi, Dhaka
   
2. **Dr. Karim's Ayurvedic Center** (Dhaka, Plus plan)
   - Specializations: Ayurveda, Herbal
   - Location: Gulshan, Dhaka
   
3. **Dr. Ahmed's Integrated Clinic** (Chittagong, Free plan)
   - Specializations: Homeopathy, Ayurveda, Unani
   - Location: Chittagong

**6 Test Users:**
- 3 Doctors (one per clinic)
- 1 Receptionist (Dr. Rahman's clinic)
- 1 Platform Admin (no tenant)
- 1 Platform Operator (no tenant)

---

## 🚀 How to Run the Seed Script

### Option 1: Using the Helper Script (Recommended)

```bash
cd backend
./scripts/run_seed.sh
```

This script will:
- Check if Docker is running
- Start database if needed
- Activate virtual environment
- Run the seed script
- Show summary

### Option 2: Manual Execution

```bash
# 1. Start Docker services
docker compose up -d

# 2. Activate virtual environment
cd backend
source venv/bin/activate

# 3. Run seed script
python scripts/seed.py
```

### Expected Output

```
============================================================
🌱 AltCare Database Seeding
============================================================

📍 Seeding geographic data...
🔌 Seeding integration providers...
🌐 Seeding translations...
👥 Seeding sample tenants and users...

============================================================
✅ Seeding completed successfully!
============================================================

📊 Summary:
  • Divisions:       8 created
  • Districts:      64 created
  • Upazilas:       10 created
  • Providers:      11 created
  • Translations:   80 created
  • Tenants:         3 created
  • Users:           6 created

💡 Test credentials:
  • Doctor:     dr.rahman@example.com / Test@1234
  • Admin:      admin@altcare.com / Admin@1234
  • Operator:   operator@altcare.com / Operator@1234
```

---

## 🧪 Test the Seeded Data

### 1. Test Login API

```bash
# Login as Dr. Rahman
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "dr.rahman@example.com",
    "password": "Test@1234"
  }'

# Expected: JWT tokens in response
```

### 2. Test Geographic Data

```bash
# Query divisions (requires database access)
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "SELECT id, name_en, name_bn FROM divisions;"
```

### 3. Test Integration Providers

```bash
# Query providers
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "SELECT name, display_name, provider_type FROM integration_providers;"
```

### 4. Test Translations

```bash
# Query translations
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "SELECT key, text_en, text_bn, category FROM translations LIMIT 10;"
```

---

## 🔑 Test Credentials

| Email | Password | Role | Tenant |
|-------|----------|------|--------|
| dr.rahman@example.com | Test@1234 | Doctor | Dr. Rahman's Clinic |
| receptionist.dhanmondi@example.com | Test@1234 | Receptionist | Dr. Rahman's Clinic |
| dr.karim@example.com | Test@1234 | Doctor | Dr. Karim's Center |
| dr.ahmed@example.com | Test@1234 | Doctor | Dr. Ahmed's Clinic |
| admin@altcare.com | Admin@1234 | Admin | Platform (no tenant) |
| operator@altcare.com | Operator@1234 | Operator | Platform (no tenant) |

---

## 🔄 Re-running the Seed Script

The seed script is **idempotent** - it safely checks if data exists before inserting.

**What happens when you re-run:**
- Existing data is skipped (no duplicates)
- New data is added
- No errors for duplicate keys
- Transaction rolls back if any error occurs

**When to re-run:**
- After database reset
- After adding new seed data files
- When testing in a fresh environment

---

## 📝 Adding More Data

### Add More Upazilas

Edit `backend/seed_data/geographic_data.json`:

```json
{
  "upazilas": [
    {
      "id": 11,
      "district_id": 1,
      "name_en": "Savar",
      "name_bn": "সাভার",
      "latitude": 23.8583,
      "longitude": 90.2667
    }
  ]
}
```

### Add Translation Keys

Edit `backend/seed_data/translations.json`:

```json
{
  "translations": [
    {
      "key": "new.feature",
      "text_en": "New Feature",
      "text_bn": "নতুন ফিচার",
      "category": "feature"
    }
  ]
}
```

### Add Integration Providers

Edit `backend/seed_data/integration_providers.json` with proper config schema.

---

## 🐛 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop
open -a Docker  # macOS
# or start Docker Desktop manually
```

### Error: "Could not connect to database"

**Solution:**
```bash
# Start database container
docker compose up -d postgres

# Wait a few seconds
sleep 5

# Try again
python scripts/seed.py
```

### Error: "ModuleNotFoundError"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -e .
```

### Error: "Duplicate key value violates unique constraint"

**This is normal!** The data already exists. The script skips existing records.

---

## ✅ Verification Checklist

After running the seed script, verify:

- [ ] Script completed without errors
- [ ] Summary shows created records
- [ ] Can login with test credentials
- [ ] Database contains 8 divisions, 64 districts
- [ ] Database contains 11 integration providers
- [ ] Database contains 80+ translation keys
- [ ] Database contains 3 tenants, 6 users

### Quick Verification

```bash
# Count records in each table
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "
SELECT 
  (SELECT COUNT(*) FROM divisions) as divisions,
  (SELECT COUNT(*) FROM districts) as districts,
  (SELECT COUNT(*) FROM upazilas) as upazilas,
  (SELECT COUNT(*) FROM integration_providers) as providers,
  (SELECT COUNT(*) FROM translations) as translations,
  (SELECT COUNT(*) FROM tenants) as tenants,
  (SELECT COUNT(*) FROM users) as users;
"
```

---

## 🎯 Next Steps

Now that seed data is complete, you can proceed with:

1. **Patient Management API** - Build CRUD endpoints for patients
2. **Doctor Profile API** - Build profile and credentials management
3. **Appointments Integration** - Integrate the appointments module
4. **Frontend Development** - Start building the UI with real data

---

## 📚 Related Documentation

- [Seed Data README](backend/seed_data/README.md) - Detailed data documentation
- [Database Schema](docs/architecture/database.md) - Full schema documentation
- [API Documentation](http://localhost:8000/docs) - Swagger UI (when running)
- [Getting Started](GETTING_STARTED.md) - Project setup guide

---

## ⚠️ Security Warning

**Do not use seed data in production!**

- Sample passwords are weak and publicly known
- Sample users are for development/testing only
- Always create real tenants through registration
- Enable 2FA for production accounts
- Delete or disable sample accounts before launch

---

**Created:** April 24, 2026  
**Status:** ✅ Complete and tested  
**Next Task:** Patient Management API
