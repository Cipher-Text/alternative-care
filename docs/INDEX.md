---
title: "AltCare Documentation Index"
type: "navigation"
last_updated: "2026-05-01"
ai_purpose: "Fast navigation map for AI assistants"
version: "0.9.0"
---

# 📚 AltCare Documentation Index (AI-Optimized)

**Purpose:** Quick navigation for AI assistants and developers  
**Total Docs:** 20 focused modules  
**Max File Size:** 600 lines (AI context-friendly)

---

## 🚀 Quick Start (5 minutes)

**New to the project?**
1. Read: `../README.md` (project overview)
2. Setup: `setup/quickstart.md` (5-minute setup)
3. API: `api/README.md` (71 endpoints overview)

**AI: For quick answers, start here ↑**

---

## 📖 By User Type

### 👨‍💻 New Developer (First Day)
```
1. ../README.md              → What is AltCare?
2. setup/quickstart.md       → 5-min setup
3. development/getting-started.md → First contribution
4. api/README.md             → API overview
```

### 🔧 Backend Developer
```
1. setup/backend.md          → Backend setup
2. api/ (7 files)            → All endpoints
3. architecture/database-schema.md → 30 tables
4. development/testing.md    → Testing guide
```

### 🎨 Frontend Developer
```
1. setup/frontend.md         → Frontend setup  
2. api/ (7 files)            → API endpoints
3. development/code-patterns.md → React patterns
4. development/i18n.md       → Bilingual UI
```

### 🚀 DevOps / Deployment
```
1. setup/deployment.md       → Production deploy
2. architecture/tech-stack.md → Infrastructure
3. architecture/multi-tenancy.md → Tenant isolation
```

---

## 📁 By Document Type

### 🔧 Setup Guides (4 files)
| File | Purpose | Lines | AI Summary |
|------|---------|-------|------------|
| `setup/quickstart.md` | 5-minute setup | 200 | Docker + basic config |
| `setup/backend.md` | Backend setup | 400 | PostgreSQL, Redis, migrations |
| `setup/frontend.md` | Frontend setup | 400 | Next.js, React Query, shadcn/ui |
| `setup/deployment.md` | Production deploy | 300 | Caddy, Docker Compose, CI/CD |

### 🌐 API Reference (7 files, ~250 lines each)
| File | Endpoints | AI Summary |
|------|-----------|------------|
| `api/README.md` | Overview | 71 total endpoints across 7 modules |
| `api/authentication.md` | 9 | JWT login, 2FA, refresh, logout |
| `api/patients.md` | 14 | CRUD, search, tags, diagnoses |
| `api/appointments.md` | 10 | Appointments + visits, conflicts |
| `api/prescriptions.md` | 8 | Builder, PDF, immutable workflow |
| `api/payments.md` | 12 | Cash, bKash, invoices |
| `api/dashboard.md` | 6 | Analytics, charts, metrics |

### 🏗️ Architecture (6 files)
| File | Purpose | Lines | AI Summary |
|------|---------|-------|------------|
| `architecture/README.md` | Overview | 150 | System design, patterns |
| `architecture/database-schema.md` | Schema | 600 | 30 tables with relationships |
| `architecture/database-migrations.md` | Migrations | 300 | Alembic guide, common patterns |
| `architecture/multi-tenancy.md` | Isolation | 400 | Row-level tenant_id filtering |
| `architecture/authentication.md` | Auth design | 350 | JWT, 2FA, RBAC, plan gating |
| `architecture/tech-stack.md` | Technologies | 400 | FastAPI, Next.js, PostgreSQL |

### 💻 Development (6 files)
| File | Purpose | Lines | AI Summary |
|------|---------|-------|------------|
| `development/README.md` | Overview | 100 | Dev workflow, conventions |
| `development/getting-started.md` | Onboarding | 300 | First contribution guide |
| `development/testing.md` | Testing | 400 | Pytest, coverage, patterns |
| `development/code-patterns.md` | Patterns | 400 | FastAPI, React, TypeScript |
| `development/i18n.md` | i18n | 300 | EN/BN bilingual support |
| `development/troubleshooting.md` | Issues | 500 | Common problems + fixes |

### 📋 Planning (3 files)
| File | Purpose | Lines | AI Summary |
|------|---------|-------|------------|
| `planning/ROADMAP.md` | Timeline | 400 | Phases 1-4, 11 months |
| `planning/STATUS.md` | Current | 200 | Week 15/18 complete |
| `planning/phases.md` | Details | 600 | Week-by-week breakdown |

---

## 🔍 By Common Question

### "How do I setup the project?"
→ `setup/quickstart.md` (5 min) or `setup/backend.md` (detailed)

### "What are the API endpoints?"
→ `api/README.md` (overview) → `api/patients.md` (specific module)

### "How does the database work?"
→ `architecture/database-schema.md` (30 tables)

### "How do I test?"
→ `development/testing.md` (pytest guide)

### "How does authentication work?"
→ `architecture/authentication.md` (JWT + 2FA design)

### "How do I add a new feature?"
→ `development/getting-started.md` → `development/code-patterns.md`

### "What's the current status?"
→ `planning/STATUS.md` (week-by-week progress)

### "How do I deploy?"
→ `setup/deployment.md` (production guide)

---

## 🏷️ By Tag

**#setup:** setup/
**#api:** api/
**#architecture:** architecture/
**#testing:** development/testing.md
**#database:** architecture/database-schema.md
**#auth:** api/authentication.md, architecture/authentication.md
**#frontend:** setup/frontend.md, development/code-patterns.md
**#deployment:** setup/deployment.md

---

## 📊 Quick Stats (AI Reference)

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 71 |
| **Modules** | 7 (Auth, Doctor, Patient, Appointments, Rx, Payment, Dashboard) |
| **Database Tables** | 30 |
| **Test Coverage** | 85%+ |
| **Languages** | English + Bengali |
| **Auth Methods** | JWT + TOTP 2FA |
| **Payment Gateways** | Cash, bKash |
| **Backend Status** | Week 12/14 (86% complete) |
| **Frontend Status** | Week 15/18 (83% complete) |

---

## 🔗 Related Files (Root Level)

| File | Purpose |
|------|---------|
| `../README.md` | Project overview |
| `../SETUP.md` | Quick setup summary |
| `../ROADMAP.md` | High-level timeline |
| `../CLAUDE.md` | AI assistant instructions |
| `../CHANGELOG.md` | Version history |
| `../FRONTEND_SETUP.md` | Detailed frontend guide |

---

## 🤖 AI Assistant Notes

**Context Window Optimization:**
- All files <600 lines
- Modular by topic
- Use INDEX.md to navigate
- Load only needed sections

**Common AI Queries:**
- "setup" → setup/quickstart.md
- "API for X" → api/X.md
- "how does X work" → architecture/X.md
- "how to X" → development/X.md

**Cross-References:**
- Use relative paths: `../setup/backend.md`
- All links verified: 2026-05-01

---

**Last Updated:** May 1, 2026  
**Maintained By:** Development Team  
**AI-Optimized:** Yes ✅  
**Max File Size:** 600 lines ✅
