# Phase 1 Development Tasks
## Task Breakdown & Assignments

> Status Note (2026-05-08): This file is a legacy sprint board from early Phase 1 planning.  
> For current code-aligned status and priorities, use:
> - `docs/status/current.md`
> - `docs/planning/roadmap.md`
> - `docs/planning/roadmap-detailed.md`
>
> Code baseline reference:
> - Backend routers: 9 active modules
> - Module endpoints: 80 total
> - Frontend implemented routes: `/login`, `/dashboard`, `/patients`, `/patients/new`, `/patients/[id]`

**Sprint Duration**: 4 weeks (Apr 22 - May 19, 2026)  
**Team Size**: 3-5 developers  
**Daily Standup**: 10:00 AM GMT+6

---

## 📋 Task Board

### 🔴 Week 1: Setup & Foundation (Apr 22-28)

#### SETUP-001: Project Initialization
**Owner**: Lead Frontend  
**Effort**: 4 hours  
**Priority**: Critical

**Tasks:**
- [ ] Create Next.js 14 project with TypeScript
- [ ] Configure `tsconfig.json` with strict mode
- [ ] Set up Tailwind CSS with design tokens
- [ ] Add ESLint + Prettier configuration
- [ ] Configure `next.config.js` for production
- [ ] Set up environment variables (`.env.local`)

**Dependencies**: None  
**Deliverable**: Running Next.js app at `localhost:3000`

---

#### SETUP-002: Install Dependencies
**Owner**: Lead Frontend  
**Effort**: 2 hours  
**Priority**: Critical

**Tasks:**
```bash
npm install cmdk react-hotkeys-hook lucide-react
npm install @tanstack/react-query framer-motion zustand
npm install --save-dev @testing-library/react @testing-library/jest-dom
npm install --save-dev jest @playwright/test
```

**Deliverable**: `package.json` with all dependencies

---

#### SETUP-003: Database Migration
**Owner**: Lead Backend  
**Effort**: 3 hours  
**Priority**: Critical

**Tasks:**
- [ ] Create Alembic migration: `onboarding_progress` table
- [ ] Create Alembic migration: `usage_tracking` table
- [ ] Run migration on dev database
- [ ] Add indexes for performance
- [ ] Write seeder for test data

**SQL:**
```sql
CREATE TABLE onboarding_progress (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR REFERENCES users(id),
  checklist_dismissed BOOLEAN DEFAULT FALSE,
  ai_explored BOOLEAN DEFAULT FALSE,
  first_patient_at TIMESTAMP,
  first_prescription_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

CREATE INDEX idx_onboarding_user ON onboarding_progress(user_id);
```

**Deliverable**: Migration files + dev database updated

---

#### SETUP-004: API Routes Structure
**Owner**: Lead Backend  
**Effort**: 2 hours  
**Priority**: High

**Tasks:**
- [ ] Create `/api/onboarding/` routes
- [ ] Create `/api/usage/` routes
- [ ] Create `/api/user/recent` route
- [ ] Add CORS configuration
- [ ] Add rate limiting
- [ ] Test with Postman

**Deliverable**: API scaffold with stub responses

---

#### SETUP-005: Analytics Setup
**Owner**: Frontend Developer  
**Effort**: 3 hours  
**Priority**: Medium

**Tasks:**
- [ ] Sign up for PostHog (or Mixpanel)
- [ ] Install analytics SDK
- [ ] Create `utils/analytics.ts` wrapper
- [ ] Add event tracking helpers
- [ ] Test in dev mode
- [ ] Document events to track

**Deliverable**: Working analytics in development

---

#### SETUP-006: Testing Framework
**Owner**: Frontend Developer  
**Effort**: 4 hours  
**Priority**: Medium

**Tasks:**
- [ ] Configure Jest for React
- [ ] Configure Playwright for E2E
- [ ] Create test utilities (`renderWithProviders`)
- [ ] Write sample test
- [ ] Set up GitHub Actions for CI
- [ ] Document testing conventions

**Deliverable**: `npm test` runs successfully

---

### 🟡 Week 2: Core Components (Apr 29 - May 5)

#### COMP-001: Onboarding Checklist Component
**Owner**: Frontend Developer 1  
**Effort**: 8 hours  
**Priority**: Critical

