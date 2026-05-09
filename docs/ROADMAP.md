# AltCare Product Roadmap

**Last Updated:** May 10, 2026  
**Current Version:** MVP v1.0 (Production Ready)

---

## 🎯 Vision

Build a comprehensive, multi-tenant SaaS platform for alternative medicine practitioners (Homeopathy, Ayurveda, Unani, Herbal) that streamlines clinical workflows, patient management, and practice operations while maintaining the highest standards of data security and regulatory compliance.

---

## 📊 Current State (MVP v1.0)

### ✅ Phase 1: Core Platform (COMPLETE)

**Authentication & Security** ✅
- [x] JWT-based authentication
- [x] Refresh token rotation
- [x] 2FA/TOTP support
- [x] Session management
- [x] Password complexity enforcement
- [x] Session invalidation on security changes
- [x] HTTP security headers (CSP, HSTS, X-Frame-Options)
- [x] Redis-backed rate limiting (login, API, AI-specific)
- [x] Row-level multi-tenant isolation (16/16 tests passing)
- [x] Fernet encryption for sensitive data

**Patient Management** ✅
- [x] Patient CRUD operations
- [x] Patient search (name, phone, code)
- [x] Patient tags/labels
- [x] Diagnosis history
- [x] Bangladesh geographic data (divisions, districts, upazilas)
- [x] Demographics tracking
- [x] Emergency contact management
- [x] Blood group tracking

**Appointments** ✅
- [x] Calendar view (react-big-calendar)
- [x] Appointment scheduling
- [x] Visit tracking
- [x] Status management (scheduled, completed, cancelled, no-show)
- [x] Appointment notes
- [x] Multiple appointment types

**Dashboard & Analytics** ✅
- [x] Key metrics (patients, appointments, revenue)
- [x] Revenue charts (monthly, quarterly)
- [x] Patient demographics (age, gender distribution)
- [x] Appointment statistics
- [x] Date range filtering

**Prescriptions** ✅
- [x] Complete CRUD workflow
- [x] Prescription builder (create/edit)
- [x] Medicine items management
- [x] Patient selection with search
- [x] Draft → Issued → Voided workflow
- [x] Immutability enforcement
- [x] Clinical information (diagnosis, notes, advice)
- [x] PDF generation (backend ready)
- [x] Status filtering

**Doctor Profile** ✅
- [x] Personal information management
- [x] Clinic information
- [x] Geographic location
- [x] License number tracking
- [x] Academic degrees (CRUD)
- [x] Certifications & trainings (CRUD)
- [x] Expiry tracking for certifications
- [x] Verification status
- [x] Language preference (English/Bengali)

**Infrastructure** ✅
- [x] Docker Compose setup
- [x] PostgreSQL 16 + pgvector
- [x] Redis 7 (caching, rate limiting, sessions)
- [x] MinIO (S3-compatible storage)
- [x] Celery (background tasks)
- [x] Alembic migrations
- [x] Seed data scripts
- [x] Health check endpoints
- [x] Metrics endpoints

---

## 🚧 Phase 2: Business Operations (IN PROGRESS)

### 📋 Payments & Billing (Backend Complete, Frontend Pending)

**Estimated Effort:** 5-7 hours frontend development

**Backend Ready:**
- [x] Payment processing
- [x] Invoice generation
- [x] bKash integration
- [x] Nagad integration
- [x] Rocket integration
- [x] SSLCommerz integration
- [x] Stripe integration
- [x] Payment status tracking
- [x] Transaction history
- [x] Refund support

**Frontend Needed:**
- [ ] Payment dashboard
- [ ] Invoice creation UI
- [ ] Payment method selection
- [ ] Transaction history view
- [ ] Invoice templates
- [ ] Payment status tracking
- [ ] Refund interface
- [ ] Payment reports

**Features:**
- Invoice generation with line items
- Multiple payment gateways (local + international)
- Payment status tracking (pending, completed, failed, refunded)
- Transaction history
- Receipt generation
- Payment reports

**Priority:** HIGH (monetization critical)

---

### 🔌 Integrations Management (Backend Complete, Frontend Pending)

**Estimated Effort:** 4-6 hours frontend development

**Backend Ready:**
- [x] Integration provider catalog
- [x] Tenant integration setup
- [x] Credential encryption (Fernet)
- [x] SMS providers (Twilio, Banglalink, Robi, BulkSMS BD)
- [x] Email providers (SendGrid, AWS SES, SMTP)
- [x] Payment providers (see above)
- [x] Integration logs
- [x] Usage tracking
- [x] Test endpoints

