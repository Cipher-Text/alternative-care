# Documentation Audit & Consolidation Plan

**Date:** May 1, 2026  
**Purpose:** Identify redundancy and apply SRP to documentation

---

## 📊 Current State (44 files, 21,290 lines)

### 🔴 Redundancy Issues Found:

#### 1. **Multiple READMEs (5 files, ~1,500 lines)**
- ❌ `README.md` (338 lines) - Project overview
- ❌ `backend/README.md` (228 lines) - Backend overview
- ❌ `docs/README.md` (219 lines) - Documentation map
- ❌ `frontend/README.md` (36 lines) - Generated Next.js
- ⚠️  **Overlap:** All describe project structure, setup, tech stack

#### 2. **Multiple ROADMAPs (3 files, ~2,500 lines)**
- ❌ `backend/ROADMAP.md` (692 lines) - Backend roadmap
- ❌ `docs/planning/roadmap.md` (304 lines) - High-level roadmap
- ❌ `docs/planning/roadmap-detailed.md` (1,525 lines) - Detailed roadmap
- ⚠️  **Overlap:** Phase 1 Week 1-14 repeated across all three

#### 3. **Multiple STATUS (2 files, ~800 lines)**
- ❌ `backend/STATUS.md` (467 lines) - Backend status
- ❌ `docs/status/current.md` (319 lines) - Current status
- ⚠️  **Overlap:** Both track Week 1-14 completion

#### 4. **Multiple SETUP (3 files, ~1,900 lines)**
- ❌ `GETTING_STARTED.md` (384 lines) - Quick start
- ❌ `backend/SETUP.md` (230 lines) - Backend setup
- ❌ `FRONTEND_SETUP.md` (1,311 lines) - Frontend setup
- ⚠️  **Overlap:** Docker, database, environment variables

#### 5. **Module READMEs vs API_ENDPOINTS (8 files, ~3,900 lines)**
- ❌ 7 module READMEs (auth, doctor, patient, appointments, prescriptions, payment, dashboard)
- ❌ `backend/API_ENDPOINTS.md` (246 lines)
- ⚠️  **Overlap:** Each module README duplicates endpoint documentation

#### 6. **Archive Clutter (6 files, ~2,100 lines)**
- ❌ Old setup guides now archived
- ❌ Session summaries
- ⚠️  **Can be deleted** - outdated or redundant

---

## ✅ Proposed SRP Structure

### **Principle: One Document, One Purpose**

```
alternative-care/
├── README.md                          # ONLY: Project overview + quick links
├── SETUP.md                           # ONLY: Complete setup (backend + frontend)
├── ROADMAP.md                         # ONLY: Timeline (current + future phases)
├── CLAUDE.md                          # ONLY: AI assistant instructions
├── CHANGELOG.md                       # ONLY: Version history
│
├── backend/
│   ├── API.md                         # ONLY: All 71 endpoints (consolidated)
│   └── README.md                      # ONLY: Backend architecture overview
│
├── frontend/
│   └── README.md                      # ONLY: Frontend architecture overview
│
└── docs/
    ├── README.md                      # ONLY: Documentation index
    ├── ARCHITECTURE.md                # ONLY: System design (database + tech stack)
    ├── DEVELOPMENT.md                 # ONLY: Developer guide (testing + i18n)
    └── archive/                       # OLD: Archived session notes
```

**Total:** ~12 core files (vs 44 current)

---

## 🎯 Consolidation Actions

### **Action 1: Consolidate READMEs**
- **Keep:** Root `README.md` (project overview)
- **Merge into root README:**
  - `backend/README.md` → Section: "Backend Architecture"
  - `frontend/README.md` → Section: "Frontend Architecture"
- **Delete:** `docs/README.md` (redundant index)

### **Action 2: Consolidate ROADMAPs**
- **Keep:** Root `ROADMAP.md`
- **Merge:**
  - `backend/ROADMAP.md` → Into root ROADMAP
  - `docs/planning/roadmap-detailed.md` → Into root ROADMAP
- **Delete:** `docs/planning/roadmap.md` (redundant)

### **Action 3: Consolidate STATUS**
- **Keep:** `ROADMAP.md` (current phase section)
- **Delete:**
  - `backend/STATUS.md`
  - `docs/status/current.md`
- **Replace with:** Live status in README.md header

### **Action 4: Consolidate SETUP**
- **Keep:** Root `SETUP.md` (complete setup)
- **Sections:**
  1. Prerequisites
  2. Backend Setup (from backend/SETUP.md)
  3. Frontend Setup (from FRONTEND_SETUP.md)
  4. Development Workflow
- **Delete:**
  - `GETTING_STARTED.md` (merge into SETUP.md)
  - `backend/SETUP.md`
  - Keep `FRONTEND_SETUP.md` as detailed reference

