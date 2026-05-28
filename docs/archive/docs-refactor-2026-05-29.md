# Documentation Refactor Proposal

Last updated: 2026-05-29

## Problem

The repository has useful documentation, but the information is split across root-level files, `docs/`, backend docs, frontend docs, and dated progress reports. Some files duplicate status snapshots, and older completion reports can conflict with the current code-aligned status.

## Recommended Target Structure

Keep the root directory small:

- `README.md` - public project overview and shortest runnable quick start
- `GETTING_STARTED.md` - end-to-end local setup
- `DOCUMENTATION_INDEX.md` - short pointer to the maintained docs hub
- `CHANGELOG.md` - release history
- `SECURITY_AUDIT_REPORT.md` - current security review
- `CLAUDE.md` - AI coding-agent guidance

Keep long-form documentation under `docs/`:

- `docs/status/current.md` - only current narrative status
- `docs/api/` - endpoint contracts by module
- `docs/architecture/` - system design and data model material
- `docs/setup/` - backend/frontend setup details
- `docs/development/` - workflow, checklist, i18n, debugging notes
- `docs/planning/` - active plans and roadmap work
- `docs/archive/` - historical progress reports and superseded setup docs

## Refactor Steps

1. Make `docs/README.md` and `docs/INDEX.md` the only full navigation docs.
2. Keep root `DOCUMENTATION_INDEX.md` as a short pointer, not a second full index.
3. Move stale root reports into `docs/archive/` after confirming they are no longer active:
   - `DESIGN_UPDATES.md`
   - `THEME_FIXES_SUMMARY.md`
   - `THEME_SYSTEM.md`
   - `THEME_CHECKER.md`
   - `THEME_QUICK_TEST.md`
   - `MEDICINE_LIBRARY_FIXES.md`
4. Merge durable content from completion reports into the relevant stable docs before archiving:
   - API behavior into `docs/api/*.md`
   - setup behavior into `docs/setup/*.md`
   - current feature status into `docs/status/current.md`
5. Add lightweight ownership rules to each major doc family:
   - API docs change with route/schema changes.
   - Setup docs change with dependency, command, or environment changes.
   - Status docs change with feature availability.
   - Planning docs change with roadmap decisions.

## Naming Rules

- Use lowercase kebab-case for new docs under `docs/`.
- Use dates only for archived reports, not active docs.
- Avoid duplicate "current status" sections outside `docs/status/current.md`.
- Prefer links to source files or stable docs instead of copying large repeated blocks.

## Validation Checklist

Before merging a docs cleanup:

1. Run `rg --files -g '*.md'` and confirm every active doc is linked from `docs/README.md` or intentionally archived.
2. Search for stale endpoint counts, module counts, and old dates.
3. Check for broken internal links after moving files.
4. Verify `README.md`, `GETTING_STARTED.md`, `docs/README.md`, and `docs/status/current.md` agree on current scope.
