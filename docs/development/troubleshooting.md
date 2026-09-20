# Troubleshooting

Common issues and fixes for AltCare development.

---

## Backend

**Note:** `docker-compose.yml` only runs Redis and MinIO (`docker compose up -d`). PostgreSQL is **not** containerized — it must be installed and running locally on port 5432 (see `backend/.env` / `DATABASE_URL`). There is no `altcare_postgres` container; use a local `psql` connection instead of `docker exec`.

**pgvector missing:**
```bash
psql "$DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS vector;"
# Or, connecting directly:
psql -U altcare -d altcare_dev -h localhost -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
# Or: uvicorn app.main:app --reload --port 8001
```

**Migration stuck:**
```bash
alembic current && alembic history

# Reset (DEV ONLY - destroys data):
psql -U altcare -d altcare_dev -h localhost \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

**Test DB errors:**
Tests use `altcare_test` database (auto-created by `tests/conftest.py`). Ensure PostgreSQL is running.

---

## Frontend

**CORS errors:**
Check `backend/.env`: `CORS_ORIGINS=http://localhost:3000,http://localhost:8000` (comma-separated string, not a JSON array — parsed by `parse_cors_origins` in `app/core/config.py`)

**API connection refused:**
Check `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` (includes the `/api/v1` prefix — see `frontend/src/lib/api/client.ts`)

**Port 3000 in use:**
```bash
lsof -ti:3000 | xargs kill -9
# Or: PORT=3001 npm run dev
```

**Module not found / stale build:**
```bash
cd frontend
rm -rf .next node_modules
npm install && npm run dev
```

**TypeScript errors:**
Update `frontend/src/types/` to match backend schemas. Run `npm run build`.