**Frontend Needed:**
- [ ] Integration provider listing
- [ ] Provider setup wizard
- [ ] Credential management UI
- [ ] Test integration interface
- [ ] Integration logs viewer
- [ ] Usage statistics
- [ ] Enable/disable toggles
- [ ] Integration status dashboard

**Features:**
- Visual provider catalog
- Step-by-step setup wizards
- Secure credential storage
- Test sending (SMS/Email)
- Usage analytics
- Error log viewing

**Priority:** MEDIUM (enables communication features)

---

## 🔮 Phase 3: Advanced Features (PLANNED)

### 🤖 AI Query Assistant

**Status:** Stub endpoint exists, needs implementation

**Current State:**
- [x] `/api/v1/ai/query` endpoint (returns 501)
- [x] Pro plan-gated
- [x] Rate limiting (100 req/hour)
- [ ] Vector search implementation
- [ ] RAG pipeline
- [ ] Knowledge base

**Planned Features:**
- Natural language prescription assistance
- Symptom-based medicine recommendations
- Drug interaction checking
- Homeopathic remedy finder
- Ayurvedic dosha analysis
- Medical knowledge Q&A
- Case history analysis

**Technical Requirements:**
- Vector embeddings (pgvector)
- LLM integration (OpenAI/Anthropic)
- RAG pipeline (LangChain/LlamaIndex)
- Knowledge base (medical texts, materia medica)
- Context-aware responses

**Estimated Effort:** 40-60 hours

**Priority:** MEDIUM-HIGH (differentiation feature)

---

### 📚 Medical Library & Knowledge Base

**Status:** Models exist, no routes

**Database Models Ready:**
- [x] Books
- [x] Chapters
- [x] Sections
- [x] Embeddings (vector search)
- [x] Reading progress
- [x] Bookmarks
- [x] Highlights

**Planned Features:**
- Digital library of medical texts
- Materia medica databases
- Search & filtering
- Vector-based semantic search
- Reading progress tracking
- Bookmarks & highlights
- Cross-referencing
- Citation support

**Estimated Effort:** 20-30 hours

**Priority:** MEDIUM (supports AI features)

---

### 💊 Medicine Database Management

**Status:** Models exist, no routes

**Database Models Ready:**
- [x] Medicines (bilingual)
- [x] Medicine aliases
- [x] Medicine-symptom mappings

**Planned Features:**
- Medicine CRUD (admin + tenant)
- Global medicine catalog (curated)
- Tenant-specific medicines
- Search with aliases
- Symptom-based search
- Bilingual support (English/Bengali)
- Category management
- Potency tracking (homeopathy)
- Indication/contraindication tracking

**Estimated Effort:** 15-20 hours

**Priority:** MEDIUM-HIGH (improves prescription workflow)

---

### 📊 Advanced Analytics & Reports

**Planned Features:**
- Practice growth metrics
- Patient retention analysis
- Revenue forecasting
- Appointment analytics (no-show rates, peak hours)
- Prescription patterns
- Treatment efficacy tracking
- Custom report builder
- Data export (PDF, CSV, Excel)
- Scheduled reports (email delivery)

**Estimated Effort:** 25-35 hours

**Priority:** MEDIUM (business intelligence)

---

### 📱 Mobile Apps (iOS/Android)

**Planned Features:**
- Native mobile apps (React Native / Flutter)
- Patient mobile app:
  - View prescriptions
  - Book appointments
  - Upload documents
  - Chat with doctor
  - Payment processing
- Doctor mobile app:
  - View schedule
  - Patient lookup
  - Quick prescriptions
  - Notifications

**Estimated Effort:** 120-160 hours

**Priority:** LOW-MEDIUM (future expansion)

---

## 🎨 Phase 4: UX & Polish (ONGOING)

### User Experience Improvements
- [ ] Onboarding wizard for new tenants
- [ ] Interactive product tour
- [ ] Keyboard shortcuts
- [ ] Bulk operations
- [ ] Advanced search & filters
- [ ] Customizable dashboards
- [ ] Dark mode improvements
- [ ] Accessibility (WCAG AA compliance)
- [ ] Performance optimization
- [ ] Progressive Web App (PWA) support

