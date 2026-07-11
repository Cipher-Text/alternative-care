# Troubleshooting

Common issues and fixes for AltCare development.

---

## Backend

**pgvector missing:**
```bash
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
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
docker exec -it altcare_postgres psql -U altcare -d altcare_dev \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

**Test DB errors:**
Tests use `altcare_test` database (auto-created by `tests/conftest.py`). Ensure PostgreSQL is running.

---

## Frontend

**CORS errors:**
Check `backend/.env`: `CORS_ORIGINS=["http://localhost:3000"]`

**API connection refused:**
Check `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`

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
