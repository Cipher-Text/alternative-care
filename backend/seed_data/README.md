# Seed Data

This directory contains JSON files used to populate the AltCare database with initial data.

## Files

### `geographic_data.json`
Bangladesh geographic hierarchy for address management.

**Contents:**
- **8 Divisions** - All administrative divisions of Bangladesh with Bengali names
- **64 Districts** - All districts with division mappings
- **10 Sample Upazilas** - Representative upazilas from major districts (expandable to 490+)

**Format:**
```json
{
  "divisions": [
    {
      "id": 1,
      "name_en": "Dhaka",
      "name_bn": "ঢাকা",
      "latitude": 23.8103,
      "longitude": 90.4125
    }
  ],
  "districts": [...],
  "upazilas": [...]
}
```

### `integration_providers.json`
Catalog of available integration providers for SMS, Email, and Payment processing.

**Contents:**
- **SMS Providers** (3): Twilio, Banglalink SMS Gateway, Robi SMS Gateway
- **Email Providers** (3): SendGrid, Amazon SES, Generic SMTP
- **Payment Providers** (5): bKash, Nagad, Rocket, SSLCommerz, Stripe

**Format:**
```json
{
  "providers": [
    {
      "name": "twilio",
      "display_name": "Twilio",
      "provider_type": "sms",
      "description": "...",
      "logo_url": "...",
      "config_schema": {...},
      "supported_countries": ["US", "CA", "BD", ...],
      "is_active": true
    }
  ]
}
```

### `translations.json`
Bilingual UI strings (English/Bengali) for the frontend interface.

**Contents:**
- **80+ translation keys** organized by category
- Categories: common, dashboard, patient, prescription, payment, appointment, medicine, settings, auth, error, success

**Format:**
```json
{
  "translations": [
    {
      "key": "dashboard.welcome",
      "text_en": "Welcome",
      "text_bn": "স্বাগতম",
      "category": "dashboard"
    }
  ]
}
```

### `sample_data.json`
Sample tenants and users for testing and development.

**Contents:**
- **3 Sample Tenants (Clinics):**
  - Dr. Rahman's Homeopathy Clinic (Dhaka, Pro plan)
  - Dr. Karim's Ayurvedic Center (Dhaka, Plus plan)
  - Dr. Ahmed's Integrated Clinic (Chittagong, Free plan)

- **6 Sample Users:**
  - 3 Doctors (one per clinic)
  - 1 Receptionist
  - 1 Platform Admin
  - 1 Platform Operator

**Test Credentials:**
- Doctors/Receptionists: `Test@1234`
- Platform Admin: `admin@altcare.com` / `Admin@1234`
- Platform Operator: `operator@altcare.com` / `Operator@1234`

**Format:**
```json
{
  "tenants": [...],
  "users": [...],
  "notes": {
    "passwords": "...",
    "tenant_ids": {...},
    "specializations": {...},
    "roles": {...},
    "plans": {...}
  }
}
```

## Usage

Run the seed script to populate the database:

```bash
# From backend directory
python scripts/seed.py

# Or with virtual environment
source venv/bin/activate
python scripts/seed.py
```

The seed script is **idempotent** - it checks for existing data before inserting, so it can be run multiple times safely.

## Data Statistics

| Type | Count | Description |
|------|-------|-------------|
| Divisions | 8 | All Bangladesh divisions |
| Districts | 64 | All Bangladesh districts |
| Upazilas | 10+ | Sample upazilas (expandable to 490+) |
| Integration Providers | 11 | SMS, Email, and Payment providers |
| Translations | 80+ | Bilingual UI strings (EN/BN) |
| Sample Tenants | 3 | Test clinics |
| Sample Users | 6 | Test users (doctors, staff, admins) |

## Expanding Data

### Adding More Upazilas

To add more upazilas, edit `geographic_data.json` and add entries to the `upazilas` array:

```json
{
  "id": 11,
  "district_id": 1,
  "name_en": "Savar",
  "name_bn": "সাভার",
  "latitude": 23.8583,
  "longitude": 90.2667
}
```

### Adding Custom Translations

Add new translation keys to `translations.json`:

```json
{
  "key": "feature.new_feature",
  "text_en": "New Feature",
  "text_bn": "নতুন ফিচার",
  "category": "feature"
}
```

### Adding Integration Providers

Add new providers to `integration_providers.json` with proper config schema.

## Notes

- All passwords in `sample_data.json` are hashed by the seed script before insertion
- Geographic coordinates are included for potential mapping features
- Integration provider config schemas define required credentials
- Translation keys follow dot notation (category.key)
- Sample data is for development/testing only

## Security Warning

⚠️ **Do not use sample credentials in production!**

The sample users and passwords are for development and testing only. Always:
1. Create new tenants through the registration flow in production
2. Use strong, unique passwords
3. Enable 2FA for sensitive accounts
4. Delete or disable sample accounts before going live

---

**Last Updated:** April 24, 2026  
**Maintained By:** AltCare Development Team
