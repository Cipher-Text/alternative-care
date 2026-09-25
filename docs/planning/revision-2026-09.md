# AltCare — Plan, Architecture & Technology Revision

**Date:** 2026-09-23
**Author:** Revision pass against checked-in code, not against existing documentation
**Supersedes:** the phase sequencing and success metrics in `docs/ROADMAP.md`, the "MVP v1.0 — Production Ready" status claim in `docs/status/current.md`, `README.md`, and `CLAUDE.md`
**Assumptions this revision was written under:** nothing is deployed yet; one developer (plus AI assistance) is building this; the clinic product and the knowledge platform are both wanted, sequenced rather than parallel

---

## 0. Why a revision

The existing plan is not wrong about direction. It is wrong about *starting position*. It sequences 400+ hours of Phase C–G work on top of a base described as production-ready, when the base has no deployment path, no account recovery, a red test suite, and a schema that physically cannot store the global catalog every later phase depends on.

This document replaces phase-sequencing-by-feature with **stage-sequencing-by-gate**: each stage ends in a condition you can verify, not a checklist you can feel done with. Everything here is grounded in code read on 2026-09-23; claims carry file references so they can be re-verified rather than believed.

---

## 1. Verified reality

| # | Claim in current docs | What the code shows | Evidence |
|---|---|---|---|
| 1 | "MVP v1.0 — Production Ready 🚀" | No Dockerfile anywhere, no IaC, no deploy script, compose covers Redis + MinIO only (the `api` service is commented out). Nothing can be deployed reproducibly. | `find . -iname 'Dockerfile*'` → empty; `docker-compose.yml` |
| 2 | "Multi-tenant isolation 16/16 tests passing" | Clean local run: **322 passed, 76 failed, 1 error** (5m15s), including the tenant-isolation suites. | `pytest -q` |
| 3 | "Security: A (95/100)" | Score has no source, date, or method attached in any checked-in doc. Meanwhile Sentry and structlog are declared dependencies that are never initialised. | `grep -rn "sentry_sdk\|structlog.configure" app/` → no wiring |
| 4 | Medicines/symptoms support admin-curated **global** rows | **Fixed 2026-09-24** (D1, out of Stage 2 order — see Stage 2 note below). As of 2026-09-23: global creation wrote `tenant_id=None` into a `NOT NULL` column, so global catalog writes failed at the database. | Was `app/modules/medicine/routes.py:102`, `app/modules/symptom/routes.py:93` vs `alembic/versions/000_initial_schema.py:110` and `TenantScopedModel` (`nullable=False`); now migration `ba209a25bf7d` |
| 5 | Password reset / email verification are "P1 to do" | The endpoints exist as **commented-out code**. There is no self-serve account recovery at all. | `app/modules/auth/routes.py:285–322` |
| 6 | Plan-based access + quotas (`usage_tracking`, 200 queries/month) | `usage_tracking` has a model and a table and **zero writers**. `plan_expires_at` is stored and never checked. `RequireProPlan` gates exactly one 501 stub. | `grep -rn UsageTracking app/` → model + export only; `app/modules/ai/routes.py` |
| 7 | MinIO ready for file storage | No storage client, no SDK dependency, no upload path. All file fields are URL strings. | `grep -rn "boto3\|minio" app/` → no matches |
| 8 | React Query for server state | `react-query@3.39.3` — the unmaintained pre-TanStack line — across 13 files. | `frontend/package.json`, `grep -rl "from 'react-query'" src` |
| 9 | "`cd frontend && npx playwright test --ui`" | `@playwright/test` is installed; there are **zero** spec files. | `find frontend -name '*.spec.ts'` → empty |
| 10 | Uniform module layering | `medicine` and `symptom` are route-only modules: 700 and 418 lines with 30 raw `select()` calls and hand-written tenant predicates. Every other domain has `service.py`. | `app/modules/medicine/routes.py`, `app/modules/symptom/routes.py` |

### 1.1 The test failures, classified

Not all 76 are product bugs, and saying so precisely matters for planning:

- **~60 failures are harness defects, not code defects.** The rate limiter is Redis-backed with production limits and no per-test reset, so tests poison each other (`429` where `200`/`401`/`422` was expected — 30+ assertions). The local `INTEGRATION_ENCRYPTION_KEY` is not a valid Fernet key, which fails 10 more (`binascii.Error: Incorrect padding`). Re-running the isolation and integration suites with limits raised and a valid key drops 35 failures to 6.
- **The remainder are real.** Two confirmed: `IntegrationService.set_primary` raises `sqlalchemy.exc.InvalidRequestError: Don't know how to join to <Mapper ... IntegrationProvider>` — an ambiguous join that will fail in production whenever a user marks an integration primary; and the registration response no longer carries `tenant_id`, so the API contract has drifted from its own tests (`KeyError: 'tenant_id'`).
- **Route-count drift:** the app exposes 128 `/api/v1` methods; `tests/unit/test_route_registration.py:44` asserts 127.
- **Tests build the schema from `Base.metadata.create_all`, not from migrations** (`tests/conftest.py`), so model-vs-migration drift is structurally invisible to the suite. The CI migration-safety job checks that migrations *run*, not that they produce the schema the code expects.

