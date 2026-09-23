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

Historical phase notes, proposal drafts, one-time implementation reports, and completed checklists live in `../archive/`.

## Source-of-Truth Rule

When any planning document conflicts with implementation:
1. `backend/app/main.py` (active routers)
2. `backend/app/modules/*/routes.py` (actual endpoints)
3. `frontend/src/app/**` (implemented UI routes)
4. `../status/current.md` (narrative status)

## Current Baseline Snapshot (2026-09-23)

- Backend active routers: 14 modules
- Module endpoints: 133 total (+ `/`, `/health`, `/metrics`) — `POST /auth/login-2fa` and 4 password-reset/email-verification endpoints added 2026-09-23 (see revision-2026-09.md Stage 0/1)
- Frontend implemented route groups (11): auth/login, dashboard, patients, appointments, prescriptions, profile, payments, medicines, symptoms, settings/integrations, admin (dashboard, clients, users) — 132 source files total
- AI route status: `/api/v1/ai/query` exists as a `501 Not Implemented` contract stub
- Admin Phase A: complete — `app/modules/admin/` at `/api/v1/admin` with 10 endpoints, including `POST /admin/tenants/{id}/doctors` (add a doctor under an existing tenant, shipped 2026-07-12)

## Maintenance

Update this file when:
- planning files are added/removed
- a document changes classification (for example, proposal → active execution plan)
- baseline snapshot meaningfully changes
