# AltCare Product Roadmap

> From MVP to comprehensive alternative medicine practice management platform

**Last updated:** April 2026  
**Current phase:** Phase 1 (Core Clinic MVP)  
**Target launch:** Q3 2026 (MVP) → Q2 2027 (Full Platform)

---

## Table of Contents

- [Vision & Goals](#vision--goals)
- [Phase Overview](#phase-overview)
- [Phase 1: Core Clinic MVP](#phase-1-core-clinic-mvp-current)
- [Phase 2: Knowledge Base](#phase-2-knowledge-base)
- [Phase 3: Book Library & Reader](#phase-3-book-library--reader)
- [Phase 4: AI/RAG Intelligence](#phase-4-airag-intelligence)
- [Phase 5: Patient Portal](#phase-5-patient-portal-future)
- [Infrastructure Evolution](#infrastructure-evolution)
- [Team Scaling](#team-scaling)
- [Risk Management](#risk-management)
- [Success Metrics](#success-metrics)

---

## Vision & Goals

### Mission Statement
Build the most comprehensive practice management system for alternative medicine practitioners in South Asia, combining modern technology with classical medical knowledge.

### Core Objectives
- **Practitioner-First:** Solve real clinic management pain points
- **Knowledge Integration:** Make classical texts accessible and searchable
- **Multi-System Support:** Serve Homeopathy, Ayurveda, Unani, and Herbal practitioners equally
- **Bangladesh Focus:** Local payment gateways, SMS providers, and cultural context
- **Scalable SaaS:** Multi-tenant architecture that can grow to thousands of clinics

### Success Definition
- **Year 1:** 50+ active paying clinics, ৳2.5L MRR
- **Year 2:** 300+ active paying clinics, ৳18L MRR
- **Year 3:** 1,000+ active paying clinics, ৳60L+ MRR, expand to India

---

## Phase Overview

| Phase | Focus | Duration | Target Launch | Status |
|-------|-------|----------|---------------|--------|
| **Phase 1** | Core Clinic MVP | 12 weeks | Q3 2026 | 🔄 In Progress |
| **Phase 2** | Knowledge Base | 8 weeks | Q4 2026 | 📋 Planned |
| **Phase 3** | Book Library | 10 weeks | Q1 2027 | 📋 Planned |
| **Phase 4** | AI/RAG | 12 weeks | Q2 2027 | 📋 Planned |
| **Phase 5** | Patient Portal | 8 weeks | Q3 2027 | 💡 Future |

**Total MVP to Full Platform:** ~50 weeks (~12 months)

---

## Phase 1: Core Clinic MVP `CURRENT`

**Timeline:** 12 weeks (April 2026 - June 2026)  
**Target Launch:** July 1, 2026  
**Goal:** Launch a working clinic management tool that 10 pilot doctors can use daily

### Week 1-2: Foundation
**Backend Setup**
- [x] FastAPI project structure with modular architecture
- [x] SQLAlchemy 2.0 async ORM setup
- [x] Alembic migration framework
- [x] Pydantic v2 models for validation
- [x] JWT authentication with passlib + python-jose
- [x] Multi-tenant middleware with ContextVar
- [ ] PostgreSQL 16 database setup with initial schema
- [ ] Redis cache configuration
- [ ] Celery worker setup for background tasks

**Frontend Setup**
- [ ] Next.js 14 with App Router
- [ ] Tailwind CSS + shadcn/ui components
- [ ] React Query for server state
- [ ] Axios interceptors with JWT refresh
- [ ] Responsive layout shell (sidebar, topbar, content)

**DevOps**
- [ ] Docker Compose for local development
- [ ] Environment variable management (.env.example)
- [ ] Git workflow (main, develop, feature branches)
- [ ] CI/CD pipeline setup (GitHub Actions)

### Week 3-4: Authentication & User Management
**Backend**
- [ ] User registration endpoint (`POST /api/v1/auth/register`)
- [ ] Admin approval workflow
- [ ] Login with JWT issuance (`POST /api/v1/auth/login`)
- [ ] Token refresh endpoint
- [ ] Password reset flow (email-based)
- [ ] Role-based access control (RBAC) dependencies
- [ ] Multi-specialization support in tenant model

**Frontend**
- [ ] Login page with form validation
- [ ] Registration page with specialization multi-select
- [ ] Forgot password flow
- [ ] Protected route wrapper
- [ ] User context provider
- [ ] Profile settings page

**Database**
- [x] `tenants` table with specializations array
- [x] `users` table with role enum
- [ ] Migration: Create initial tables
- [ ] Seed: Create platform admin user

### Week 5-6: Patient Management
**Backend**
- [ ] Patient CRUD endpoints
- [ ] Patient search with filters (name, phone, diagnosis)
- [ ] Patient tags system (special case, chronic, treatment, allergy)
- [ ] Patient diagnosis records
- [ ] Visit creation and management
- [ ] File upload for patient attachments (MinIO integration)
- [ ] Pagination and sorting

**Frontend**
- [ ] Patient list view with filters
- [ ] Patient detail slide-out panel
- [ ] Add/Edit patient form
- [ ] Tag management UI
- [ ] Visit history timeline
- [ ] Patient search autocomplete

**Database**
- [x] `patients` table
- [x] `patient_tags` table
- [x] `patient_diagnoses` table
- [x] `visits` table
- [ ] Indexes for search performance

### Week 7-8: Prescription System
**Backend**
- [ ] Prescription creation endpoint
- [ ] Prescription items management (medicines)
- [ ] Support for both DB medicines and free-text entries
- [ ] PDF generation with WeasyPrint (Celery task)
- [ ] Prescription history retrieval
- [ ] Prescription void/replacement logic

**Frontend**
- [ ] Prescription builder UI
- [ ] Medicine autocomplete (search existing + add custom)
- [ ] Dosage, frequency, duration inputs
- [ ] Live PDF preview
- [ ] Prescription history view
- [ ] Print/Download functionality

**Database**
- [x] `prescriptions` table with status enum
- [x] `prescription_items` table with nullable medicine_id
- [ ] Migration: Add prescription tables

### Week 9: Payment & Invoicing
**Backend**
- [ ] Payment recording endpoint
- [ ] Invoice generation (PDF via WeasyPrint)
- [ ] Payment method support (cash, bKash, Nagad, card)
- [ ] Revenue reports (daily, monthly aggregates)
- [ ] Payment status tracking

**Frontend**
- [ ] Payment recording form
- [ ] Invoice list view
- [ ] Revenue dashboard widgets
- [ ] Payment status badges
- [ ] Invoice PDF download

**Database**
- [x] `payments` table with payment_method enum
- [x] `invoices` table
- [ ] Indexes for revenue aggregation

### Week 10: Dashboard & Analytics
**Backend**
- [ ] Dashboard KPI endpoints (patients, visits, revenue)
- [ ] Calendar data aggregation (patient load per day)
- [ ] Top diagnoses chart data
- [ ] Top medicines chart data
- [ ] Growth metrics (month-over-month)

**Frontend**
- [ ] Dashboard with KPI cards
- [ ] Patient calendar with heatmap
- [ ] Bar charts for diagnoses and medicines
- [ ] Recent patients table
- [ ] Upcoming follow-ups widget

**Database**
- [ ] Optimized queries for dashboard aggregations
- [ ] Partial indexes for performance

### Week 11: Integration Framework (Bonus)
**Backend**
- [ ] Integration provider catalog seeding
- [ ] Tenant integration configuration
- [ ] Credentials encryption (Fernet)
- [ ] Test transaction endpoints (SMS, Email, Payment)
- [ ] Integration logs table population

**Frontend**
- [ ] Integration provider selection UI
- [ ] Credentials configuration forms
- [ ] Test integration buttons
- [ ] Integration logs viewer

**Database**
- [x] `integration_providers` table (seeded)
- [x] `tenant_integrations` table
- [x] `integration_logs` table

### Week 12: Testing, Polish & Launch Prep
**Testing**
- [ ] Unit tests for core business logic (80% coverage)
- [ ] Integration tests for API endpoints
- [ ] E2E tests with Playwright (critical flows)
- [ ] Load testing with Locust (100 concurrent users)
- [ ] Security audit (OWASP top 10)

**Polish**
- [ ] Error handling and user feedback
- [ ] Loading states and skeletons
- [ ] Empty states with CTAs
- [ ] Mobile responsiveness fixes
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Performance optimization (Lighthouse > 90)

**Documentation**
- [ ] API documentation (auto-generated via FastAPI)
- [ ] User guide (help center)
- [ ] Video tutorials (3-5 mins each)
- [ ] Deployment guide for production

**Launch Prep**
- [ ] Beta testing with 5 pilot doctors (2 weeks)
- [ ] Bug fixes from beta feedback
- [ ] Production deployment to VPS
- [ ] SSL certificate setup (Caddy auto-HTTPS)
- [ ] Domain configuration (altcare.health)
- [ ] Monitoring setup (Sentry, Uptime monitoring)

### Phase 1 Deliverables

✅ **Functional MVP** that includes:
- Doctor registration with admin approval
- Multi-specialization support (1-4 systems)
- Patient management with visit history and tagging
- Prescription builder with PDF export
- Payment tracking and invoice generation
- Dashboard with KPIs and analytics
- Integration framework for SMS/Email/Payment

✅ **Technical Foundation:**
- Multi-tenant architecture (row-level isolation)
- Role-based access control (Admin, Operator, Doctor, Receptionist)
- Async backend with Celery for background jobs
- Responsive frontend with React/Next.js
- Docker Compose for deployment
- Automated backups and monitoring

✅ **Go-to-Market:**
- 10 pilot doctors onboarded
- User feedback collected
- Pricing validated (Free/Plus/Pro tiers)
- Marketing website live
- Payment gateway integrated (bKash)

---

## Phase 2: Knowledge Base

**Timeline:** 8 weeks (July - August 2026)  
**Goal:** Add medicine database with symptom-based search to help doctors during consultations

### Week 1-2: Medicine Database Foundation
**Backend**
- [ ] Global medicine CRUD endpoints (admin only)
- [ ] Tenant-specific medicine additions
- [ ] Medicine search with filters (system, category, potency)
- [ ] Full-text search optimization (tsvector)
- [ ] Specialization-based filtering
- [ ] Import bulk medicines from CSV/Excel

**Frontend**
- [ ] Medicine search UI with autocomplete
- [ ] Medicine detail view
- [ ] Add/Edit medicine forms (admin)
- [ ] Filtering by system, category
- [ ] Bulk import interface

**Database**
- [x] `medicines` table with is_global flag
- [ ] Migration: Add medicines table
- [ ] Seed: Import 500+ common medicines (Homeopathy, Ayurveda, Unani, Herbal)

### Week 3-4: Symptom Mapping
**Backend**
- [ ] Symptom-to-medicine mapping CRUD
- [ ] Symptom search algorithm (weighted matching)
- [ ] Match strength calculation
- [ ] Modality notes support
- [ ] Symptom tag management

**Frontend**
- [ ] Symptom search page
- [ ] Multi-symptom input with autocomplete
- [ ] Match results with percentage scores
- [ ] Grouped by medical system
- [ ] Quick add to prescription from search results

**Database**
- [x] `medicine_symptoms` table with match_strength
- [ ] GIN indexes for symptom search
- [ ] Seed: Add symptom mappings (1000+ entries)

### Week 5-6: Integration with Prescription Builder
**Backend**
- [ ] Medicine quick search in prescription endpoint
- [ ] Recently used medicines tracking
- [ ] Commonly prescribed medicines analytics
- [ ] Dosage guidance retrieval

**Frontend**
- [ ] Enhanced prescription builder with medicine search
- [ ] Auto-complete with symptom hints
- [ ] Dosage suggestions from database
- [ ] Recently used medicines quick-select
- [ ] Contraindications warnings

### Week 7-8: Content Curation & Testing
**Content**
- [ ] Partner with medical practitioners for validation
- [ ] Curate 1,000+ medicines across all four systems
- [ ] Add symptom mappings with practitioner review
- [ ] Add dosage guidelines
- [ ] Validate contraindications and interactions

**Testing**
- [ ] User acceptance testing with 10 doctors
- [ ] Symptom search accuracy validation
- [ ] Performance testing (search latency < 100ms)
- [ ] Mobile experience testing

### Phase 2 Deliverables

✅ **Medicine Database:**
- 1,000+ curated medicines (global pool)
- Filterable by specialization
- Full-text search optimized
- Bulk import capability

✅ **Symptom Search:**
- Multi-symptom input support
- Weighted matching algorithm
- Results grouped by medical system
- Match percentage scoring

✅ **Enhanced Prescription Builder:**
- One-click add from symptom search
- Dosage auto-suggestions
- Recently used medicines
- Contraindications warnings

---

## Phase 3: Book Library & Reader

**Timeline:** 10 weeks (September - November 2026)  
**Goal:** Give doctors access to classical medical texts within the platform

### Week 1-2: EPUB Upload & Storage
**Backend**
- [ ] EPUB file upload endpoint (multipart/form-data)
- [ ] MinIO integration for file storage
- [ ] File validation (format, size limits)
- [ ] Book metadata extraction
- [ ] Global vs tenant-specific books

**Frontend**
- [ ] Book upload UI with drag-and-drop
- [ ] Upload progress indicator
- [ ] Book metadata form (title, author, system)
- [ ] Book library grid view

**Database**
- [x] `books` table with epub_url and is_global
- [ ] MinIO bucket setup

### Week 2-4: EPUB Parsing
**Backend**
- [ ] EPUB parsing with ebooklib (Celery task)
- [ ] Chapter extraction
- [ ] Section parsing with heading detection
- [ ] Content cleaning (HTML to plain text)
- [ ] Word count calculation
- [ ] Parsing error handling and retry logic

**Database**
- [x] `chapters` table
- [x] `sections` table
- [ ] Migration: Add book-related tables
- [ ] Indexes for chapter/section navigation

### Week 5-7: Book Reader
**Frontend**
- [ ] Book reader UI with table of contents
- [ ] Chapter navigation (prev/next)
- [ ] Section rendering with typography
- [ ] Reading progress tracking (% completed)
- [ ] Scroll position persistence
- [ ] Font size and theme controls
- [ ] Search within book

**Backend**
- [ ] Reading progress update endpoint
- [ ] Bookmark CRUD endpoints
- [ ] Highlight CRUD endpoints
- [ ] Chapter content retrieval (paginated)

**Database**
- [x] `reading_progress` table
- [x] `bookmarks` table
- [x] `highlights` table

### Week 8-9: Content Curation
**Content**
- [ ] Partner with publishers for legal access
- [ ] Digitize/acquire 20+ classical texts:
  - **Homeopathy:** Organon of Medicine, Materia Medica, Repertory
  - **Ayurveda:** Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya
  - **Unani:** Al-Qanun fi al-Tibb (Canon of Medicine), Kamil al-Sana'a
  - **Herbal:** PDR for Herbal Medicines, Chinese Herbal Medicine
- [ ] Parse all books (validate chapter/section structure)
- [ ] Quality check (ensure readability)

### Week 10: Testing & Polish
**Testing**
- [ ] Reader performance testing (large books > 1000 pages)
- [ ] Bookmark/highlight sync testing
- [ ] Mobile reader experience
- [ ] Progress tracking accuracy

**Polish**
- [ ] Smooth scrolling and navigation
- [ ] Typography optimization (readability)
- [ ] Dark mode support
- [ ] Keyboard shortcuts

### Phase 3 Deliverables

✅ **Book Library:**
- 20+ classical medical texts
- Filterable by system and author
- Upload capability for doctors (Pro plan)
- Cover images and metadata

✅ **Book Reader:**
- Clean, readable interface
- Table of contents navigation
- Reading progress tracking
- Bookmarks and highlights
- Search within book

✅ **Dashboard Integration:**
- Currently reading widget
- Reading progress visualization
- Recently accessed books

---

## Phase 4: AI/RAG Intelligence

**Timeline:** 12 weeks (December 2026 - February 2027)  
**Goal:** Add AI-powered clinical reference assistant grounded in classical texts

### Week 1-3: Embedding Pipeline
**Backend**
- [ ] OpenAI API integration (text-embedding-3-small)
- [ ] LangChain setup for document processing
- [ ] Chunking strategy (800 tokens, 100 token overlap)
- [ ] Batch embedding generation (Celery task)
- [ ] pgvector extension setup
- [ ] Embedding storage and indexing
- [ ] Re-embedding on book updates

**Database**
- [x] `embeddings` table with vector(1536)
- [ ] HNSW index for vector similarity search
- [ ] Migration: Add pgvector extension

**Processing**
- [ ] Embed all existing books (~20 books → ~50K sections)
- [ ] Validate embedding quality
- [ ] Performance testing (retrieval latency)

### Week 4-6: RAG Retrieval System
**Backend**
- [ ] Vector similarity search implementation
- [ ] Top-k retrieval with cosine similarity
- [ ] Metadata filtering (by medical system)
- [ ] Context window assembly
- [ ] Prompt engineering for clinical queries
- [ ] OpenAI GPT-4o integration
- [ ] Response formatting with citations

**API**
- [ ] AI query endpoint (`POST /api/v1/ai/query`)
- [ ] Streaming response support (SSE)
- [ ] Usage tracking per tenant
- [ ] Rate limiting (200 queries/month for Pro)

### Week 7-8: AI Assistant UI
**Frontend**
- [ ] Chat interface (message bubbles)
- [ ] Quick prompt buttons (common queries)
- [ ] Streaming response rendering
- [ ] Source citations display (book, chapter, section)
- [ ] Copy response button
- [ ] Query history
- [ ] Clinical disclaimer banner

**UX**
- [ ] Professional medical tone
- [ ] Clear citation format
- [ ] Loading states
- [ ] Error handling (quota exceeded, API errors)

### Week 9-10: Guardrails & Safety
**System Prompts**
- [ ] Explicit instruction: "Never make prescriptive medical decisions"
- [ ] Grounding requirement: "Answer only from provided sources"
- [ ] Citation requirement: "Always cite book title and section"
- [ ] Uncertainty handling: "If answer not in sources, say so"

**Content Filtering**
- [ ] Block inappropriate queries
- [ ] Flag potentially harmful advice
- [ ] Human review queue for flagged responses

**Testing**
- [ ] Red teaming (try to get harmful responses)
- [ ] Accuracy validation (compare responses with source texts)
- [ ] Hallucination detection
- [ ] Citation accuracy verification

### Week 11-12: Analytics & Optimization
**Analytics**
- [ ] Query intent classification
- [ ] Popular queries dashboard
- [ ] Response quality metrics (user feedback)
- [ ] Source coverage analysis (which books used most)
- [ ] Token usage tracking (cost monitoring)

**Optimization**
- [ ] Caching for common queries
- [ ] Embedding dimensionality reduction testing
- [ ] Retrieval accuracy tuning (k value, similarity threshold)
- [ ] Prompt optimization for better responses
- [ ] Cost optimization (batch processing, caching)

### Phase 4 Deliverables

✅ **AI Assistant:**
- Chat interface with streaming responses
- Grounded in 20+ classical texts
- Citations for every answer
- 200 queries/month for Pro plan

✅ **Embedding System:**
- 50K+ embedded text sections
- Sub-second vector retrieval
- Filtered by doctor's specializations
- Automated re-embedding on content updates

✅ **Safety:**
- Clinical disclaimer on every response
- Guardrails against prescriptive advice
- Hallucination detection
- Human review for flagged queries

✅ **Analytics:**
- Query usage tracking
- Popular topics dashboard
- Response quality metrics
- Cost monitoring

---

## Phase 5: Patient Portal `FUTURE`

**Timeline:** 8 weeks (Q3 2027)  
**Goal:** Give patients access to their prescriptions, visit history, and educational content

### Scope
**Patient Features:**
- [ ] Patient login (email/phone OTP)
- [ ] View prescription history with PDFs
- [ ] View visit history and notes
- [ ] View upcoming appointments
- [ ] Educational content library
- [ ] Appointment booking (request)
- [ ] Feedback and ratings

**Doctor Features:**
- [ ] Patient portal toggle (enable/disable)
- [ ] Control what patients can see
- [ ] Educational content curation
- [ ] Appointment approval workflow

**Technical:**
- [ ] Patient user type in database
- [ ] OTP-based authentication (SMS/Email)
- [ ] Patient-scoped data access
- [ ] Responsive mobile-first design
- [ ] PWA (installable on phone)

---

## Infrastructure Evolution

### Phase 1: Single VPS
**Specs:** 4 vCPU, 8 GB RAM, 80 GB SSD  
**Cost:** $25/month (Hetzner)  
**Capacity:** 50-200 concurrent users

**Services:**
- Caddy (reverse proxy + auto HTTPS)
- FastAPI (4 Uvicorn workers)
- Celery worker (1 instance)
- PostgreSQL 16
- Redis
- MinIO (local S3)

### Phase 2-3: Managed Services
**Database:** Migrate to managed PostgreSQL (Neon, Supabase, or DigitalOcean Managed DB)  
**Cache:** Migrate to managed Redis (Upstash, Redis Cloud)  
**Storage:** Migrate to Cloudflare R2 or AWS S3  
**Cost:** ~$80/month  
**Capacity:** 500-1000 concurrent users

### Phase 4: Horizontal Scaling
**API:** Add 2nd API container behind load balancer  
**Workers:** 3 Celery workers (PDF, Email, Embeddings)  
**Database:** Read replicas for analytics queries  
**CDN:** Cloudflare for static assets  
**Cost:** ~$200/month  
**Capacity:** 2000-5000 concurrent users

### Phase 5: Multi-Region (Future)
**Regions:** Bangladesh (primary), India (secondary)  
**Database:** Multi-region replication  
**CDN:** Edge caching globally  
**Cost:** $500+/month  
**Capacity:** 10,000+ concurrent users

---

## Team Scaling

### Phase 1 (MVP)
**Team:** 2-3 people
- 1 Full-stack developer (Python + React)
- 1 Designer/Frontend developer
- 1 Part-time medical advisor (practitioner)

### Phase 2-3
**Team:** 4-5 people
- 2 Backend developers (Python/FastAPI)
- 1 Frontend developer (React/Next.js)
- 1 Designer (UI/UX)
- 1 Medical content curator (full-time)
- 1 Part-time DevOps

### Phase 4
**Team:** 6-8 people
- 2 Backend developers
- 2 Frontend developers
- 1 ML/AI engineer (RAG optimization)
- 1 Designer
- 1 Medical content team (2 people)
- 1 DevOps engineer

### Phase 5+
**Team:** 10-15 people
- 3 Backend developers
- 3 Frontend developers
- 1 ML engineer
- 2 Designers (UI/UX, Product)
- 1 QA engineer
- 2 Medical content team
- 1 DevOps engineer
- 1 Product manager
- 1 Customer success manager

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database performance degradation with growth | High | Implement read replicas, query optimization, caching strategy |
| EPUB parsing failures | Medium | Robust error handling, manual fallback, partner with publishers |
| AI hallucinations | High | Strict grounding, citation requirements, human review, clear disclaimers |
| Integration API downtime (bKash, SMS) | Medium | Fallback providers, queue retry logic, status monitoring |
| Data loss | Critical | Daily automated backups, point-in-time recovery, quarterly restore testing |

### Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low doctor adoption | Critical | Pilot program with 10 doctors, iterate on feedback, strong onboarding |
| Competition from existing EMR systems | High | Focus on alternative medicine niche, AI differentiator, Bangladesh-first approach |
| Payment gateway issues in Bangladesh | Medium | Multiple gateway options (bKash, Nagad, Rocket), cash fallback |
| Content licensing for books | Medium | Partner with publishers early, offer revenue share, focus on public domain initially |
| Regulatory compliance (medical data) | High | HIPAA-like standards, encryption at rest/transit, regular audits |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Key person dependency | High | Documentation, code reviews, knowledge sharing sessions |
| Scope creep | Medium | Strict phase-based development, feature freeze windows |
| Budget overrun | Medium | Conservative estimates, 20% buffer, monthly budget reviews |

---

## Success Metrics

### Phase 1 (MVP)
- [ ] 10 pilot doctors onboarded and actively using daily
- [ ] 500+ patients managed in system
- [ ] 200+ prescriptions generated
- [ ] 95%+ uptime
- [ ] <1s average page load time
- [ ] 80%+ user satisfaction (NPS > 40)

### Phase 2 (Knowledge Base)
- [ ] 1,000+ medicines in database
- [ ] Symptom search used by 80%+ of active doctors
- [ ] 30%+ of prescriptions use symptom search workflow
- [ ] Search accuracy > 85% (validated by practitioners)

### Phase 3 (Library)
- [ ] 20+ books parsed and accessible
- [ ] 50%+ of doctors use library feature monthly
- [ ] Average reading session > 10 minutes
- [ ] 100+ bookmarks created

### Phase 4 (AI)
- [ ] 80%+ of Pro plan doctors use AI assistant
- [ ] Average 15 queries per doctor per month
- [ ] Response citation accuracy > 95%
- [ ] Zero prescriptive medical advice violations

### Overall (End of Year 1)
- [ ] 50+ paying clinics (target met)
- [ ] ৳2.5L+ MRR (Monthly Recurring Revenue)
- [ ] 70% retention rate (doctors stay subscribed)
- [ ] 40%+ upgrade rate (Free → Plus or Plus → Pro)
- [ ] <5% churn rate monthly

---

## Go-to-Market Strategy

### Pre-Launch (Weeks before Phase 1 launch)
- [ ] Create marketing website (landing page)
- [ ] Publish 5 blog posts on alternative medicine digitization
- [ ] Partner with 3 alternative medicine associations in Bangladesh
- [ ] Create demo video (3 minutes)
- [ ] Social media presence (Facebook, LinkedIn)

### Launch (Phase 1)
- [ ] Press release to healthcare tech media
- [ ] Product Hunt launch
- [ ] Free trial for first 50 doctors (90 days)
- [ ] Webinar series: "Digitizing Your Alternative Medicine Practice"
- [ ] Email campaign to 500+ practitioners (purchased list)

### Growth (Phase 2-3)
- [ ] Referral program (1 month free for both referrer and referee)
- [ ] Content marketing (2 blog posts per week)
- [ ] SEO optimization (rank for "homeopathy software bangladesh")
- [ ] Facebook ads targeting doctors in Dhaka
- [ ] Partnership with medical colleges

### Scale (Phase 4+)
- [ ] Expand to India (localization)
- [ ] Partnerships with pharmacy chains
- [ ] White-label offering for large clinics
- [ ] Mobile app (iOS + Android)
- [ ] Annual conference for users

---

## Technology Roadmap

### Immediate (Phase 1-2)
- Python 3.12, FastAPI, SQLAlchemy 2.0
- PostgreSQL 16, Redis, MinIO
- Next.js 14, React Query, Tailwind CSS
- Docker Compose deployment

### Near-term (Phase 3-4)
- Add pgvector for embeddings
- LangChain for RAG pipeline
- OpenAI API (embeddings + GPT-4o)
- Kubernetes for orchestration (if scaling needed)

### Future (Phase 5+)
- GraphQL API (in addition to REST)
- React Native mobile app
- Real-time collaboration (WebSockets)
- Advanced analytics (BigQuery or ClickHouse)
- Machine learning for prescription recommendations
- Blockchain for prescription verification (explore)

---

## Pricing Evolution

### Phase 1 Launch Pricing
- **Free:** 30 patients, 10 prescriptions/month
- **Plus:** ৳799/month (500 patients, unlimited prescriptions, PDF export)
- **Pro:** ৳1,799/month (unlimited patients, AI assistant, 1 receptionist seat)

### Phase 2-3 Pricing (Knowledge Base + Library)
- **Free:** Unchanged
- **Plus:** ৳899/month (+100, adds medicine DB + 5 books)
- **Pro:** ৳1,999/month (+200, adds unlimited books + AI assistant)

### Phase 4+ Pricing (Full Platform)
- **Free:** Unchanged (acquisition tool)
- **Plus:** ৳999/month
- **Pro:** ৳2,299/month
- **Enterprise:** Custom (10+ doctors, dedicated support, SLA)

### Annual Discount
- 20% off all plans when billed annually

---

## Dependencies & Blockers

### Critical Dependencies
- ✅ UI mockups completed (Admin + Doctor views)
- ✅ Database schema designed (24 tables)
- ⏳ Beta doctor recruitment (target: 10 doctors)
- ⏳ bKash merchant account approval (2-3 weeks)
- ⏳ Content licensing agreements (for books)
- ⏳ OpenAI API key and budget allocation

### Potential Blockers
- Medical content validation (need practitioner partnerships)
- EPUB book acquisition (public domain vs licensed)
- Payment gateway integration delays
- AI model API rate limits or cost overruns
- Regulatory compliance requirements (if any)

---

## Conclusion

This roadmap represents a **12-month journey** from MVP to a comprehensive AI-powered alternative medicine practice management platform. The phased approach allows us to:

1. **Validate early** with a working MVP (Phase 1)
2. **Add value incrementally** (Phases 2-4)
3. **Scale sustainably** with proven product-market fit
4. **Maintain focus** through clear milestones and deliverables

**Next Steps:**
1. Complete Phase 1 backend foundation (Weeks 1-2)
2. Recruit 10 beta doctors for pilot program
3. Begin daily standups and weekly sprint planning
4. Set up monitoring and alerting
5. Launch Phase 1 MVP by July 1, 2026

**Success requires:**
- Strong execution on technical milestones
- Close collaboration with medical practitioners
- Rapid iteration based on user feedback
- Disciplined scope management
- Sustainable team culture

---

**Document Owner:** Product Team  
**Last Review:** April 16, 2026  
**Next Review:** June 1, 2026 (Pre-launch)

**Questions or feedback?** Contact the product team or open an issue in the repository.