### 1.2 Other findings worth fixing on sight

- **Dependency split-brain.** `backend/pyproject.toml` is what CI installs. `backend/requirements.txt` is a second, divergent manifest pinning `langchain==0.1.16`, `openai==1.16.2`, `pgvector==0.2.5`, `stripe`, `sendgrid`, `twilio` — an AI/vector stack that nothing installs and nothing imports.
- **Root `.env` is tracked by git.** Its values currently match `.env.example` (only `DATABASE_URL` differs), so nothing is leaked today — but there is no root `.gitignore` rule, so the next real key written into it lands in history. `backend/.env` is correctly ignored.
- **`.env` advertises `RATE_LIMIT_ENABLED`; `app/core/config.py` has no such setting.** The toggle the test suite needs is already documented and simply not implemented.
- **Tokens live in JavaScript-readable cookies** (`frontend/src/lib/api/client.ts:51–52`), so any XSS is a full session theft. There is no `frontend/src/middleware.ts`, so route protection is client-side only.
- **Celery is half-wired**: one task module (integration SMS/email), no beat schedule, no worker in any deployment unit.
- **Legacy dual API surface**: five `/auth/admin/*` endpoints still shadow `/api/v1/admin/*` (`app/modules/auth/routes.py:56–119`).

---

## 2. Direction: two tracks, one keystone

The answer to "clinic SaaS or knowledge platform" is both, but the current roadmap sequences them as *phases* (C → D → E → F → G) and that sequencing is what makes it unachievable solo. Reframed:

- **Track P (Practice)** is the revenue and the credibility. It is nearly built; what it lacks is not features but *shippability* — recovery, deployment, billing enforcement, backups.
- **Track K (Knowledge)** is the moat and the reason the product is worth more than a scheduling tool. It is almost entirely unbuilt.

They are not independent. **The keystone is the global-catalog schema fix (§3, D1).** The same migration that lets an admin curate a platform-wide medicine library is what makes the clinic product's prescription autocomplete useful — today the autocomplete component exists and has nothing to autocomplete against, because global rows cannot be written. One migration, two tracks. It is therefore scheduled early, in Stage 2, not deferred into the knowledge phases.

**Sequencing rule:** Track P runs to a shippable, paid, deployed state first (Stages 0–1). Track K's foundation lands next (Stage 2). Content and retrieval follow (Stages 3–4). No Track K work starts before Stage 1's gate, because an undeployed platform with a book reader is worth less than a deployed clinic tool.

### 2.1 What this revision cuts

Cutting is the substance of a solo plan, so these are removals, not deferrals-in-name:

| Cut | From | Why |
|---|---|---|
| **Mobile apps (React Native, iOS + Android)** | Phase F, 120–160 h | Two more deployment targets and two app-store relationships for one developer. Responsive web already covers the use case; make it installable as a PWA instead. |
| **GraphQL API, Keycloak SSO, white-label, multi-clinic chains, SOC 2** | Phase G | Every one is an enterprise-buyer feature, and there are no enterprise buyers in the pipeline. Revisit when a signed contract asks. |
| **Public doctor directory** | Phase E, 25–35 h | It is a marketplace, and a marketplace with no supply is an empty page. Gate it on ≥20 listed practitioners, which Stage 3's public pages are what actually produce. |
| **LangChain** | `requirements.txt` | Two major lines stale, and the retrieval this product needs is ~200 lines of pgvector query plus prompt assembly. It is the single largest dependency-risk surface in the repo for the smallest benefit. |
| **"1,000+ medicines / 1,000+ mappings" targets** | Roadmap tasks 11–12 | Volume targets invite scraping. 300 practitioner-reviewed homeopathy entries beat 1,000 unreviewed ones, and the review capacity is the real constraint. |
| **Notification template CMS, bulk operations** | Roadmap tasks 14, 18 | Real but small pain, competing against deployment and billing. Deferred behind Stage 3 with no date. |

### 2.2 What this revision adds that the old plan omitted

Deployment and operations (§6), billing enforcement, backup/restore with a rehearsed drill, a storage adapter, RLS as a second isolation layer, an honest test harness, and a content-rights gate before any book is ingested.

### 2.3 Scope beyond Track P/Track K — deliberately not detailed here

The product owner's scope for AltCare is wider than Track P/K: practitioner/clinic/college directories and editorial content, alongside the book library. A feature-by-feature audit (95 named items) found 38 (40%) with zero footprint anywhere in the repo — not a sync problem, scope that was never captured. Direction and sequencing for that scope are decided in **`docs/planning/future-scope-2026-09.md`** (Track D — Directory, Track C — Content/CMS), kept in a separate document on purpose: both tracks sit behind Stage 4 or later, and D1–D10's stage-by-stage detail above is for work that's active *now*. Mixing "ships in weeks" with "gated, no date" at equal weight in one document defeats §0's whole point. Schema-level detail for Track D/C is intentionally deferred to when each stage actually starts, not speculated now — see that document's own note on why.

---

## 3. Architecture decisions

Each decision states the change, the reason, and the alternative rejected.

