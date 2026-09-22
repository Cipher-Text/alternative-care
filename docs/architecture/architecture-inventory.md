# AltCare Architecture Inventory and Phase A Plan

**Inspected:** 2026-09-23. This inventory describes the checked-in implementation, not planned capabilities.

## 1. Current architecture inventory

AltCare is one Next.js application (`frontend/src/app`), one FastAPI application (`backend/app/main.py`), and a shared PostgreSQL schema managed by Alembic. SQLAlchemy async sessions are provided centrally by `app.core.database`. Redis is configured for rate limiting and Celery; `app.core.celery` configures a Celery app and currently imports integration tasks. MinIO endpoint/bucket credentials are settings only: no storage client or upload integration was found. `pgvector` is a dependency and the existing library model declares a 1536-dimensional vector column; no search or retrieval implementation was found.

Active backend routers are auth, admin, tenant, AI, appointments, dashboard, doctor, patient, prescription, payment, integration, medicine, symptom, and geographic. Library has models only; notification is a placeholder. The `/api/v1/ai/query` endpoint is a Pro-gated 501 stub. The API description and Python package description still call the product a practice management system.

Shared SQLAlchemy models are imported for Alembic autogeneration from `app.shared.models`. The common `TenantScopedModel` adds a **non-null** `tenant_id` FK. It claims automatic filtering in its docstring, but that is not true: filtering is explicitly performed by `BaseTenantService` and individual route/service queries. `tenant_id_ctx` is set during authentication but no reads were found. There is no PostgreSQL RLS policy or session-level tenant enforcement.

Medicine and symptom tables encode a hybrid intent with `is_global` plus `tenant_id`, and routes return global-flagged rows plus rows matching the current tenant. However, the checked-in ORM base and initial Alembic migrations make `tenant_id` non-null for these models, while global create routes set `tenant_id=None`. The “global” classification can be shared for reads, but tenantless global creation is inconsistent with the current schema and may fail at the database. Resolve this with an explicit additive migration/model review in Phase B; do not replace these tables with duplicate master catalogs. Aliases and medicine-symptom mappings also inherit tenant-scoped model behavior and need relationship scope decisions when global associations are expanded.

The current library model comprises books, chapters, sections, embeddings, reading progress, bookmarks, and highlights. All inherit `TenantScopedModel`, including content-oriented books/chapters/sections/embeddings. Books have bilingual title/description, one author string, one `system` string, publication year, publisher, ISBN, language, EPUB and cover URLs, parsing counts/status, global flag, and active flag. There are no author entities, access/copyright capabilities, checksum fields, ingestion jobs, library routes/services, or MinIO integration. Reader annotations/progress are tenant-scoped. PostgreSQL vector support is declared but migration/runtime retrieval support was not established in this inspection.

Doctor degrees/trainings are tenant-scoped credential records attached by `user_id`; no separate public practitioner entity exists. Platform admin routes are in `modules/admin` with `RequireAdmin`; the frontend admin pages live under the same dashboard route group. Frontend route groups `(auth)` and `(dashboard)` do not alter URLs; dashboard layout gates application routes. No distinct public/practice/admin layout boundary was found beyond the auth and dashboard layouts.

There are two initial schema migrations plus follow-up migrations through June 2026. Existing tests include unit and integration coverage, including multi-tenant and MVP isolation suites. Documentation includes authoritative architecture, status, roadmap, API, and archived status material; some checked-in docs overstate guarantees (notably “impossible” cross-tenant leakage and “row-level security”) and several counts/statuses require ongoing reconciliation against live code.

## 2. Problems and risks found

1. Tenant isolation is application-level explicit row filtering, not PostgreSQL RLS and not automatic. Hand-written queries can omit scope. Base service assumes every model has a non-null tenant, so it is unsuitable for platform-global records.
2. Platform users have `tenant_id=None`. Patient, appointment, prescription, payment, dashboard, and tenant route dependencies reject missing tenant. The initial inspection found missing tenant guards in doctor and tenant-integration paths; Phase A adds the shared guard to those service dependencies while leaving global integration provider catalog reads available.
3. Medicine/symptom routes permit global-flagged reads and are authenticated rather than public. Global create routes set null tenant IDs despite non-null ORM/migration constraints; this is a code/schema mismatch. Tenant-created records rely on a current tenant. Relationship-table tenant semantics may not match future platform-global parent records.
4. Existing library content is tenant-scoped, which conflicts with the intended platform-global canonical catalog. Converting it requires a staged data migration and separate user annotation ownership; do not alter it as part of Phase A.
5. MinIO is configured but not integrated; Celery exists but its configured task imports currently cover integration only. Book ingestion and OCR are not implemented.
6. Admin user/tenant management is integrated, but the entire frontend admin section shares dashboard layout/navigation. A separate platform-admin UX boundary is still future work.
7. Existing docs sometimes describe application row filtering as row-level/database security and claim stronger guarantees than the implementation. Treat docs as claims to verify, not evidence.