### Internationalization
- [x] English support
- [x] Bengali support (partial)
- [ ] Complete Bengali translations
- [ ] Arabic support (future)
- [ ] Hindi support (future)
- [ ] RTL layout support

---

## 🔒 Phase 5: Enterprise Features (FUTURE)

### Multi-Clinic Management
- Clinic chains/groups
- Role hierarchy (super admin, clinic admin, doctor, receptionist)
- Cross-clinic reporting
- Resource sharing
- Staff management

### Advanced Security
- Audit logs (comprehensive)
- HIPAA compliance mode
- Data retention policies
- Backup/restore UI
- Disaster recovery
- Penetration testing
- SOC 2 compliance

### White-Label Solution
- Custom branding
- Custom domains
- Email customization
- Logo/color themes
- Custom terminology

---

## 📅 Timeline

### Q2 2026 (Current)
- ✅ MVP v1.0 launch (Core platform)
- 🚧 Payments frontend (Week 1)
- 🚧 Integrations frontend (Week 2)
- 🔜 Medicine database (Week 3-4)

### Q3 2026
- AI query assistant (basic)
- Medical library
- Advanced analytics
- Mobile app (alpha)
- UX improvements

### Q4 2026
- AI query assistant (advanced)
- Mobile app (beta launch)
- Enterprise features (phase 1)
- Performance optimization

### Q1 2027
- White-label solution
- SOC 2 compliance
- Multi-clinic management
- International expansion

---

## 🎯 Success Metrics

### Current (MVP v1.0)
- ✅ 6/9 modules with complete frontend
- ✅ 82+ API endpoints
- ✅ 68+ frontend files
- ✅ Security: A (95/100)
- ✅ Test coverage: Multi-tenant isolation 100%
- ✅ Production ready

### Targets (Phase 2)
- [ ] 8/9 modules with complete frontend
- [ ] Payment processing live
- [ ] First paying customers
- [ ] 90%+ uptime
- [ ] <500ms API response time
- [ ] 10+ active tenants

### Targets (Phase 3)
- [ ] AI assistant with 80%+ accuracy
- [ ] 100+ paying customers
- [ ] 50,000+ prescriptions generated
- [ ] 99.9% uptime SLA
- [ ] Mobile apps launched

---

## 🚀 Getting Started (Contributors)

### Immediate Priorities (Next 2 Weeks)

1. **Payments Frontend** (HIGH)
   - Invoice UI
   - Payment gateway integration
   - Transaction history
   - ~5-7 hours

2. **Integrations Frontend** (MEDIUM)
   - Provider setup UI
   - Credential management
   - Test interface
   - ~4-6 hours

3. **Medicine Database** (MEDIUM-HIGH)
   - Backend routes
   - Frontend CRUD
   - Search integration
   - ~15-20 hours

### How to Contribute

1. Review [CLAUDE.md](../CLAUDE.md) for architecture
2. Check [GitHub Issues](https://github.com/anthropics/claude-code/issues) for open tasks
3. Follow conventions in existing modules
4. Write tests for new features
5. Update documentation

---

## 📝 Notes

### Design Decisions
- **Free-text medicines (MVP):** Allows immediate functionality without medicine DB dependency
- **PDF generation:** Backend-only (ReportLab/WeasyPrint), frontend triggers
- **Immutable prescriptions:** Draft → Issued → Voided workflow ensures audit trail
- **Row-level tenancy:** Security over performance (acceptable for target scale)

### Technical Debt
- [ ] Medicine autocomplete (using free-text for now)
- [ ] File uploads (URLs only currently)
- [ ] Bulk operations (no batch APIs)
- [ ] Export functionality (limited)
- [ ] Email/SMS templates (hardcoded)
- [ ] Notification system (basic)

### Known Limitations
- No prescription templates
- No appointment reminders (SMS/Email)
- No patient portal
- No telemedicine/video calls
- No e-signature for prescriptions
- No lab integration
- No pharmacy integration

---

## 🔗 Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Architecture & conventions
- [README.md](../README.md) - Getting started
- [Prescription Progress](archive/PRESCRIPTION_FRONTEND_COMPLETE_2026-05-10.md)
- [Doctor Profile Progress](archive/DOCTOR_PROFILE_PROGRESS_2026-05-10.md)

---

**Last Review:** 2026-05-10  
**Next Review:** 2026-06-01  
**Maintained by:** Development Team