**Tasks:**
- [ ] Create `<OnboardingChecklist />` component
- [ ] Implement progress bar animation
- [ ] Add dismiss functionality
- [ ] Add "Continue Setup" navigation
- [ ] Integrate with API endpoint
- [ ] Write unit tests (>80% coverage)
- [ ] Add to Storybook
- [ ] Mobile responsive

**Files:**
- `components/dashboard/OnboardingChecklist.tsx`
- `__tests__/OnboardingChecklist.test.tsx`

**Deliverable**: Component working on dashboard

---

#### COMP-002: Quick Actions Menu
**Owner**: Frontend Developer 2  
**Effort**: 6 hours  
**Priority**: High

**Tasks:**
- [ ] Create `<QuickActionsMenu />` component
- [ ] Implement floating button
- [ ] Add radial menu animation
- [ ] Add keyboard shortcut (Cmd+K)
- [ ] Implement keyboard hint tooltip
- [ ] Write unit tests
- [ ] Mobile positioning (bottom-center)
- [ ] Add to Storybook

**Files:**
- `components/global/QuickActionsMenu.tsx`
- `__tests__/QuickActionsMenu.test.tsx`

**Deliverable**: Floating button on all pages

---

#### COMP-003: Command Palette
**Owner**: Frontend Developer 1  
**Effort**: 10 hours  
**Priority**: High

**Tasks:**
- [ ] Create `<CommandPalette />` component using cmdk
- [ ] Implement fuzzy search
- [ ] Add keyboard navigation (↑↓ Enter)
- [ ] Load recent items from API
- [ ] Group items (Recent, Actions, Navigate)
- [ ] Add keyboard shortcut hint in footer
- [ ] Write integration tests
- [ ] Accessibility audit

**Files:**
- `components/global/CommandPalette.tsx`
- `__tests__/CommandPalette.test.tsx`

**Deliverable**: Working Cmd+K palette

---

#### COMP-004: Empty State Templates
**Owner**: Frontend Developer 2  
**Effort**: 5 hours  
**Priority**: Medium

**Tasks:**
- [ ] Create `<NoPatients />` empty state
- [ ] Create `<NoPrescriptions />` empty state
- [ ] Create `<NoPayments />` empty state
- [ ] Create `<NoSearchResults />` empty state
- [ ] Create `<FeatureLocked />` empty state
- [ ] Write tests for all 5
- [ ] Add to Storybook
- [ ] Document usage patterns

**Files:**
- `components/empty-states/*.tsx` (5 files)
- `__tests__/empty-states/*.test.tsx`

**Deliverable**: 5 reusable empty states

---

#### COMP-005: Upgrade Prompt Variants
**Owner**: Frontend Developer 3  
**Effort**: 6 hours  
**Priority**: High

**Tasks:**
- [ ] Create `<PatientLimitWarning />` component
- [ ] Create `<AIFeatureTeaser />` modal
- [ ] Create `<PDFExportLocked />` banner
- [ ] Add trigger logic (85%, 95%)
- [ ] Add dismiss/remind functionality
- [ ] Track analytics events
- [ ] Write tests
- [ ] A/B test setup (variant A/B)

**Files:**
- `components/upgrade/*.tsx` (3 files)
- `__tests__/upgrade/*.test.tsx`

**Deliverable**: Context-aware upgrade prompts

---

### 🟢 Week 3: API Integration (May 6-12)

#### API-001: Onboarding Progress Endpoint
**Owner**: Backend Developer 1  
**Effort**: 6 hours  
**Priority**: Critical

**Tasks:**
- [ ] Implement `GET /api/onboarding/progress/{user_id}`
- [ ] Implement `POST /api/onboarding/dismiss/{user_id}`
- [ ] Add helper functions (check_profile_complete, etc.)
- [ ] Write unit tests (pytest)
- [ ] Add to Swagger docs
- [ ] Test with frontend integration

**Files:**
- `backend/app/api/routes/onboarding.py`
- `backend/tests/api/test_onboarding.py`

**Deliverable**: Working API endpoints

---

#### API-002: Usage Limits Endpoint
**Owner**: Backend Developer 1  
**Effort**: 5 hours  
**Priority**: Critical

**Tasks:**
- [ ] Implement `GET /api/usage/limits`
- [ ] Count patients, prescriptions, AI queries
- [ ] Calculate warnings (85%, 95%)
- [ ] Add caching (Redis) for performance
- [ ] Write unit tests
- [ ] Test with frontend

**Files:**
- `backend/app/api/routes/usage.py`
- `backend/tests/api/test_usage.py`

