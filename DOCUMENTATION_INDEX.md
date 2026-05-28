# AltCare Documentation Index

This root index is a short pointer to the maintained documentation hub.

## Start Here

1. [README.md](README.md) - project overview and quick start
2. [GETTING_STARTED.md](GETTING_STARTED.md) - local setup flow
3. [docs/README.md](docs/README.md) - documentation hub
4. [docs/INDEX.md](docs/INDEX.md) - complete navigation map
5. [docs/status/current.md](docs/status/current.md) - current implementation status

## Current Source of Truth

When documentation and implementation disagree, verify in this order:

1. `backend/app/main.py` for active backend routers
2. `backend/app/modules/*/routes.py` for actual API endpoints
3. `frontend/src/app/**` for implemented UI routes
4. `docs/status/current.md` for narrative project status

## Maintenance

- Keep long-form docs under `docs/`.
- Keep root docs limited to onboarding, release notes, security notes, and agent guidance.
- Move dated progress reports to `docs/archive/` after they stop guiding active work.
- Update [docs/status/current.md](docs/status/current.md) after feature-state changes.

Last updated: 2026-05-29
