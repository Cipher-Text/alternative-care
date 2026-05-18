# AltCare Development Roadmap

**Project:** Alternative Medicine Practice Management System  
**Timeline:** May 2026 - March 2027 (11 months)  
**Current Status:** Phase 1, Week 12 of 14 (86% complete)  
**Last Updated:** May 1, 2026

---

## Overview

AltCare is being developed in 4 phases over 11 months, with each phase building on the previous. The roadmap follows an agile approach with 2-week sprints and regular milestone reviews.

**Development Philosophy:**
- ✅ Build core features first, add advanced features later
- ✅ Test-driven development (TDD) with 80%+ coverage
- ✅ Continuous deployment to staging environment
- ✅ User feedback incorporated every 2 weeks
- ✅ Multi-tenant architecture from day one

---

## Timeline At-a-Glance

```
May 2026          Jun 2026          Jul 2026          Aug-Oct 2026      Nov 2026-Mar 2027
│                 │                 │                 │                 │
├─ Phase 1 ───────────────────────┤                 │                 │
│  Backend MVP                    │                 │                 │
│  (14 weeks)                     │                 │                 │
│                                 │                 │                 │
│                                 ├─ Phase 2 ────────────────────┤     │
│                                 │  Knowledge Base              │     │
│                                 │  (12 weeks)                  │     │
│                                 │                              │     │
│                                 │                              ├─ Phase 3 ──────┤
│                                 │                              │  Medical Library│
│                                 │                              │  (12 weeks)     │
│                                 │                              │                 │
│                                 │                              │                 ├─ Phase 4 ──┤
│                                 │                              │                 │  AI/RAG    │
│                                 │                              │                 │  (8 weeks) │
└─────────────────────────────────┴──────────────────────────────┴─────────────────┴────────────┘
Week 1           Week 6           Week 14          Week 26               Week 38         Week 46
```

---

## Phase 1: Core Clinic MVP (14 weeks)
**Timeline:** May 1 - August 1, 2026  
**Status:** 86% Complete (Week 12/14)  
**Goal:** Production-ready backend for essential clinic operations

### ✅ Completed (Weeks 1-12)

#### Week 1-2: Backend Foundation ✅
**Status:** 100% Complete | **Completed:** May 15, 2026

**Deliverables:**
- [x] Database schema (30 tables)
- [x] PostgreSQL 16 + pgvector setup
- [x] Docker infrastructure (PostgreSQL, Redis, MinIO)
- [x] Alembic migrations
- [x] Multi-tenant architecture (row-level isolation)
- [x] Base models and schemas
- [x] FastAPI application structure
- [x] Development environment setup

**Metrics:**
- 30 database tables
- 100% migration coverage
- Docker compose with 3 services

---

#### Week 3-4: Authentication & User Management ✅
**Status:** 100% Complete | **Completed:** May 29, 2026

**Deliverables:**
- [x] User registration with tenant creation
- [x] JWT access + refresh tokens
- [x] TOTP-based 2FA with QR codes
- [x] Session management
- [x] Password change
- [x] Role-based access control (RBAC)
- [x] Plan-based feature gating
- [x] 9 API endpoints
- [x] 45+ tests (85% coverage)

**Metrics:**
- 9 endpoints
- 45 tests
- 85% test coverage
- JWT + 2FA fully functional

---

#### Week 5-6: Doctor Profile & Credentials ✅
**Status:** 100% Complete | **Completed:** June 12, 2026

**Deliverables:**
- [x] Doctor profile management
- [x] Medical degrees (CRUD)
- [x] Professional trainings (CRUD)
- [x] Document verification workflow
- [x] 12 API endpoints
- [x] 30+ tests (82% coverage)

**Metrics:**
- 12 endpoints
- 30 tests
- 82% test coverage
- Verification workflow operational

---

#### Week 7-8: Patient Management ✅
**Status:** 100% Complete | **Completed:** June 26, 2026

