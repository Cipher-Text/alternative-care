# E2E Tests (Playwright)

## Prerequisites
- App running (`./run.sh` from repo root)
- Seeded DB (`./backend/scripts/run_seed.sh`)

## Run
- `npx playwright test -c tests/e2e/playwright.config.ts`
- `npx playwright test -c tests/e2e/playwright.config.ts tests/e2e/specs/smoke`
- API path regressions:
  - `cd frontend && NODE_PATH=$PWD/node_modules E2E_BASE_URL=http://localhost:3000 ./node_modules/.bin/playwright test ../tests/e2e/specs/regression/api-paths.spec.ts --config ../tests/e2e/playwright.config.ts --project chromium`
