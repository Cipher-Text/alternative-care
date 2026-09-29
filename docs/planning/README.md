# Planning Docs Guide

This guide classifies planning documents by how they should be used.

## Read Order

1. `../status/current.md` — current code-aligned implementation status
2. `../ROADMAP.md` — high-level active roadmap
3. `roadmap-detailed.md` — detailed active roadmap and phase breakdown

## Document Classification

| File | Classification | Use It For | Avoid Using It For |
|------|----------------|------------|---------------------|
| `../ROADMAP.md` | Active | high-level priorities, current phase direction | endpoint-level implementation truth |
| `roadmap-detailed.md` | Active | detailed phase execution planning and sequencing | exact API/UI implementation state without code verification |

Historical phase notes, proposal drafts, one-time implementation reports, and completed checklists are not maintained as a separate archive. Current decisions belong in active planning, architecture, or changelog documents.

## Source-of-Truth Rule

When any planning document conflicts with implementation:
1. `backend/app/main.py` (active routers)
2. `backend/app/modules/*/routes.py` (actual endpoints)
3. `frontend/src/app/**` (implemented UI routes)
4. `../status/current.md` (narrative status)

## Current Baseline Snapshot (2026-09-30)

- Backend active routers: 16 modules (`backend/app/main.py`)
- API route methods: 144 under `/api/v1`, plus `/`, `/health`, `/metrics` (asserted in `backend/tests/unit/test_route_registration.py`)
- Frontend includes auth/recovery, public landing/knowledge/institutions, practice workflows, and platform-admin routes; inspect `frontend/src/app/` for the live route tree
- The public doctor/practitioner directory remains planned; public global medicine/symptom catalogs and institutions directory are implemented
- AI route status: `/api/v1/ai/query` exists as a `501 Not Implemented` contract stub, gated by a DB-backed plan check and now tracked in `usage_tracking` (Stage 1 "Billing enforcement", 2026-09-24)
- Admin Phase A: complete — `app/modules/admin/` at `/api/v1/admin` with 11 endpoints, including `POST /admin/tenants/{id}/doctors` (add a doctor under an existing tenant, shipped 2026-07-12) and `GET /admin/tenants/{id}/usage` (tenant billing usage, shipped 2026-09-24)

## Maintenance

Update this file when:
- planning files are added/removed
- a document changes classification (for example, proposal → active execution plan)
- baseline snapshot meaningfully changes