**Deliverables:**
- [x] Patient CRUD operations
- [x] Patient search functionality
- [x] Patient tags for categorization
- [x] Patient diagnoses tracking
- [x] Visit history integration
- [x] 14 API endpoints
- [x] 28+ tests (79% coverage)

**Metrics:**
- 14 endpoints
- 28 tests
- 79% test coverage
- Search functionality working

---

#### Bonus Week: Appointments & Visits ✅
**Status:** 100% Complete | **Completed:** July 3, 2026

**Deliverables:**
- [x] Appointment booking system
- [x] Time slot conflict detection
- [x] Multiple appointment statuses
- [x] Visit records (linked & standalone)
- [x] Clinical information tracking
- [x] Vitals recording
- [x] 10 API endpoints (6 appointments + 4 visits)
- [x] 22+ tests (74% coverage)

**Metrics:**
- 10 endpoints
- 22 tests
- 74% test coverage
- Conflict detection working

---

#### Week 9-10: Prescription System ✅
**Status:** 100% Complete | **Completed:** July 17, 2026

**Deliverables:**
- [x] Prescription builder
- [x] Immutable workflow (draft → issued → voided)
- [x] Support for database medicines + free-text
- [x] PDF generation ready
- [x] Prescription items management
- [x] Comprehensive validation
- [x] 8 API endpoints
- [x] 36 tests (98% coverage)

**Metrics:**
- 8 endpoints
- 36 tests
- 98% test coverage (highest!)
- Immutability enforced

---

#### Week 11: Payment & Invoicing ✅
**Status:** 100% Complete | **Completed:** July 24, 2026

**Deliverables:**
- [x] Manual cash payments
- [x] bKash Payment Gateway v1.2.0-beta integration
- [x] OAuth token management with auto-refresh
- [x] Auto-generated invoices (INV-YYYYMM-NNNN)
- [x] Payment filtering and summaries
- [x] Invoice PDF generation (placeholder)
- [x] 12 API endpoints
- [x] 70+ tests (87% coverage)

**Metrics:**
- 12 endpoints
- 70 tests
- 87% test coverage
- bKash integration working

---

#### Week 12: Dashboard & Analytics ✅
**Status:** 100% Complete | **Completed:** May 1, 2026

**Deliverables:**
- [x] Real-time analytics across all modules
- [x] Financial metrics with revenue breakdowns
- [x] Patient demographics and trends
- [x] Appointment booking analytics
- [x] Visit patterns and chief complaints
- [x] Prescription medication trends
- [x] Date range filtering
- [x] 6 API endpoints
- [x] 21 tests (92% coverage)

**Metrics:**
- 6 endpoints
- 21 tests
- 92% test coverage
- Real-time analytics operational

---

### 🔄 In Progress (Week 13)

#### Week 13: Integration Framework
**Timeline:** May 1-8, 2026  
**Status:** 0% Complete | **Next**

**Goals:**
- Unified integration provider framework
- SMS provider configuration
- Email provider setup
- Provider status monitoring
- Integration logs and debugging
- Test mode vs production mode
- Credential encryption

**Planned Deliverables:**
- [ ] Integration provider catalog (global)
- [ ] Tenant integration configs (encrypted credentials)
- [ ] SMS providers: Twilio, Banglalink, Robi, GP
- [ ] Email providers: SendGrid, AWS SES, Mailgun
- [ ] Integration logs with request/response tracking
- [ ] Provider health monitoring
- [ ] 10+ API endpoints
- [ ] Test coverage 80%+

**Success Metrics:**
- Send test SMS via any provider
- Send test email via any provider
- Provider switching without code changes
- All credentials encrypted with Fernet
- Complete audit trail of all API calls

---

### 📋 Planned (Week 14)

#### Week 14: Testing & Production Launch
**Timeline:** May 8-15, 2026  
**Status:** Planned

**Goals:**
- End-to-end integration testing
- Performance optimization
- Security audit
- Production deployment
- Monitoring and alerting