### **Action 5: Consolidate API Documentation**
- **Create:** `backend/API.md` (single source of truth)
- **Sections:**
  - Overview (71 endpoints)
  - Authentication endpoints (from auth/README.md)
  - Doctor endpoints (from doctor/README.md)
  - Patient endpoints (from patient/README.md)
  - Appointments endpoints (from appointments/README.md)
  - Prescriptions endpoints (from prescriptions/README.md)
  - Payments endpoints (from payment/README.md)
  - Dashboard endpoints (from dashboard/README.md)
- **Delete:**
  - All module READMEs
  - `backend/API_ENDPOINTS.md`

### **Action 6: Consolidate Architecture Docs**
- **Create:** `docs/ARCHITECTURE.md`
- **Merge:**
  - `docs/architecture/database.md`
  - `docs/architecture/tech-stack.md`
- **Sections:**
  1. System Design
  2. Database Schema (30 tables)
  3. Tech Stack
  4. Multi-Tenancy

### **Action 7: Consolidate Development Docs**
- **Create:** `docs/DEVELOPMENT.md`
- **Merge:**
  - `docs/development/quick-reference.md`
  - `docs/development/i18n.md`
  - `docs/development/frontend-checklist.md`
- **Sections:**
  1. Quick Reference (code patterns)
  2. Testing Guide
  3. i18n Guide (EN/BN)
  4. Frontend Checklist

### **Action 8: Clean Archive**
- **Delete entire `docs/archive/` folder** (6 files, 2,100 lines)
- **Reason:** Outdated session notes, no longer relevant

---

## 📈 Impact Analysis

### **Before Consolidation:**
- Total files: 44
- Total lines: 21,290
- Redundancy: ~40%
- Maintenance: High (update 3-4 places per change)

### **After Consolidation:**
- Total files: ~12 core + 3 detailed
- Total lines: ~8,000 (62% reduction)
- Redundancy: <5%
- Maintenance: Low (single source of truth)

---

## 🚀 Benefits

1. **Single Source of Truth** - No conflicting information
2. **Easier Maintenance** - Update once, not 3-4 times
3. **Faster Onboarding** - Less docs to read
4. **Better SEO** - No duplicate content confusion
5. **SRP Compliance** - Each doc has one clear purpose

---

## 📋 Execution Plan

### **Phase 1: Create Consolidated Files (1 hour)**
1. Create `SETUP.md` (merge 3 setup docs)
2. Create `backend/API.md` (merge 8 endpoint docs)
3. Create `docs/ARCHITECTURE.md` (merge 2 architecture docs)
4. Create `docs/DEVELOPMENT.md` (merge 3 development docs)

### **Phase 2: Update Root Files (30 min)**
1. Update `README.md` (add backend/frontend sections)
2. Update `ROADMAP.md` (merge 3 roadmaps)
3. Update `CLAUDE.md` (point to new structure)

### **Phase 3: Delete Redundant Files (15 min)**
1. Delete 7 module READMEs
2. Delete 2 STATUS files
3. Delete `docs/archive/` folder (6 files)
4. Delete `backend/API_ENDPOINTS.md`
5. Delete `backend/SETUP.md`
6. Delete `GETTING_STARTED.md`

### **Phase 4: Update Cross-References (15 min)**
1. Find all `[link](old-file.md)` references
2. Update to new file paths
3. Test all links work

**Total Time:** ~2 hours

---

## ✅ Final Structure (SRP-Compliant)

```
alternative-care/
│
# Core Documentation (6 files)
├── README.md              (350 lines) - Project overview, quick start
├── SETUP.md               (400 lines) - Complete setup guide
├── ROADMAP.md             (600 lines) - Timeline + phases
├── CHANGELOG.md           (110 lines) - Version history
├── CLAUDE.md              (400 lines) - AI instructions
└── FRONTEND_SETUP.md      (1,311 lines) - Detailed frontend guide
│
# Backend (2 files)
├── backend/
│   ├── README.md          (150 lines) - Architecture overview
│   └── API.md             (800 lines) - All endpoints
│
# Frontend (1 file)
├── frontend/
│   └── README.md          (100 lines) - Architecture overview
│
# Detailed Documentation (3 files)
└── docs/
    ├── ARCHITECTURE.md    (1,200 lines) - Database + tech stack
    ├── DEVELOPMENT.md     (1,000 lines) - Dev guide + testing
    └── README.md          (100 lines) - Documentation index

TOTAL: 12 core files, ~6,500 lines
```

---

## 🎯 Recommendation

**Execute consolidation plan?**
- Reduces docs by 73% (44 → 12 files)
- Eliminates 40% redundancy
- Applies SRP throughout
- Improves maintainability

**Next Step:** Run consolidation scripts to create new structure.