**Deliverable**: Usage tracking API

---

#### API-003: Recent Items Endpoint
**Owner**: Backend Developer 2  
**Effort**: 4 hours  
**Priority**: Medium

**Tasks:**
- [ ] Implement `GET /api/user/recent`
- [ ] Return last 5 viewed patients
- [ ] Return last 3 prescribed medicines
- [ ] Add activity tracking on views
- [ ] Write tests
- [ ] Optimize query performance

**Files:**
- `backend/app/api/routes/user.py`
- `backend/tests/api/test_user.py`

**Deliverable**: Recent items for command palette

---

#### INTEG-001: Frontend-Backend Integration
**Owner**: Full-stack Developer  
**Effort**: 8 hours  
**Priority**: Critical

**Tasks:**
- [ ] Connect OnboardingChecklist to API
- [ ] Connect UpgradePrompts to usage API
- [ ] Connect CommandPalette to recent API
- [ ] Add loading states
- [ ] Add error handling
- [ ] Add optimistic updates
- [ ] Test all flows end-to-end

**Deliverable**: All components working with live data

---

#### INTEG-002: Analytics Integration
**Owner**: Frontend Developer  
**Effort**: 4 hours  
**Priority**: Medium

**Tasks:**
- [ ] Add tracking to all new components
- [ ] Track 15+ events (see list in PHASE1_DEV_KICKOFF.md)
- [ ] Test events in PostHog/Mixpanel
- [ ] Set up custom dashboards
- [ ] Document event naming conventions

**Deliverable**: All events tracked

---

### 🔵 Week 4: Polish & Launch (May 13-19)

#### TEST-001: E2E Testing
**Owner**: QA / Frontend Developer  
**Effort**: 6 hours  
**Priority**: High

**Tasks:**
- [ ] Write Playwright tests for onboarding flow
- [ ] Write Playwright tests for quick actions
- [ ] Write Playwright tests for command palette
- [ ] Write Playwright tests for upgrade prompts
- [ ] Run on multiple browsers (Chrome, Safari, Firefox)
- [ ] Run on mobile viewports
- [ ] Fix flaky tests

**Files:**
- `e2e/*.spec.ts` (4 files)

**Deliverable**: Passing E2E test suite

---

#### TEST-002: Accessibility Audit
**Owner**: Frontend Developer  
**Effort**: 4 hours  
**Priority**: Medium

**Tasks:**
- [ ] Run axe DevTools on all pages
- [ ] Test keyboard navigation
- [ ] Test screen reader (NVDA/VoiceOver)
- [ ] Fix ARIA labels
- [ ] Add focus indicators
- [ ] Test color contrast (WCAG AA)
- [ ] Document accessibility features

**Deliverable**: WCAG AA compliant

---

#### TEST-003: Mobile Responsive Testing
**Owner**: Frontend Developer  
**Effort**: 5 hours  
**Priority**: High

**Tasks:**
- [ ] Test on iPhone (Safari)
- [ ] Test on Android (Chrome)
- [ ] Test on tablet (iPad)
- [ ] Fix layout issues
- [ ] Optimize touch targets (48px min)
- [ ] Test in landscape mode
- [ ] Performance audit (Lighthouse)

**Deliverable**: Works on all devices

---

#### BETA-001: Beta Testing
**Owner**: Product Manager  
**Effort**: 10 hours (spread over 3 days)  
**Priority**: Critical

**Tasks:**
- [ ] Recruit 10 beta users (doctors)
- [ ] Send onboarding email + instructions
- [ ] Monitor usage (PostHog)
- [ ] Collect feedback (Google Form)
- [ ] Conduct 3 user interviews (30 min each)
- [ ] Compile feedback report
- [ ] Prioritize bugs/improvements

**Deliverable**: Beta feedback report

---

#### BUG-001: Bug Fixes from Beta
**Owner**: All Developers  
**Effort**: 8 hours  
**Priority**: Critical

**Tasks:**
- [ ] Fix P0 bugs (blocking)
- [ ] Fix P1 bugs (high priority)
- [ ] Triage P2 bugs (medium) for Phase 2
- [ ] Re-test all fixes
- [ ] Update tests if needed

**Deliverable**: Stable build

---

#### DEPLOY-001: Staging Deployment
**Owner**: DevOps / Backend Lead  
**Effort**: 4 hours  
**Priority**: High