**Planned Deliverables:**
- [ ] E2E test suite (critical user flows)
- [ ] Performance benchmarks (response times, throughput)
- [ ] Security scan (OWASP Top 10)
- [ ] Production deployment scripts
- [ ] Monitoring setup (Prometheus + Grafana)
- [ ] Alerting rules
- [ ] Backup and recovery procedures
- [ ] Final documentation review

**Launch Checklist:**
- [ ] All 71+ endpoints tested
- [ ] 80%+ test coverage achieved
- [ ] No critical security vulnerabilities
- [ ] Performance targets met (< 200ms p95)
- [ ] Monitoring and alerts operational
- [ ] Backup strategy validated
- [ ] Documentation complete
- [ ] Production database migrated
- [ ] SSL certificates configured
- [ ] Domain DNS configured

**Success Metrics:**
- Backend deployed to production
- 99.9% uptime target set
- Automated backups running
- Monitoring dashboards live
- Zero critical bugs

---

## Phase 1 Summary

**Duration:** 14 weeks (May 1 - August 1, 2026)  
**Status:** 86% Complete (12/14 weeks done)  
**Target Launch:** August 1, 2026

### Phase 1 Achievements ✅

**Backend:**
- ✅ 7 modules fully functional
- ✅ 71 API endpoints live
- ✅ 252 automated tests
- ✅ 83% overall test coverage
- ✅ Multi-tenant architecture proven
- ✅ bKash payment integration
- ✅ Real-time analytics

**Infrastructure:**
- ✅ Docker development environment
- ✅ PostgreSQL 16 + pgvector
- ✅ Redis caching layer
- ✅ MinIO object storage
- ✅ Automated migrations

**Quality:**
- ✅ 83% test coverage
- ✅ Zero critical bugs
- ✅ Clean code (Black, Ruff, MyPy)
- ✅ Comprehensive documentation

### Phase 1 Gaps

**Features:**
- ⏳ Integration framework (Week 13)
- ⏳ Production deployment (Week 14)
- 📋 Email verification (deferred)
- 📋 Password reset via email (deferred)
- 📋 Invoice PDF generation (placeholder)
- 📋 Prescription PDF generation (placeholder)

**Technical:**
- Test database compatibility issues (bcrypt)
- Some integration tests need infrastructure fixes
- PDF generation needs implementation

---

## Phase 2: Knowledge Base (12 weeks)
**Timeline:** August 1 - October 24, 2026  
**Status:** Planned  
**Goal:** Medicine database and symptom-based search

### Planned Features

#### Week 15-16: Medicine Database
- Import medicine catalog (Homeopathy, Ayurveda, Unani, Herbal)
- Medicine search and filtering
- Bilingual support (English/Bengali)
- Medicine aliases and alternative names
- Dosage guidelines
- Contraindications
- 8-10 API endpoints

#### Week 17-18: Symptom Database
- Symptom catalog with hierarchies
- Symptom-medicine mappings
- Modality tracking (better/worse conditions)
- Symptom search
- Bilingual symptom names
- 6-8 API endpoints

#### Week 19-20: Repertory System
- Symptom repertorization
- Rubric-based search
- Medicine ranking by symptom match
- Case taking interface
- Repertory builder
- 8-10 API endpoints

#### Week 21-22: Materia Medica
- Detailed medicine profiles
- Proving information
- Clinical indications
- Personality profiles (for Homeopathy)
- Cross-references
- 6-8 API endpoints

#### Week 23-24: Advanced Search
- Multi-symptom search
- Differential diagnosis
- Treatment protocols
- Case history templates
- Search history
- 6-8 API endpoints

#### Week 25-26: Knowledge Testing & Polish
- E2E testing of knowledge base
- Performance optimization
- Search relevance tuning
- Documentation
- Beta testing with doctors

### Phase 2 Success Metrics
- 10,000+ medicines cataloged
- 5,000+ symptoms mapped
- Search results in < 100ms
- 90%+ doctor satisfaction with search
- Bilingual content complete

