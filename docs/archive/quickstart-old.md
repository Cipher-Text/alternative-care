---
title: "AltCare Quick Start Guide"
type: "setup"
difficulty: "beginner"
time: "5 minutes"
last_updated: "2026-05-01"
ai_summary: "Get AltCare running in 5 minutes with Docker"
---

# 🚀 Quick Start Guide (5 Minutes)

Get AltCare up and running in 5 minutes.

---

## ✅ Prerequisites

- Docker & Docker Compose
- Git
- **That's it!** Everything else runs in Docker

---

## 📦 Step 1: Clone Repository

```bash
git clone https://github.com/your-org/alternative-care.git
cd alternative-care
```

---

## 🐳 Step 2: Start Infrastructure

```bash
# Start PostgreSQL, Redis, MinIO
docker compose up -d

# Verify containers are running
docker ps
```

**Should see:**
- `altcare_postgres` (PostgreSQL 16)
- `altcare_redis` (Redis 7)
- `altcare_minio` (MinIO S3)

---

## 🔧 Step 3: Backend Setup

```bash
cd backend

# Run automated setup script
./quick_start.sh
```

**Script does:**
1. Creates Python virtual environment
2. Installs dependencies
3. Creates `.env` file
4. Runs database migrations
5. Seeds initial data

---

## ▶️ Step 4: Start Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload
```

**Backend running at:** http://localhost:8000

---

## ✨ Step 5: Verify Backend

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","environment":"development","version":"0.9.0"}
```

**API Docs:** http://localhost:8000/docs

---

## 🎨 Step 6: Frontend Setup (Optional)

```bash
cd ../frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Frontend running at:** http://localhost:3000

---

## 🎉 Done!

**You now have:**
- ✅ Backend API: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ Frontend: http://localhost:3000 (if started)

---

## 🧪 Test It Out

### 1. Login

Go to: http://localhost:3000/login

**Default credentials** (created by seed data):
- Email: `admin@altcare.com`
- Password: `admin123`

### 2. Explore API

Visit: http://localhost:8000/docs

Try the endpoints:
1. POST `/auth/login` - Get JWT token
2. GET `/patients` - List patients
3. GET `/dashboard/overview` - View stats

---

## 🛠️ Common Commands

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Database migrations
cd backend && alembic upgrade head

# Run tests
cd backend && pytest

# Stop infrastructure
docker compose down
```

---

## ❓ Troubleshooting

### Port 8000 in use?

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Database connection error?

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart if needed
docker restart altcare_postgres
```

### Frontend won't start?

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

---

## 📚 Next Steps

**After quick start:**

1. **Detailed Setup:** [backend.md](backend.md) or [frontend.md](frontend.md)
2. **API Reference:** [../api/README.md](../api/README.md)
3. **Architecture:** [../architecture/README.md](../architecture/README.md)
4. **Development:** [../development/getting-started.md](../development/getting-started.md)

---

## 🤖 AI Quick Reference

**Q: How do I start the project?**
→ `docker compose up -d` → `cd backend && ./quick_start.sh` → `uvicorn app.main:app --reload`

**Q: What's the default login?**
→ admin@altcare.com / admin123

**Q: Where are the API docs?**
→ http://localhost:8000/docs

**Q: How do I reset the database?**
→ `docker compose down -v` → `docker compose up -d` → `alembic upgrade head`

---

**Time to Complete:** 5 minutes ✅  
**Difficulty:** Beginner ✅  
**Last Updated:** May 1, 2026
