# AltCare Documentation

Central documentation hub for the repository.

## Start Here

1. [Project Overview](../README.md)
2. [Getting Started](../GETTING_STARTED.md)
3. [Documentation Index](INDEX.md)
4. [Current Status](status/current.md)

## Documentation Map

### Setup
- [Getting Started](../GETTING_STARTED.md)
- [Backend Setup](setup/backend.md)
- [Frontend Setup](setup/frontend.md)

### API
- [API Overview](api/README.md)
- [Authentication](api/authentication.md)
- [Patients](api/patients.md)
- [Doctor](api/doctor.md)
- [Appointments](api/appointments.md)
- [Prescriptions](api/prescriptions.md)
- [Payments](api/payments.md)
- [Dashboard](api/dashboard.md)
- [Integrations](api/integrations.md)

### Architecture
- [Architecture Overview](architecture/README.md)
- [Database Deep Dive](architecture/database.md)
- [Database Schema](architecture/database-schema.md)
- [Authentication Design](architecture/authentication.md)
- [Multi-tenancy](architecture/multi-tenancy.md)
- [Tech Stack](architecture/tech-stack.md)

### Development
- [Quick Reference](development/quick-reference.md)
- [Frontend Checklist](development/frontend-checklist.md)
- [i18n Guide](development/i18n.md)

### Planning and Status
- [Current Status](status/current.md)
- [Roadmap](ROADMAP.md)
- [Detailed Roadmap](planning/roadmap-detailed.md)
- [Testing Strategy](testing/TEST_STRATEGY.md)
- [Phase 1 Kickoff](planning/phase1-kickoff.md)
- [Phase 1 Tasks](planning/phase1-tasks.md)
- [UX Improvements](planning/ux-improvements.md)
- [Documentation Refactor Proposal](planning/docs-refactor.md)

## AI/Codex Notes

If you are using Codex/QAI tooling to reason about current behavior:
- Treat `backend/app/main.py` as the source of truth for active API routers.
- Treat route decorators in `backend/app/modules/*/routes.py` as endpoint truth.
- Treat `frontend/src/app/**` as the source of truth for implemented UI routes.
- Treat AI/RAG as planned work; currently only `/api/v1/ai/query` stub exists and returns `501`.

## Maintenance Rule

When implementation changes:
1. Update this map if files or sections moved.
2. Update `status/current.md` for feature-state changes.
3. Update API docs for endpoint changes.
4. Move dated progress reports to `archive/` once they are no longer active planning material.
