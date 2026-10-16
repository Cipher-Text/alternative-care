# Seed Data

This directory contains JSON files used to populate the AltCare database with initial data.

## Files

### `geographic_data.json`
Bangladesh geographic hierarchy for address management.

**Contents:**
- **8 Divisions** - All administrative divisions of Bangladesh with Bengali names
- **64 Districts** - All districts with division mappings
- **495 Upazilas** - All current upazilas with district mappings and coordinates

Upazila coordinates are approximate WGS84 latitude/longitude points. Most are derived from online administrative boundary geometry centroids; newer upazilas that are missing from the boundary layer use online point-coordinate references.

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
- **SMS Providers** (4): Twilio, Banglalink SMS Gateway, Robi SMS Gateway, BulkSMSBD
- **Email Providers** (3): SendGrid, Amazon SES, Generic SMTP
- **Payment Providers** (5): bKash, Nagad, Rocket, SSLCommerz, Stripe
- **Provider Logos**: Stable local frontend assets under `/integrations/*`; seeded `logo_url` values should not depend on external vendor CDN URLs.

**Format:**
```json
{
  "providers": [
    {
      "name": "twilio",
      "display_name": "Twilio",
      "provider_type": "sms",
      "description": "...",
      "logo_url": "/integrations/twilio.svg",
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
- **80 translation keys** organized by category
- Categories: common, dashboard, patient, prescription, payment, appointment, medicine, settings, auth, error, success

### `medicines.json`
Starter medicine catalog seeded per medical system (Homeopathy, Ayurveda, Unani, Herbal).

**Contents:**
- **14 medicines** with bilingual names, potency/dosage guidance, and indications

### `symptoms.json`
Starter symptom catalog used for medicine-symptom lookups.

**Contents:**
- **25 symptoms** with bilingual names and categories

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
| Upazilas | 495 | All current upazilas with coordinates |
| Integration Providers | 12 | SMS, Email, and Payment providers |
| Translations | 80 | Bilingual UI strings (EN/BN) |
| Medicines | 14 | Starter medicine catalog |
| Symptoms | 25 | Starter symptom catalog |
| Sample Tenants | 3 | Test clinics |
| Sample Users | 6 | Test users (doctors, staff, admins) |

## Maintaining Data

### Updating Upazilas

To update upazilas after administrative changes, edit `geographic_data.json` and keep entries in the `upazilas` array in this format:

```json
{
  "id": 496,
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

Add new providers to `integration_providers.json` with a proper config schema and a stable local logo path. Frontend logo assets live in `frontend/public/integrations/`, and `frontend/src/lib/integration-logos.ts` should be updated so already-seeded databases also render the right logo.

## Notes

- All passwords in `sample_data.json` are hashed by the seed script before insertion
- Geographic coordinates are included for potential mapping features
- Integration provider config schemas define required credentials
- Integration provider `logo_url` values point to local frontend assets for reliable settings UI rendering
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

**Last Updated:** May 29, 2026  
**Maintained By:** AltCare Development Team

## Catalogue (medicines, symptoms, aliases, mappings)

`medicines.json`, `symptoms.json`, `medicine_aliases.json`, `symptom_aliases.json` and `medicine_symptom_mappings.json` are
**generated** from `raw/` plus the human decisions in `backend/scripts/catalogue/curation.py`. Do not edit them by hand:

```bash
cd backend && venv/bin/python -m scripts.catalogue.build          # rewrite seed_data/ and print what changed vs raw/
venv/bin/python -m scripts.catalogue.build --check                # fail if seed_data/ is stale
```

What the build changes from `raw/`: potency `"Not specified"` becomes null; the "no evidence-based dose" text is dropped from the
dosage field (it stays in the description, so nothing can be copied into a prescription as a dose); raw `aliases_*` become alias
rows alongside the curated common names; medicine to symptom links are regenerated from the indication text by whole-word match
inside a clause, skipping negated and look-alike phrases ("croup-like", "no thirst during fever", "diabetic carbuncle"), with a
`strength` of 2 to 5 (2 = only a very general word matched; higher = named early in the text or by several terms).
The links record *traditional associations from the source text, not evidence of efficacy*; the UI must keep saying so.

`scripts/seed.py` seeds all five files: rows that already exist are **completed** (empty columns filled, old placeholders cleared)
but never overwritten, and an existing alias or link (including a strength an admin changed) is left alone, so it is safe to rerun.
Symptoms with no medicine yet: Conjunctivitis, Croup, Frequent Urination, Herpes, Laryngitis, Migraine, Vertigo.

## Articles and videos (`articles.json`)

10 Bangla blog posts and 5 Bangla videos/podcasts for the public `/articles` section, seeded by `seed.py` as **published**, owned by the
first platform admin, credited to "AltCare সম্পাদকীয় দল". The posts were written for the platform and **no practitioner has reviewed them**,
so no reviewer is recorded and the public page shows no "reviewed by" line; have a clinician read them, then put each in review and
publish with their name. The five videos are real YouTube videos by third-party channels (checked embeddable via oEmbed on 2026-10-17);
their views are the channels' own, which each video's text says. Existing slugs are never overwritten.