---

## Phase 3: Medical Library (12 weeks)
**Timeline:** October 24, 2026 - January 16, 2027  
**Status:** Planned  
**Goal:** EPUB medical book library with reading features

### Planned Features

#### Week 27-28: Book Management
- Book catalog (EPUB format)
- Book upload and parsing
- Chapter/section extraction
- Metadata management
- Access control
- 8-10 API endpoints

#### Week 29-30: Reading Interface
- EPUB reader integration
- Reading position tracking
- Page bookmarks
- Text highlighting
- Notes and annotations
- 10-12 API endpoints

#### Week 31-32: Search & Discovery
- Full-text search across books
- Table of contents navigation
- Search within book
- Related content suggestions
- Reading recommendations
- 6-8 API endpoints

#### Week 33-34: Vector Embeddings
- Generate embeddings for all content
- pgvector integration
- Semantic search preparation
- Embedding pipeline
- Vector indexing
- 4-6 API endpoints

#### Week 35-36: Advanced Features
- Reading statistics
- Study mode
- Offline support
- PDF export
- Sharing and collaboration
- 8-10 API endpoints

#### Week 37-38: Library Testing & Polish
- E2E testing
- Performance optimization
- Mobile reading experience
- Documentation
- Content migration

### Phase 3 Success Metrics
- 1,000+ medical books available
- Vector embeddings for all content
- Reading position synced across devices
- < 50ms search latency
- 85%+ doctor engagement

---

## Phase 4: AI/RAG Clinical Assistant (8 weeks)
**Timeline:** January 16 - March 13, 2027  
**Status:** Planned  
**Goal:** AI-powered clinical reference assistant using RAG

### Planned Features

#### Week 39-40: RAG Foundation
- LangChain integration
- OpenAI API setup
- Vector search implementation
- Context retrieval from library
- Prompt engineering
- 4-6 API endpoints

#### Week 41-42: Clinical Assistant
- Natural language queries
- Case analysis
- Medicine recommendations
- Differential diagnosis support
- Treatment protocol suggestions
- 6-8 API endpoints

#### Week 43-44: AI Enhancement
- Fine-tuning on medical data
- Multi-turn conversations
- Chat history
- Confidence scoring
- Source attribution
- 6-8 API endpoints

#### Week 45-46: AI Testing & Production
- Accuracy validation with doctors
- Safety guardrails
- Rate limiting
- Cost optimization
- Production deployment
- Final documentation

### Phase 4 Success Metrics
- 90%+ relevant responses
- < 3 second query response time
- Source attribution for all recommendations
- Safety checks prevent harmful advice
- 80%+ doctor trust in AI suggestions

---

## Post-Phase 4: Continuous Improvement

### Frontend Development (Parallel Track)
**Start:** Week 13-14  
**Duration:** 16 weeks

- Next.js 14 setup (Week 13-14)
- Authentication UI (Week 15-16)
- Patient management UI (Week 17-18)
- Appointment booking UI (Week 19-20)
- Prescription builder UI (Week 21-22)
- Dashboard UI (Week 23-24)
- Payment UI (Week 25-26)
- Library UI (Week 27-28)

### Mobile App (Future)
**Start:** After Phase 4  
**Platform:** React Native

- Patient mobile app
- Doctor mobile app
- Offline support
- Push notifications
- Mobile payment integration

### Advanced Features (Future)
- Telemedicine integration
- Lab results integration
- Inventory management
- Staff scheduling
- Multi-location support
- WhatsApp integration
- SMS appointment reminders
- Email marketing

---

## Release Strategy

### Alpha Release (Phase 1 Complete)
**Date:** August 1, 2026  
**Audience:** Internal team  
**Features:** Core clinic operations

### Beta Release (Phase 2 Complete)
**Date:** November 1, 2026  
**Audience:** 10 pilot clinics  
**Features:** + Knowledge base

