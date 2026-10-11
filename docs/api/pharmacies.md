# Pharmacies API

Admin-curated directory of pharmacies, wholesalers, manufacturers and depots where practitioners
buy alternative-medicine stock. **Global** — no `tenant_id`, same shape as Institutions. Every
authenticated user can read; only platform admins write. Accuracy depends on that curation, so each
row carries `source_url`, `is_verified`, and `last_confirmed_at` (show it in the UI so a stale
listing is visibly stale).

Base path: `/api/v1/pharmacies`

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/` | any authenticated | List / search / near-me |
| GET | `/{id}` | any authenticated | Detail |
| POST | `/` | admin | Create |
| PATCH | `/{id}` | admin | Update; `is_verified: true` stamps `verified_at/by`; `mark_confirmed: true` stamps `last_confirmed_at` |
| DELETE | `/{id}` | admin | Deactivate (hidden from lists, kept) |
| POST | `/import` | admin | Bulk CSV import |

## List

`GET /pharmacies/` — paginated (`limit` 1–500, default 100; `offset`), ordered by name.

Filters: `search` (name EN/BN or address), `discipline` (`homeopathy|ayurveda|unani|herbal`),
`pharmacy_type` (`retail|wholesale|manufacturer|depot`), `district_id`, `delivers`, `is_active`
(default true).

**Near me:** pass `lat` and `lon` (both, or 422) and optionally `radius_km` (default 10, max 200).
Only listings that have a map pin inside the radius are returned, **nearest first**, each with
`distance_km`. Listings without a pin never appear in near-me results (they still appear in normal
lists). Distance is great-circle; a lat/lon bounding box on an index narrows rows first. Fine for
thousands of rows; revisit (PostGIS) if the directory grows far beyond that.

## Location rules

`latitude` and `longitude` are optional but must be set **together** (DB check + API validation),
and range-checked (−90..90, −180..180).

## CSV import

`POST /pharmacies/import` (multipart, field `file`). UTF-8 (a BOM from Excel is fine), header row
required, ≤ 1000 rows and ≤ 2 MB. Columns:

```
name_en,name_bn,pharmacy_type,disciplines,address,district,latitude,longitude,phone,whatsapp,email,website_url,opening_hours,delivers,notes_en,notes_bn,source_url
```

- `disciplines`: one or more, separated by `;` or `|` (e.g. `homeopathy;unani`)
- `district`: an English district name from the `districts` table (case-insensitive); unknown → row error
- `delivers`: `yes/true/1` → true
- **All-or-nothing:** if any row is invalid nothing is saved; the response lists every bad row with
  its CSV line number (header = line 1).
- Rows that already exist (same `name_en` in the same district, case-insensitive) are **skipped**,
  including duplicates inside the same file, so re-uploading a corrected file is safe.

Response: `{ "created": n, "skipped": n, "errors": [{ "row": 3, "message": "..." }] }`

## Seed data

`backend/seed_data/pharmacies.json`, loaded by `scripts/seed.py` (`seed_pharmacies`, idempotent: same
name in the same district is skipped; an unknown district name fails loudly). **50 rows, all from
one source:** the Hamdard Laboratories (Waqf) Bangladesh website (head office + 49 branch centres
from `hamdard.com.bd/healthcare-center`, read 2026-10-11, with the Google Maps pin Hamdard publishes
for each). All are **Unani**, **unverified** and **unconfirmed** (so practitioners see "not yet
confirmed — please call first"); an admin should phone-check a listing and then use *Confirmed
today* / *Verify*. There are **no homeopathy or ayurveda rows** — no source of comparable quality
was found. `tests/unit/test_pharmacy_seed_data.py` guards the file (schema, https source, phone
format, district exists, pin within 70 km of its district, no shared pins).

## Not built (by decision)

Practitioner suggestions/reports, per-clinic favorites, reviews, stock/price lists, public
(logged-out) access.

## Frontend

- **Admin page** `/admin/pharmacies` (sidebar: Pharmacies; operators view, admins edit): server-side
  search/filters/paging, add/edit dialog with a Leaflet pin-drop map (OpenStreetMap tiles; click to
  drop, drag to adjust, district choice recentres the map), "Confirmed today" / Verify / Deactivate
  actions, a *Stale* badge after 180 days without confirmation, and CSV import with a downloadable
  template. Code: `components/pharmacies/`, `lib/hooks/usePharmacies.ts`.
- **Practitioner page** `/pharmacies` (sidebar: Pharmacies; every tenant role, receptionists read the same):
  list (paged, 20/page) or map (up to 500 pins), search and discipline/type/district/delivers
  filters, **Near me** with a 5–100 km radius, nearest first with distances. Each card has
  Call / WhatsApp / Directions (Google Maps) buttons sized for thumbs, a Verified badge, and a
  "Confirmed <date>" note that turns into a warning when older than 180 days or missing. A details
  dialog adds notes, email, website. Code: `app/(dashboard)/pharmacies`, `components/pharmacies/`,
  `lib/utils/contact.ts` (link builders, unit-tested), `lib/hooks/useNearMe.ts`.
- **Near me privacy:** the browser asks permission; the position is never stored, is rounded to 3
  decimals (~110 m) before it is sent, and is sent only as search parameters. Works on HTTPS or
  localhost only.
- WhatsApp buttons use the listing's WhatsApp number, falling back to its phone number (Bangladeshi
  `01…` numbers are converted to `8801…`).
- The geographic API now also returns `latitude`/`longitude` for districts and upazilas (used to
  start the map in the right place).
- OpenStreetMap's public tile server is fine for an admin tool; use a tile provider with a usage
  allowance before heavy public/practitioner use.