### D1 — Two model bases. `GlobalCatalogModel` alongside `TenantScopedModel` — **the keystone**

`TenantScopedModel` forces `tenant_id NOT NULL`, which is correct for clinical rows and wrong for catalog rows. Introduce an audited base with no tenant column, and migrate `medicines`, `symptoms`, `medicine_aliases`, `symptom_aliases`, `medicine_symptom_mappings` to nullable `tenant_id` guarded by a constraint that makes the invalid state unrepresentable:

```sql
CHECK ( (is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL) )
```

Additive migration, backfill existing rows as tenant-owned, no destructive step. *Rejected:* a parallel `global_medicines` master table — it doubles every read path, every alias join, and every mapping, to avoid one migration.

### D2 — PostgreSQL RLS as a second layer, not a replacement

Keep application-level filtering exactly as it is. Add RLS policies on the eight clinical tables (`patients`, `appointments`, `visits`, `prescriptions`, `prescription_items`, `payments`, `invoices`, `patient_diagnoses`) keyed on `current_setting('app.tenant_id')`, set per session in `get_db`. The point is not to replace `BaseTenantService`; it is to convert the failure mode of a hand-written query that forgets its predicate from *silent cross-tenant leak* to *hard error*. Catalog tables stay outside RLS; platform users (`tenant_id IS NULL`) connect under a role that is not subject to the clinical policies. *Rejected:* schema-per-tenant — 34 tables × N clinics of migration pain for a product that must query across tenants for platform analytics.

### D3 — No SQL in routes

`medicine` and `symptom` get `service.py` like every other module, with one `_visible_query()` that encodes the global-vs-tenant read rule in a single place. This is not tidiness: 30 hand-written `select()` calls in route handlers is precisely the shape D2 is defending against, in precisely the module Track K expands.

### D4 — Knowledge reads and clinical reads never share a path

Public knowledge endpoints mount under `/api/v1/public/*` with no auth dependency, their own rate-limit bucket, and services that have no import path to any patient model. The boundary is structural, so a future refactor cannot accidentally expose a patient row through a knowledge endpoint.

### D5 — Search: PostgreSQL first, vectors only when there is a corpus

`pg_trgm` GIN indexes already exist on `medicines`. Add generated `tsvector` columns plus GIN indexes on medicines, symptoms, and book sections, behind one `/search` endpoint with per-type ranking. Vector search enters in Stage 4, when there is something embedded to search. *Rejected:* Elasticsearch/Meilisearch — a second datastore to run, back up, and keep in sync, for a corpus that fits comfortably in Postgres.

### D6 — One storage adapter, S3-compatible

`app/core/storage.py` exposing `put_object` / `presigned_url` / `delete`, S3-compatible via `boto3`; MinIO in dev, S3/R2/Spaces in prod. This single missing piece is what blocks EPUB upload, prescription PDF persistence, doctor photos, and clinic logos — four "small" features that all silently depend on it.

### D7 — Celery stays, but becomes real

Add a beat schedule (appointment reminders, plan-expiry sweep, ingestion jobs), queues per class (`default` / `sms` / `email` / `pdf` / `ingest`), and actual `worker` + `beat` processes in the deployment unit. *Rejected:* swapping to `arq`/APScheduler — Celery is already configured and working; replacing it buys nothing.

### D8 — Auth hardening at the browser boundary

Refresh token moves to an httpOnly, `SameSite=Lax`, `Secure` cookie set by the backend; the access token lives in memory (non-persisted Zustand). Add `frontend/src/middleware.ts` for server-side route gating. This closes the "XSS equals full session theft" exposure that the current JS-readable cookies create.

### D9 — Deployment unit: one VPS, one compose stack

Even though nothing is deployed yet, the target is chosen now because it constrains everything else: `caddy` (TLS + reverse proxy) · `api` (uvicorn) · `worker` · `beat` · `web` (Next standalone) · `postgres:16 + pgvector` · `redis` · `minio`, as a single Docker Compose project on one VPS, deployed by `git pull && docker compose up -d --build && alembic upgrade head`. Sized for one developer and a Bangladesh-market price point; revisit at ~200 clinics or the first enterprise contract. *Rejected:* managed PaaS (recurring cost without the ops relief that matters at this size), and AWS/GCP proper (Terraform, IAM, and a VPC to maintain alone).

### D10 — Three environments, secrets never in git

`dev` (local) · `staging` (second compose project on the same box, separate DB) · `prod`. Remove root `.env` from tracking, add a root `.gitignore`, keep `.env.example` as the only committed template. Nightly `pg_dump` to object storage, and a restore drill that is *performed*, not documented.

D11–D16 (discipline, condition/therapy, evidence subsystem, directory sourcing, college directory, content/CMS) moved to `docs/planning/future-scope-2026-09.md` — see §2.3.

---

## 4. Technology decisions