### Public Beta (Phase 3 Complete)
**Date:** February 1, 2027  
**Audience:** 50+ clinics  
**Features:** + Medical library

### General Availability (Phase 4 Complete)
**Date:** April 1, 2027  
**Audience:** All alternative medicine practitioners  
**Features:** + AI assistant

---

## Key Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Backend Foundation | May 15, 2026 | ✅ Complete |
| Authentication Module | May 29, 2026 | ✅ Complete |
| Doctor Module | June 12, 2026 | ✅ Complete |
| Patient Module | June 26, 2026 | ✅ Complete |
| Appointments Module | July 3, 2026 | ✅ Complete |
| Prescription Module | July 17, 2026 | ✅ Complete |
| Payment Module | July 24, 2026 | ✅ Complete |
| Dashboard Module | May 1, 2026 | ✅ Complete |
| **Integration Framework** | **May 8, 2026** | 🔄 **Next** |
| **Production Launch** | **August 1, 2026** | 📋 Planned |
| Knowledge Base Beta | November 1, 2026 | 📋 Planned |
| Medical Library Beta | February 1, 2027 | 📋 Planned |
| AI Assistant GA | April 1, 2027 | 📋 Planned |

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database performance at scale | High | Implement caching, optimize queries, add indexes |
| Third-party API downtime (bKash) | Medium | Implement retry logic, fallback to manual entry |
| AI hallucinations in clinical context | High | Source attribution, confidence scoring, human review |
| Mobile app platform fragmentation | Medium | Use React Native, test on multiple devices |

### Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low doctor adoption | High | Pilot with 10 clinics, gather feedback, iterate |
| Competitor launches similar product | Medium | Focus on Bangladesh market, alternative medicine niche |
| Regulatory changes (medical software) | High | Consult legal, maintain compliance documentation |
| Payment gateway restrictions | Medium | Integrate multiple gateways, support manual payments |

### Resource Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Key developer unavailable | High | Knowledge sharing, comprehensive documentation |
| Budget overrun | Medium | Phased approach, MVP first, validate before scaling |
| Timeline delays | Medium | Buffer time in estimates, prioritize ruthlessly |

---

## Success Metrics

### Phase 1 (Backend MVP)
- ✅ 71+ API endpoints
- ✅ 80%+ test coverage
- ✅ Multi-tenant architecture
- ✅ bKash integration
- ⏳ Production deployment

### Phase 2 (Knowledge Base)
- 10,000+ medicines cataloged
- 5,000+ symptoms mapped
- < 100ms search latency
- 90%+ doctor satisfaction

### Phase 3 (Medical Library)
- 1,000+ books available
- Vector embeddings complete
- < 50ms search latency
- 85%+ engagement

### Phase 4 (AI Assistant)
- 90%+ relevant responses
- < 3s query response
- Source attribution
- 80%+ doctor trust

### Business Metrics (End of 2027)
- 100+ active clinics
- 10,000+ patients managed
- 50,000+ prescriptions issued
- $100K+ annual revenue
- 4.5+ star rating

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | May 1, 2026 | Initial foundation |
| 0.2.0 | May 15, 2026 | + Auth module |
| 0.3.0 | May 29, 2026 | + Doctor module |
| 0.4.0 | June 12, 2026 | + Patient module |
| 0.5.0 | June 26, 2026 | + Appointments |
| 0.6.0 | July 3, 2026 | + Prescriptions |
| 0.7.0 | July 17, 2026 | + Payments |
| 0.8.0 | May 1, 2026 | + Dashboard |
| 0.9.0 | May 8, 2026 | + Integration (planned) |
| 1.0.0 | August 1, 2026 | Production launch (planned) |

---

**Roadmap maintained by:** Development Team  
**Review frequency:** Bi-weekly  
**Next review:** May 8, 2026

**For detailed status, see:** [STATUS.md](STATUS.md)  
**For API details, see:** [API_ENDPOINTS.md](API_ENDPOINTS.md)  
**For current work, see:** [CLAUDE.md](CLAUDE.md)
