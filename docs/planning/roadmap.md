# 🗺️ AltCare Development Roadmap

> **High-level view** of the 12-month development plan. For detailed specifications, see [roadmap-detailed.md](roadmap-detailed.md).

**Last Updated:** April 21, 2026  
**Current Phase:** Phase 1 - Core Clinic MVP (Week 1-2 complete)

---

## Timeline Overview

```
2026        Q2          Q3          Q4        2027 Q1
    ├───────────┼───────────┼───────────┼───────────┤
    │  Phase 1  │  Phase 2  │  Phase 3  │  Phase 4  │
    │    MVP    │ Knowledge │  Library  │  AI/RAG   │
    └───────────┴───────────┴───────────┴───────────┘
       14 weeks    8 weeks    10 weeks    12 weeks
```

**Total:** ~44 weeks from start to full platform

---

## Phases at a Glance

### ✅ Phase 0: Planning & Design (Complete)
**Timeline:** 2 weeks (Apr 7-20, 2026)  
**Status:** ✅ Complete

**Deliverables:**
- UI mockups (Admin + Doctor views)
- Database schema (30 tables)
- Technology stack
- Backend foundation **✅ Implemented**

---

### 🔄 Phase 1: Core Clinic MVP (In Progress)
**Timeline:** 14 weeks (May-July 2026)  
**Target Launch:** August 1, 2026  
**Status:** Week 1-2 of 14 complete (15%)

**Goal:** Launch a working clinic management tool for 10 pilot doctors

**What We're Building:**
- 👤 **User Management** - Registration, login, 2FA, roles
- 👨‍⚕️ **Doctor Profiles** - Academic degrees, certifications
- 🏥 **Patient Management** - Records, tags, diagnoses, visits
- 💊 **Prescriptions** - Builder with PDF export
- 💳 **Payments** - bKash/Nagad/cash tracking + invoices
- 📊 **Dashboard** - KPIs, analytics, calendar
- 🔌 **Integrations** - SMS/Email/Payment providers

**Progress:**
```
Week 1-2:  Backend Foundation    ████████████ 100% ✅
Week 3-4:  Auth & Users          ░░░░░░░░░░░░   0% 📋
Week 5-6:  Doctor Profile        ░░░░░░░░░░░░   0% 📋
Week 7-8:  Patient Management    ░░░░░░░░░░░░   0% 📋
Week 9-10: Prescriptions         ░░░░░░░░░░░░   0% 📋
Week 11:   Payments              ░░░░░░░░░░░░   0% 📋
Week 12:   Dashboard             ░░░░░░░░░░░░   0% 📋
Week 13:   Integrations          ░░░░░░░░░░░░   0% 📋
Week 14:   Testing & Launch      ░░░░░░░░░░░░   0% 📋
```

**Success Metrics:**
- 10 pilot doctors actively using daily
- 500+ patients managed
- 200+ prescriptions generated
- 95%+ uptime

**→ Details:** [phase1-tasks.md](phase1-tasks.md)

---

### 📋 Phase 2: Knowledge Base (Planned)
**Timeline:** 8 weeks (Aug-Sep 2026)  
**Status:** Planned

**Goal:** Add medicine database with symptom-based search

**What We'll Build:**
- 💊 **Medicine Database** - 1,000+ medicines (Homeopathy, Ayurveda, Unani, Herbal)
- 🔍 **Symptom Search** - Multi-symptom to remedy matching
- 🏷️ **Medicine Categories** - Filterable by system and category
- 🔗 **Prescription Integration** - One-click add from symptom search

**Filtered by Doctor's Specializations:**
- Homeopathy-only doctor sees only homeopathic medicines
- Multi-system doctor sees all their chosen systems

**Success Metrics:**
- 1,000+ medicines curated
- 85%+ symptom search accuracy
- 30%+ of prescriptions use symptom workflow

---

### 📋 Phase 3: Book Library & Reader (Planned)
**Timeline:** 10 weeks (Oct-Dec 2026)  
**Status:** Planned

**Goal:** Provide access to classical medical texts

**What We'll Build:**
- 📚 **EPUB Upload** - Upload and parse medical books
- 📖 **Book Reader** - In-browser reader with progress tracking
- 🔖 **Bookmarks & Highlights** - Personal annotations
- 📊 **Reading Progress** - Track progress across books

**Initial Library:**
- 5-7 Homeopathy texts (Organon, Materia Medica, etc.)
- 5-7 Ayurveda texts (Charaka Samhita, Sushruta Samhita, etc.)
- 3-4 Unani texts
- 3-4 Herbal medicine texts

**Success Metrics:**
- 20+ books available
- 50%+ of doctors use library monthly
- 10+ minutes average reading session

---

### 📋 Phase 4: AI/RAG Intelligence (Planned)
**Timeline:** 12 weeks (Jan-Mar 2027)  
**Status:** Planned

**Goal:** Add AI-powered clinical reference assistant

**What We'll Build:**
- 🤖 **AI Assistant** - RAG-based chat interface
- 🧠 **Embedding Pipeline** - Chunk and embed all books
- 🔍 **Vector Search** - Cosine similarity retrieval (pgvector)
- 📝 **Grounded Responses** - Always cite source sections
- 🛡️ **Guardrails** - No prescriptive advice, clinical disclaimer

