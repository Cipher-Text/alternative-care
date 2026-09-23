# ADR 008: Practitioner and clinic directories are projections of Tenant data, not new entities

- Status: Accepted
- Date: 2026-09-23

## Decision

The public Practitioner Directory and Clinic Directory (`docs/planning/revision-2026-09.md` D14, Stage 5) read from the existing `Tenant` and `User(role=doctor)` tables — filtered to `Tenant.is_approved = true` and a new opt-in `Tenant.is_publicly_listed: bool` (default `false`) — rather than a new `PractitionerProfile`/`ClinicProfile`/`directory_listings` table a tenant fills out separately.

A clinic's name, address, specializations, and doctor roster already live on `Tenant`/`User`/`DoctorDegree`/`DoctorTraining`. The directory is a `/api/v1/public/*` read path (ADR — see D4) over that same data, not a second copy of it.

## Why not a separate profile table

The tempting alternative is a table a tenant explicitly curates for public consumption, independent of their operational record — giving them field-level control over what's public vs. internal (e.g., list the clinic's public phone number but not its billing address). That's a real advantage this ADR gives up.

It was rejected because:

1. **Drift is the failure mode this schema already exists to prevent.** ADR 002 and D1 (`revision-2026-09.md`) exist because global-vs-tenant data got duplicated once already (global medicine/symptom writes) and it broke at the database level. A parallel profile table reintroduces the same shape of bug one layer up: a clinic updates its address in Settings, the public listing silently doesn't move, and now the directory is actively wrong instead of just incomplete.
2. **No second consumer today.** A dedicated profile table earns its cost when something needs to diverge from the operational record. Nothing does yet — Stage 5's gate is "≥20 practitioners with complete public profiles," which the existing `Tenant`/`User` fields already satisfy.
3. **Smaller migration, smaller review surface, faster to gate-check.** One boolean column vs. a new table, its own CRUD, and a sync job (or a lack of one) to keep it honest.

## Consequences

- **Projection, not copy.** The directory service reads `Tenant`/`User` directly (through the same `GlobalCatalogModel`/public-router pattern as Medicine/Symptom, per D4), filtered by `is_approved` and `is_publicly_listed`. No directory-specific write path exists — a tenant "updates" its listing by updating its profile, the same way it always has.
- **Field-level privacy is coarse.** `is_publicly_listed` is all-or-nothing at the tenant level today. If tenants ask to show some fields publicly and hide others (e.g., public phone, private billing address), that requires either new nullable "public override" columns on `Tenant` or revisiting this ADR — evaluate when it's an actual request, not preemptively.
- **This is the one call in the Stage 5/6 batch with real reversal cost.** The "public projection" pattern gets baked into how the directory routes and services are written; unwinding it into a separate-table model later means a real migration, not a config flag. Flagged explicitly in `revision-2026-09.md` D14 for that reason.
- **College/Institution Directory is unaffected** — colleges aren't tenants, so `colleges` is a genuine new `GlobalCatalogModel` table (D15), admin-curated the same way Medicine/Symptom are. This ADR only concerns data that already has a tenant-owned source of truth.