| # | Decision | Change from today | Rationale |
|---|---|---|---|
| T1 | **One Python manifest** | Delete `backend/requirements.txt`; `pyproject.toml` gains `[ai]` and `[dev]` extras; adopt `uv` with a committed lockfile | Two divergent manifests is an outage waiting for the day someone installs the wrong one |
| T2 | **TanStack Query v5** | Migrate 13 files off `react-query@3` | v3 is unmaintained and predates React 19; the migration is mechanical now and compounds with every hook added |
| T3 | **No LangChain** | Provider SDK + pgvector + a small retrieval module | See §2.1 |
| T4 | **Model choice deferred to a Bangla evaluation** | Do not inherit the `gpt-4o-mini` / `text-embedding-3-small` pins from `requirements.txt` by default | Bengali retrieval and generation quality is the deciding variable for this product and it differs sharply by model. Build a 50-question bilingual eval set *before* committing to a provider, and re-run it when switching. Budget and citation fidelity, not brand, decide |
| T5 | **`RATE_LIMIT_ENABLED` setting** | Add to `config.py` (default `true`, `false` in tests) + autouse Redis-flush fixture | Turns ~60 red tests green and makes the suite runnable locally — the key is already in `.env`, just unimplemented |
| T6 | **Tests build the schema from migrations** | `alembic upgrade head` in `conftest.py` instead of `create_all` | Makes model-vs-migration drift a test failure instead of a production surprise |
| T7 | **Frontend CI + Playwright smoke suite** | New workflow: `tsc --noEmit`, `eslint`, and one end-to-end path (login → patient → prescription → issue → PDF) | The frontend currently has no CI at all, and the documented test command runs zero tests |
| T8 | **Observability wired, not declared** | `sentry_sdk.init`, `structlog.configure` (JSON in prod), request-ID middleware | Both dependencies are already paid for in install time and deliver nothing until initialised |
| T9 | **i18n completeness enforced in CI** | Check every `en` key has a `bn` counterpart | Bengali is a market requirement here, not a nice-to-have, and translation coverage rots silently |
| T10 | **Stack otherwise unchanged** | Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL 16 + pgvector, Redis, Next.js 16 / React 19, Tailwind 4, shadcn/ui | No technology in the core stack is the problem. The problems are unfinished wiring and drift |

---

## 5. The revised roadmap

Five stages, each ending in a gate. Dates assume one developer; a missed date moves the stage, never the gate.

### Stage 0 — Truth & Green · by 2026-10-07

**Status as of 2026-09-24: mostly done.** `pytest -q` runs **432 passed, 2 xfailed, 0 failed** locally (409 passed on 2026-09-23 when this stage was first drafted; the 23 added since are coverage for password reset, email verification, and Google Sign-In, landed the same week — see Stage 1 note below. Before that: 322 passed / 76 failed on 2026-09-23 morning, then 316/82/1 error on the next verification pass before this work started — see §1 for how that number was produced). The 2 `xfail`s are intentional — they pin down known, still-open gaps as regression tests rather than deleting the coverage or quietly loosening the assertion:
  - `test_plan_downgrade_revokes_pro_access` (`test_auth_security.py`) — plan enforcement is JWT-claim-only today; `RequireProPlan` never checks the DB, so a downgraded tenant's still-`pro`-flagged access token keeps working until it expires. Real fix is Stage 1's "Billing enforcement."
  - `test_receptionist_cannot_access_doctor_endpoints` (`test_auth_security.py`) — `app/modules/doctor/routes.py` guards its endpoints with `get_current_user`/`require_tenant_user` only, no `require_role('doctor')`, so any tenant role (including receptionist) can call them. Matches the documented "receptionist: no enforcement" gap; real fix is Phase B role enforcement.

Done:
- `RATE_LIMIT_ENABLED` setting added (default `true`); an autouse `conftest.py` fixture sets it `false` per test by default and flushes Redis before each test, so unrelated suites stop getting poisoned by shared rate-limit counters. Tests that specifically exercise rate limiting opt back in per-test. A real Fernet key is now in `backend/.env` (was the placeholder string `dev-fernet-key-change-in-production`, which broke all 12 integration-credential tests). (T5)
- Both confirmed bugs fixed: `IntegrationService`'s three `.join(IntegrationProvider)` calls (`list_integrations`, `set_primary`, `get_primary_integration`) now pass an explicit `on` clause — `TenantIntegration.provider_id` was never declared as a real FK, so SQLAlchemy couldn't infer the join. The registration response already carried `tenant_id` correctly on inspection; the `KeyError: 'tenant_id'` in the isolation test was actually the rate-limit poisoning above, now fixed.
- Route-count assertion reconciled at **129** (not 128 — a `POST /auth/login-2fa` endpoint was added along the way, see below).
- Root `.env` untracked, root `.gitignore` added. `backend/requirements.txt` was already gone.
- Sentry + structlog + request-ID middleware wired (`app/core/observability.py`): `structlog.configure()` now actually runs (JSON renderer in production, console renderer otherwise, request ID merged into every log line); `sentry_sdk.init()` runs when `SENTRY_DSN` is set; `X-Request-ID` is generated/echoed on every response. (T8)
- This section, and the top-of-file status claims, corrected to match the above.