## 3. Proposed target module map

Keep current paths and FastAPI app. Use conceptual ownership, not package churn:

```text
Platform:      auth, admin, tenant, geographic
Practice:      doctor, patient, appointments, prescription, payment,
               integration, dashboard
Knowledge:     medicine, symptom, discipline, condition, herb,
               reference, evidence
Content:       library, college, content/article; optional directory
Intelligence:  ai, search
Infrastructure: core, shared models/schemas
```

Future cross-domain relations should use shared catalog records and explicit association tables, with module-owned services/routes and admin authorization on mutations. Platform admin remains in the one app. Public knowledge retrieval must not share patient-record retrieval.

## 4. Database changes required (planned, not yet applied)

Phase A: no schema change is necessary. Phase B onward: introduce global-capable audited model base separate from `TenantScopedModel`; add discipline, condition, herb, reference, and evidence tables plus association tables; connect disciplines to existing medicine/doctor/book and later college/article. Preserve existing medicine/symptom global-vs-tenant records and migrate carefully. Library requires a staged shift from tenant-scoped canonical book content toward platform-global catalog/content, plus authors/book-author and book-discipline relations, explicit access capabilities, file metadata/checksums, and idempotent import identity. Keep reading progress/bookmarks/highlights user/tenant scoped. College and CMS tables are subsequent phases. Prefer additive migrations and backfills; no destructive migration is proposed now.

## 5. Migration sequence

1. **Phase A (this change):** verified inventory, corrected architecture/product docs, ADRs, explicit global/tenant data rules, shared tenant-user dependency, regression coverage for platform-user rejection at clinical and tenant-integration boundaries. No schema changes and no route renames.
2. **Phase B foundation (later):** global audited model base and discipline/condition/herb/reference/evidence schema in additive migrations; reuse global medicine/symptom semantics; connect relationships after schema review.
3. **Phase C:** library ownership/access-policy migration, metadata/authors, object storage adapter and Celery ingestion tasks with checksums/idempotency; retain existing reader annotation behavior.
4. **Phases D–G:** public frontend, college/content, PostgreSQL search, then knowledge-only RAG with citations. Each phase gets its own migration and API compatibility review.

## 6. Files expected to change in Phase A

- `README.md`, `backend/pyproject.toml`, `backend/app/main.py` for accurate product positioning.
- `docs/architecture/README.md`, `docs/architecture/multi-tenancy.md`, `docs/architecture/roles-access.md`, `docs/status/current.md`, `docs/ROADMAP.md` and new `docs/architecture/adr/` records.
- `backend/app/core/dependencies.py` plus selected route dependencies and regression tests to require tenant identity at tenant-only endpoints.
- No Alembic migration, no table rename, and no frontend URL change.

## 7. Compatibility risks

Changing product descriptions and adding a tenant-required dependency should not change successful tenant-user requests or endpoint paths. Platform users that previously reached a tenant-only endpoint with a null tenant will receive 403; this is a security correction. Global medicine/symptom reads remain available under their existing authenticated API contracts. Any attempt to make catalog records truly platform-global is deferred because current library entities inherit a non-null tenant FK and changing ownership has migration risk.

## 8. Test plan

Use existing tenant-isolation and role tests as regression coverage; add focused tests proving platform users cannot invoke doctor/tenant clinical paths while tenant users remain accepted. Validate global medicine/symptom behavior stays available under existing query rules. For later phases, add CRUD/authorization, access-policy, import idempotency, workflow, public-route, and search tests alongside each implementation. This turn runs backend tests and configured static checks only where the environment supports them; frontend behavior is not changing.

## Verified target product statement

**AltCare — Alternative Medicine Knowledge & Practice Platform**. The current delivered product remains clinic-focused; knowledge, library, directory, CMS, search, and RAG expansion is a staged roadmap, not a claim of implemented functionality.