**Tasks:**
- [ ] Deploy frontend to Vercel staging
- [ ] Deploy backend to staging server
- [ ] Run database migrations on staging
- [ ] Configure environment variables
- [ ] Smoke test all features
- [ ] Load test (100 concurrent users)

**Deliverable**: Staging environment live

---

#### DEPLOY-002: Production Deployment
**Owner**: DevOps / Backend Lead  
**Effort**: 4 hours  
**Priority**: Critical

**Tasks:**
- [ ] Create production deployment plan
- [ ] Backup production database
- [ ] Deploy frontend to Vercel production
- [ ] Deploy backend to production
- [ ] Run database migrations
- [ ] Smoke test critical paths
- [ ] Monitor error logs (Sentry)
- [ ] Roll back plan ready

**Deliverable**: Production deployment

---

#### MONITOR-001: Post-Launch Monitoring
**Owner**: Product Manager + Developers  
**Effort**: 2 hours/day for 1 week  
**Priority**: High

**Tasks:**
- [ ] Monitor activation rate daily
- [ ] Monitor error rates (Sentry)
- [ ] Monitor API performance (response times)
- [ ] Monitor conversion funnel
- [ ] Respond to support tickets
- [ ] Daily metrics report

**Deliverable**: Metrics dashboard + weekly report

---

## 📊 Progress Tracker

> Historical Snapshot: the percentages below reflect the original April sprint plan and are not current implementation truth.

### Overall Progress
```
Week 1: [░░░░░░░░░░] 0/6 tasks   (Setup)
Week 2: [░░░░░░░░░░] 0/5 tasks   (Components)
Week 3: [░░░░░░░░░░] 0/4 tasks   (Integration)
Week 4: [░░░░░░░░░░] 0/7 tasks   (Polish)

Total:  [Historical] 0/22 tasks in this specific sprint board
```

### Velocity Tracking
| Week | Planned | Completed | Velocity |
|------|---------|-----------|----------|
| 1    | 6       | -         | -        |
| 2    | 5       | -         | -        |
| 3    | 4       | -         | -        |
| 4    | 7       | -         | -        |

---

## 🚨 Blockers & Risks

### Current Blockers
*None yet*

### Potential Risks
1. **Risk**: API response time >500ms
   - **Mitigation**: Add Redis caching
   - **Owner**: Backend Lead

2. **Risk**: Beta users don't complete onboarding
   - **Mitigation**: 1-on-1 onboarding calls
   - **Owner**: Product Manager

3. **Risk**: Mobile Safari keyboard shortcuts not working
   - **Mitigation**: Touch-only fallback
   - **Owner**: Frontend Developer

---

## 📞 Team Communication

### Daily Standup (Async on Slack)
**Time**: By 10:00 AM GMT+6  
**Format**:
```
✅ Yesterday: [What I completed]
🚧 Today: [What I'm working on]
🚨 Blockers: [Any blockers]
```

### Weekly Demo (Friday 4:00 PM)
**Duration**: 30 minutes  
**Attendees**: All team + stakeholders  
**Format**: Live demo of completed features

### Sprint Retro (Friday 4:30 PM)
**Duration**: 30 minutes  
**Format**: 
- What went well? 👍
- What could improve? 🤔
- Action items 🎯

---

## 🎯 Definition of Done

A task is "Done" when:
- [ ] Code written and self-reviewed
- [ ] Unit tests written (>80% coverage)
- [ ] Linted and formatted (no ESLint errors)
- [ ] Tested locally (all browsers)
- [ ] PR created and reviewed
- [ ] Merged to main branch
- [ ] Deployed to staging
- [ ] QA tested on staging
- [ ] Documented (if needed)
- [ ] Analytics events added

---

## 📚 Resources

### Documentation
- [PHASE1_DEV_KICKOFF.md](./PHASE1_DEV_KICKOFF.md) - Detailed specs
- [UX_IMPROVEMENTS.md](./UX_IMPROVEMENTS.md) - UX strategy
- [ROADMAP.md](./ROADMAP.md) - Overall timeline

### Design
- Figma: *[Link TBD]*
- Design tokens: See `tailwind.config.js`

### APIs
- Swagger: `http://localhost:8000/docs`
- Postman collection: *[Link TBD]*

### Tools
- Project board: GitHub Projects
- Slack: #altcare-dev
- Sentry: *[Link TBD]*
- PostHog: *[Link TBD]*

---

*Last updated (legacy board): 2026-04-21*  
*Reconciled note added: 2026-05-08*