Not done (moved to a follow-up, not silently dropped):
- **`conftest.py` still uses `Base.metadata.create_all`, not `alembic upgrade head` (T6 not done).** Checked the drift risk this was meant to catch directly: ran `alembic upgrade head` against a scratch database and diffed its table set against `Base.metadata.sorted_tables` — identical, all 34 tables (33 domain tables + `alembic_version`) match by name. No column-level diff was done. Switching the fixture itself is a bigger change than it looks: the current fixture drops/recreates the whole schema per test function; migrations are comparatively slow, so a naive swap would multiply the suite's runtime by however many tests exist unless the fixture is restructured to migrate once per session and reset data per test (truncate, not drop/create) — that restructuring is real design work, deferred rather than rushed.
- `uv` adoption / lockfile (T1) — not started; `pyproject.toml` + `pip install -e ".[dev]"` still the installation path, which is what CI already uses successfully.
- Deep beyond the 2 confirmed bugs, **12 more real, previously-undetected bugs surfaced once the harness noise (rate-limit poisoning, a shared-`AsyncClient`-instance fixture bug) was cleared away** — see the running list below. Fixing the harness didn't just turn red tests green, it let real signal through for the first time.

**Real bugs found and fixed while chasing Stage 0 green** (beyond the 2 already documented in §1):
1. **Refresh-token rotation didn't rotate.** `create_refresh_token()` hashed with bcrypt, which truncates input at 72 bytes; two refresh tokens for the same user (same header, same `sub`, same `token_version`) are byte-identical in their first 72 characters, so bcrypt hashed them identically regardless of the different `exp`/would-be-`jti` further in — meaning a "rotated" refresh token still validated against the old hash. Fixed by hashing refresh tokens with SHA-256 (`hash_refresh_token`/`verify_refresh_token` in `app/core/security.py`) instead of bcrypt, and added a `jti` claim for good measure. This is a real session-security bug, not a test artifact — old refresh tokens were never actually being invalidated on rotation.
2. **`authenticated_client` and `authenticated_client_2` were the same object.** Both fixtures mutated the header on the one shared `client` fixture instance, so any test requesting both got the *same* client with whichever token was set last — silently defeating cross-tenant isolation tests (the exact category of test this matters most for). Fixed with a separate `client_2` fixture. Affected 5 tests across `test_integration_routes.py`, `test_auth_security.py`, `test_multi_tenant_isolation.py`.
3. **`GET /integrations/logs` and `GET /payments/invoices` were unreachable.** Both were registered *after* a same-shape single-segment dynamic route (`GET /{integration_id}`, `GET /{payment_id}`) in their respective route files; Starlette matches in registration order, so every request to `/logs` or `/invoices` was swallowed by the dynamic route first. Fixed by moving both above their colliding dynamic routes (with a comment explaining why, so it doesn't regress).
4. **`bKash query` endpoint silently discarded its response.** `response_model=BkashPaymentResponse` declared snake_case fields; the service returns bKash's raw camelCase payload verbatim (`paymentID`, `trxID`, …). Pydantic dropped every unrecognized key and returned an all-`null` object. Changed to `response_model=dict` (matching the sibling `/bkash/create` endpoint, which already did this correctly).
5. **2FA login had no way to actually complete.** The login service hard-failed with `400` when a 2FA-enabled account omitted `totp_code`, but `LoginResponse` had a `requires_2fa` field and the frontend already called a `POST /auth/login-2fa` endpoint that **didn't exist on the backend**. 2FA login was broken end-to-end. Added the endpoint, and changed the service to return `requires_2fa: true` (tokens/user omitted) instead of raising, matching what the frontend already assumed.
6. **`POST /auth/logout` couldn't revoke a single session.** `refresh_token` was an unmarked function parameter, which FastAPI binds as a *query* parameter for a plain `str` — but every caller (and the API's own convention) sends it as a JSON body. Every "logout this one device" call was silently falling through to "revoke all sessions." Added a `LogoutRequest` body schema.
7. Assorted expired-JWT UX: `get_current_user` and `refresh_tokens()` now distinguish `ExpiredSignatureError` from other `JWTError`s and say "expired" instead of a generic "could not validate credentials" — `refresh_tokens()` was also accidentally catching its own raised `HTTPException`s in a blanket `except Exception`, discarding their specific messages.
8. Several test-only bugs fixed alongside (wrong fixture password, stale field names after model renames — `PatientDiagnosis.diagnosis`→`description`, `Appointment.appointment_type` doesn't exist, `Visit.diagnosis`/`notes`→`provisional_diagnosis`/`treatment_plan` — missing required fields, sync `expire_all()` incorrectly awaited, a hardcoded month in an invoice-number assertion, and a dashboard test hitting a real un-migrated dev DB instead of the isolated test one).

**Gate (revised to be honest about what's actually verified):** `pytest` is green locally (**432 passed, 2 xfailed, 0 failed**, verified 2026-09-24) — CI (`.github/workflows/backend-tests.yml`) has not been re-run since these fixes, though its environment matches what was verified locally (`pip install -e ".[dev]"`, real Postgres+pgvector, real Redis) and should now pass. `alembic upgrade head` against an empty database produces all 34 tables (verified against a scratch DB, see above) — `conftest.py` itself doesn't exercise this path yet (T6, deferred). Every doc claim contradicted in §1 has been corrected below.

### Stage 1 — Shippable · by 2026-11-21

- [x] **Password reset + email verification — done 2026-09-23.** Implemented the previously commented-out endpoints (`POST /auth/password/forgot`, `/password/reset`, `/auth/email/verify`, `/email/resend`), Celery-delivered system email (`app/core/system_email.py`, provider selected by `EMAIL_PROVIDER`), and covering tests (§1, finding 5 — closed).
- [x] **Google Sign-In and registration — done 2026-09-23, not originally scoped for this stage.** `POST /auth/google` + `POST /auth/google/register`, server-side ID token verification, auto-linking to an existing password account by verified email. Landed alongside the password-reset work since both touch the same auth surface; see `docs/api/authentication.md`. Doesn't close any Stage 1 gate item on its own — noted here so Stage 1's scope reflects what actually shipped, not just what was planned.
- Dockerfiles for api/worker/web, `compose.prod.yml`, Caddy, `deploy.sh`, staging project on the same box (D9)
- Nightly `pg_dump` to object storage **and a rehearsed restore** (D10)
- [x] **httpOnly refresh cookie + route guard — done 2026-09-25 (D8).** Refresh token no longer transits the JSON response body at all (`TokenResponse`/`LoginResponse`/`GoogleAuthResponse.tokens.refresh_token` all `str | None = None`, omitted via `response_model_exclude_none=True`) — `login`/`login-2fa`/`google`/`refresh` now set it as an httpOnly, `SameSite=Lax` cookie (`Secure` in production only) via `response.set_cookie` in `app/modules/auth/routes.py`; `/refresh` and `/logout` read it back via `request.cookies`, with an optional body fallback for non-browser clients (checked in that order — an explicit body value wins, since a browser never sends one). Cookie `Path` is `/` (not scoped to `/api/v1/auth`) — a path-scoped cookie would be invisible to the frontend's own page-navigation requests, which is what the route guard needs to see. `LogoutRequest` gained an explicit `all_sessions: bool` flag, since a browser can no longer supply the raw token to opt into revoking every session — omitting the body now means "log out this session" (via the cookie), not "log out everywhere," which is the safer default now that every ordinary browser logout omits the body. Frontend: access token moved to in-memory-only Zustand state (`store/authStore.ts`, no longer written to any cookie); `lib/api/client.ts` added `withCredentials: true` and reads the token from the store instead of `js-cookie`; `(dashboard)/layout.tsx` gained a silent-refresh bootstrap (`POST /auth/refresh` + `GET /auth/me`) so a page reload re-derives the access token from the httpOnly cookie instead of losing the session. `frontend/src/proxy.ts` (Next.js 16 renamed the `middleware.ts` convention to `proxy.ts` mid-implementation — migrated rather than leave known-deprecated code) does a presence-only check on the cookie to gate direct navigation to protected routes; real authorization stays enforced by the backend's 401s. Verified live in a real browser (Playwright-driven Chromium against the actual dev servers, not just the test suite): login sets exactly one auth cookie and it's httpOnly (`document.cookie` doesn't contain it), a full page reload preserves the session via silent refresh with zero console/network errors, a cookie-less direct request to `/dashboard` redirects to `/login`, and logout does too. One real bug caught by that live run and fixed before it passed: the bootstrap's `/auth/me` call was firing before the just-refreshed access token was stored, so it 401'd on every reload until the token is written to the store first. Backend: 12 test call sites across `test_auth_routes.py`/`test_auth_security.py`/`test_multi_tenant_isolation.py`/`test_api_contracts.py` updated to read the rotated cookie instead of a JSON field; `pytest -q` still 442 passed / 1 xfailed / 0 failed.
- [x] **Remove the five legacy `/auth/admin/*` endpoints — done 2026-09-25.** They shadowed the canonical `/api/v1/admin/*` ones (`app/modules/admin/routes.py`); the frontend had already fully migrated (confirmed via grep — nothing called `authApi.provisionClient`/`listAdminClients`/`getAdminClient`/`listPendingTenants`/`approveTenant`), and no backend test hit the `/auth/admin/*` paths directly (they simulate admin actions via direct DB writes instead). Deleted the 5 routes, their `AuthService` methods, and their now-dead schemas; route count assertion updated 136 → 131 (`tests/unit/test_route_registration.py`).
- [x] **Billing enforcement — done 2026-09-24.** `require_plan()` (`app/core/dependencies.py`) checks the tenant's `plan`/`plan_expires_at` in the DB (not the JWT claim), so a downgrade or expiry revokes pro access immediately — closes `test_plan_downgrade_revokes_pro_access` (§1, finding 6; the xfail from Stage 0 §5.0 no longer applies). `usage_tracking` gets real writers via `app/core/usage_tracking.py`'s `UsageService`: prescription issue (`prescription/service.py`, both create-as-issued and draft→issued via `PATCH`), SMS send (`integration/routes.py`), and AI query (`ai/routes.py`, tracked even though the endpoint itself is still a 501 stub). Migration `ed07cf4aebc7` adds `usage_tracking.sms_sent` and a `(tenant_id, usage_date)` unique constraint. Surfaced read-only via `GET /admin/tenants/{id}/usage`. Scoped narrowly per the doc's own norm: no quota *blocking* (that's Stage 4) and no `plan_expires_at` check on general tenant-scoped endpoints, only on `require_plan`-gated ones — broader enforcement is untested, undefined product behavior. `pytest -q`: 442 passed / 1 xfailed / 0 failed (verified 2026-09-24).
- [x] **Frontend CI + Playwright smoke path — done 2026-09-25 (T7).** `frontend/playwright.config.ts` + `frontend/e2e/smoke.spec.ts` cover the one path T7 scoped: login → create patient → build a prescription → issue → generate PDF (asserted at the API layer — `pdf_url` is still a hardcoded placeholder domain per `prescription/service.py`, no storage adapter yet, D6/Stage 3 — fetching the file itself isn't meaningful yet). New `.github/workflows/frontend-tests.yml` runs Postgres+Redis services, migrates and seeds the DB, starts the backend, then `tsc --noEmit` → `eslint` → the Playwright suite, uploading the HTML report on failure. Verified by actually running it end-to-end against real dev servers (not just written and trusted) — caught and fixed two real bugs in the process: (1) the D8 silent-refresh bootstrap in `(dashboard)/layout.tsx` called `GET /auth/me` before storing the just-refreshed access token, so every page reload's profile fetch 401'd; (2) `scripts/seed.py`'s `seed_medicines`/`seed_symptoms` unconditionally set `tenant_id` on every row, which has failed the `ck_medicines_tenant_global`/`ck_symptoms_tenant_global` CHECK constraints (and silently rolled back the *entire* seed, including the test users) ever since D1 landed 2026-09-24 — anyone running `./scripts/run_seed.sh` fresh since then would have hit this. Fixed to only attach `tenant_id` when the JSON row isn't `is_global`.

**Gate:** a real clinic signs up on a public URL, recovers a forgotten password unaided, uses the product for a full week, and you restore the production database from backup into staging in under 30 minutes.

### Stage 2 — Catalog Foundation · by 2026-12-19 · *the keystone*

- [x] **`GlobalCatalogModel` + nullable `tenant_id` + CHECK constraint migration — done 2026-09-24, no backfill needed (D1).** Landed ahead of the rest of Stage 2 since it was blocking basic admin catalog curation. `medicines`, `symptoms`, `medicine_aliases`, `symptom_aliases`, `medicine_symptom_mappings` now inherit `GlobalCatalogModel` (`app/shared/models/base.py`) with a nullable `tenant_id`; `medicines`/`symptoms` additionally carry a CHECK constraint (`ck_medicines_tenant_global`/`ck_symptoms_tenant_global`) enforcing `(is_global AND tenant_id IS NULL) OR (NOT is_global AND tenant_id IS NOT NULL)`. Migration `ba209a25bf7d`, `down_revision` = `283e895eb3eb`. No backfill was needed — every existing row already had a non-null `tenant_id`, which already satisfied the constraint's tenant-owned branch. Verified: `pytest -q` unchanged at 432 passed / 2 xfailed / 0 failed; manually confirmed a global insert (`is_global=True, tenant_id=None`) now succeeds and that both invalid combinations (`is_global=True` with a tenant_id, `is_global=False` with a null tenant_id) are rejected by the CHECK constraint.
- `medicine` / `symptom` service layer; routes thinned to handlers; one `_visible_query()` (D3) — not started
- RLS on the eight clinical tables (D2) — not started
- `/api/v1/public/*` router boundary (D4) and unified `tsvector` search (D5) — not started
- Seed **300 practitioner-reviewed homeopathy medicines** and their symptom mappings — one system done properly, not four done thinly (§2.1) — not started; the schema can now hold global rows, nothing has been seeded into it yet

**Gate:** ~~an admin creates a global medicine successfully — the operation that returns a 500 today~~ **met 2026-09-24** (see D1 above); a doctor's prescription autocomplete returns seeded global medicines — not yet, no seed data exists; and a deliberately mis-written service query against a clinical table raises instead of returning another tenant's rows — not yet, D2/D3 not started. Stage 2 is not gated-complete: one of three conditions holds.

**Note (added 2026-09-23):** the taxonomy expansion in `docs/planning/future-scope-2026-09.md` (discipline/condition/therapy/references) is meant to land in this same migration wave when it's actually scheduled — bundled with D1 rather than done twice. It isn't scheduled yet, so it isn't in this stage's scope or gate above; adding it later will widen this stage's surface without moving its date, which is a cost to name explicitly when that happens, not now.

### Stage 3 — Library & Public Web · Q1 2027

- Storage adapter (D6); EPUB ingestion via Celery with checksums and idempotent re-import (D7)
- Books/chapters/sections become catalog rows; reading progress, bookmarks, and highlights stay user- and tenant-scoped
- Reader UI; **5 texts whose rights are cleared first** — public-domain classical works only until a rights review says otherwise
- Public knowledge pages (SSG/ISR) for medicines, symptoms, and books — the SEO surface that also produces the practitioner supply a directory would later need

**Gate:** 5 books ingested, searchable, and readable end to end; public pages served and indexable; re-running an import creates zero duplicate rows.

### Stage 4 — Retrieval Assistant · Q2 2027

- Embed ingested sections; HNSW index; retrieval module without LangChain (T3)
- Every citation resolved against a real row ID before the response is returned; refuse rather than answer when no source supports the question
- The 50-question bilingual eval set from T4, run as a gate rather than a demo
- Pro-plan quota enforced through the `usage_tracking` written in Stage 1

**Gate:** ≥80% of eval answers carry a correct, resolvable citation, and zero answers contain an uncited clinical claim. If that bar is not met, the feature does not ship — an alternative-medicine assistant that invents sources is a liability, not a feature.

### After Stage 4, gated not dated

Public doctor directory (gate: ≥20 practitioners with complete public profiles) · audit log UI · notification templates · bulk operations. Directory (colleges, formalizing the doctor directory above) and Content/CMS are scoped as Track D/Track C in `docs/planning/future-scope-2026-09.md` §2.3 — kept out of this list because they're wider than a bullet point and belong to their own document, not because they're less real.

---

## 6. Deployment & operations plan

Because nothing is deployed, this is a plan, not a description.

**Topology (D9):** one VPS; Caddy terminates TLS and proxies `/api` to uvicorn and everything else to Next standalone; `worker` and `beat` run from the same image as `api`; Postgres 16 + pgvector, Redis, and MinIO run as containers with named volumes.

**Deploy:** `deploy.sh` = pull, build, `alembic upgrade head`, `docker compose up -d`, health check, roll back to the previous image tag on failure. Migrations run before the new image serves traffic and stay additive, so rollback never requires a down-migration in production.

**Backups:** nightly `pg_dump` and a MinIO bucket sync to off-box object storage, 30-day retention. The restore drill is quarterly and timed; an untested backup is not a backup.

**Monitoring:** Sentry for errors, `/metrics` scraped by an uptime checker, alerts on 5xx rate and on a failed nightly backup. That is the whole monitoring stack at this size, deliberately.

**Capacity:** this design is sized for ~200 clinics. The trigger to revisit is the first of: p95 latency past 500 ms under normal load, a backup that no longer completes in the nightly window, or a contract that requires an availability SLA.

---

## 7. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **Clinical liability.** An AI assistant giving treatment guidance in alternative medicine is legally and ethically exposed | High | Retrieval with citations only, never prescriptive phrasing; permanent non-dismissible disclaimer; every answer logged with its sources; Stage 4's gate enforces this before launch, not after |
| **Content rights.** Ingesting copyrighted medical texts | High | Rights review precedes ingestion; public-domain works only in Stage 3; per-book access capability fields in the schema from day one |
| **Patient data protection.** Health records under Bangladeshi and any future export-market rules | High | RLS (D2), encryption at rest for credentials (already), audit trail, documented retention policy before the first paying clinic |
| **Single VPS is a single point of failure** | Medium | Tested restores, off-box backups, a documented rebuild procedure; accepted deliberately at this scale |
| **Bus factor of one** | Medium | Decisions recorded as ADRs; the deploy path is a script in the repo, not knowledge in a head |
| **Documentation drift** — the root cause of this entire revision | Medium | §8; docs asserting capability must cite a file or a test |
| **Scope regrowth** | Medium | §2.1 is a commitment; re-adding a cut item requires writing down what it displaces |

Track D/Track C carry their own risks (editorial content liability, directory data staleness) — see `docs/planning/future-scope-2026-09.md`, not duplicated here since that scope isn't scheduled.

---

## 8. Revised success metrics

The previous targets (200 paying clinics and an India expansion by Q3 2027, solo) are replaced with numbers a single developer can be held to:

| Horizon | Target |
|---|---|
| 2026-10-07 | Test suite green; zero doc claims contradicted by code |
| 2026-11-21 | Deployed, publicly reachable, **1 paying clinic** using it daily; restore drill passed |
| 2026-12-19 | Global catalog writable; 300 reviewed medicines live; **5 paying clinics** |
| Q1 2027 | 5 books readable and searchable; public pages indexed; **10 paying clinics** |
| Q2 2027 | Assistant passes its citation gate or does not ship; **25 paying clinics** |

Ongoing: 99% monthly uptime measured by an external checker (not asserted), p95 API latency under 500 ms, and zero cross-tenant incidents.

---

## 9. Documentation rules going forward

The gap in §1 is not a documentation problem; it is a problem that documentation made invisible. Three rules:

1. **A status claim cites evidence** — a file path, a test name, or a command whose output supports it. "16/16 passing" without a date and a command is a rumour.
2. **Planned and built are never the same verb.** Roadmap items are written in the infinitive; only shipped items are ticked.
3. **Numbers come from commands, not from memory.** Endpoint counts, table counts, and file counts are regenerated when touched, or removed from the doc.

---

## Related

- `docs/architecture/architecture-inventory.md` — the code-verified inventory this revision builds on
- `docs/ROADMAP.md` — superseded in sequencing and metrics by §5 and §8
- `docs/status/current.md` — superseded in status by §1
- `docs/planning/future-scope-2026-09.md` — Track D (Directory) and Track C (Content/CMS): direction and sequencing beyond Track P/K, kept separate because it isn't scheduled (§2.3)