**Technical:**
- OpenAI text-embedding-3-small (1536 dimensions)
- pgvector for storage and similarity search
- LangChain for RAG pipeline
- GPT-4o-mini for responses (cost-optimized)

**Success Metrics:**
- 80%+ of Pro users engage with AI
- 95%+ citation accuracy
- 4.0/5.0+ user rating
- <$300/month OpenAI cost

---

## Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| **Apr 20, 2026** | Phase 0 Complete | ✅ Done |
| **Apr 21, 2026** | Backend Foundation Complete | ✅ Done |
| **May 5, 2026** | Authentication Module | 📋 Target |
| **May 19, 2026** | Patient Management | 📋 Target |
| **Jun 2, 2026** | Prescription System | 📋 Target |
| **Jun 16, 2026** | Payment System | 📋 Target |
| **Jul 1, 2026** | Dashboard & Analytics | 📋 Target |
| **Aug 1, 2026** | **Phase 1 MVP Launch** | 🎯 Goal |
| **Oct 1, 2026** | Phase 2 Knowledge Base | 📋 Target |
| **Dec 15, 2026** | Phase 3 Book Library | 📋 Target |
| **Mar 15, 2027** | Phase 4 AI/RAG | 📋 Target |
| **Apr 1, 2027** | **Full Platform Launch** | 🎯 Goal |

---

## Success Criteria by Phase

### Phase 1 (MVP)
- ✅ 10+ pilot doctors onboarded
- ✅ 500+ patients managed
- ✅ 200+ prescriptions generated
- ✅ 95%+ uptime
- ✅ 80%+ user satisfaction (NPS > 40)

### Phase 2 (Knowledge)
- ✅ 1,000+ medicines in database
- ✅ Symptom search: 85%+ accuracy
- ✅ Used by 80%+ of active doctors

### Phase 3 (Library)
- ✅ 20+ books available
- ✅ 50%+ of doctors use monthly
- ✅ 10+ minute average sessions

### Phase 4 (AI)
- ✅ 80%+ of Pro users engage
- ✅ 95%+ citation accuracy
- ✅ 4.0/5.0+ user rating

---

## Business Goals (Year 1)

**By April 2027:**
- 50+ active paying clinics
- ৳2.5L+ MRR (Monthly Recurring Revenue)
- 70%+ retention rate
- <5% monthly churn

**Revenue Targets:**
- MVP Launch (Aug 2026): 10 clinics = ৳12,000/month
- End of Year 1 (Apr 2027): 50 clinics = ৳60,000/month
- Year 2 (Apr 2028): 300 clinics = ৳3,60,000/month

---

## Infrastructure Evolution

### Phase 1 (MVP)
- Single VPS (4 vCPU, 8GB RAM)
- Docker Compose
- PostgreSQL + Redis + MinIO
- **Cost:** ~$150-200/month
- **Capacity:** 50-200 users

### Phase 2-3 (Growth)
- Managed PostgreSQL (Neon/DigitalOcean)
- Managed Redis (Upstash)
- CDN (Cloudflare)
- **Cost:** ~$400-500/month
- **Capacity:** 500-1,000 users

### Phase 4 (Scale)
- Horizontal scaling (2+ API servers)
- Read replicas
- Celery workers by type
- **Cost:** ~$800-1,000/month
- **Capacity:** 2,000-5,000 users

---

## Team Scaling

### Phase 1 (MVP)
- 2-3 developers (Full-stack, Frontend)
- 1 part-time medical advisor

### Phase 2-3 (Growth)
- 4-5 developers
- 1 UI/UX designer
- 1 medical content curator
- 1 part-time DevOps

### Phase 4 (AI)
- 6-8 developers
- 1 ML/AI engineer
- 2 medical advisors
- 1 DevOps engineer

---

## Risk Management

### High Priority Risks
1. **Timeline slippage** - 14-week MVP is ambitious
   - Mitigation: Strict scope control, no feature creep

2. **Doctor adoption** - Need 10 pilots for validation
   - Mitigation: Early recruitment, strong onboarding

3. **Multi-tenant isolation** - Data security is critical
   - Mitigation: Rigorous testing, security audits

### Medium Priority Risks
1. **Payment integration delays** - SSLCommerz approval takes time
2. **Content licensing** - Book acquisition for Phase 3
3. **API cost overruns** - OpenAI costs in Phase 4

---

## Next Steps

**This Week:**
1. Build authentication module (register, login, 2FA)
2. Create seed data (geographic, providers)
3. Start patient CRUD endpoints

**This Month:**
1. Complete authentication & user management
2. Complete patient management
3. Begin prescription system

**This Quarter:**
1. Complete Phase 1 MVP
2. Launch with 10 pilot doctors
3. Gather feedback for Phase 2

---

**For detailed week-by-week breakdown:** [roadmap-detailed.md](roadmap-detailed.md)  
**For current status:** [../status/current.md](../status/current.md)  
**For task list:** [phase1-tasks.md](phase1-tasks.md)

---

**Last Updated:** April 21, 2026  
**Next Review:** Weekly (every Monday)  
**Maintained By:** Product & Engineering Team
