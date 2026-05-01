# E2E Tests (Playwright)

## Prerequisites
- App running (`./run.sh` from repo root)
- Seeded DB (`./backend/scripts/run_seed.sh`)

## Run
- `npx playwright test -c tests/e2e/playwright.config.ts`
- `npx playwright test -c tests/e2e/playwright.config.ts tests/e2e/specs/smoke`
