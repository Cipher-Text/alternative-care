# Frontend Development Checklist — Week 13-18

> **Status:** Ready to start | **Start Date:** Week 13 (May 6, 2026)  
> **Target:** Production-ready frontend by Week 18 (June 10, 2026)

---

## Overview

This checklist tracks the frontend development progress from initial setup through production launch. Each week builds on the previous, with integrated testing throughout.

**Total Duration:** 6 weeks  
**Tech Stack:** Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui + React Query  
**Backend Dependency:** All 71 API endpoints ready ✅

---

## Week 13: Foundation & Authentication (May 6-12)

### Day 1-2: Project Setup ✅

- [ ] Run `./frontend-quickstart.sh` to initialize project
- [ ] Verify backend is running (http://localhost:8000/health)
- [ ] Create Next.js project with TypeScript
- [ ] Install all dependencies (axios, react-query, zustand, etc.)
- [ ] Initialize shadcn/ui component library
- [ ] Configure environment variables (.env.local)
- [ ] Create directory structure (see FRONTEND_SETUP.md)
- [ ] Setup translation files (en.json, bn.json)
- [ ] Configure Next.js (next.config.js)
- [ ] Test dev server runs (http://localhost:3000)

**Deliverable:** Frontend project runs, displays Next.js welcome page

---

### Day 3-5: Authentication Flow

#### API Client Setup

- [ ] Create `src/lib/api/client.ts` - Axios instance with interceptors
- [ ] Create `src/store/authStore.ts` - Zustand auth store
- [ ] Create `src/lib/api/auth.ts` - Auth API calls
- [ ] Test token storage in cookies (not localStorage for security)
- [ ] Test token refresh on 401 response
- [ ] Test logout clears all tokens

#### Login Page

- [ ] Create `src/app/(auth)/layout.tsx` - Auth layout (no sidebar)
- [ ] Create `src/app/(auth)/login/page.tsx` - Login page
- [ ] Create `src/components/auth/LoginForm.tsx` - Login form component
- [ ] Implement form validation with zod + react-hook-form
- [ ] Style with shadcn/ui components
- [ ] Handle login success → redirect to /dashboard
- [ ] Handle login errors → show toast notifications
- [ ] Test with actual backend API

#### 2FA Flow

- [ ] Create `src/components/auth/TwoFactorForm.tsx` - TOTP input
- [ ] Detect 2FA requirement from login response
- [ ] Show 2FA form after password verification
- [ ] Implement 6-digit code input
- [ ] Handle 2FA success → redirect to /dashboard
- [ ] Handle 2FA errors → show error message
- [ ] Test with 2FA-enabled test user

#### Protected Routes

- [ ] Create `src/components/auth/ProtectedRoute.tsx` - Route guard
- [ ] Redirect to /login if not authenticated
- [ ] Check token validity on mount
- [ ] Refresh token if expired but refresh token valid
- [ ] Test navigation between protected/public routes

**Deliverable:** Complete authentication flow working end-to-end

---

### Day 6-7: Dashboard Layout

#### Layout Components

- [ ] Create `src/app/(dashboard)/layout.tsx` - Main dashboard layout
- [ ] Create `src/components/layout/Sidebar.tsx` - Navigation sidebar
- [ ] Create `src/components/layout/Header.tsx` - Top header with user menu
- [ ] Create `src/components/layout/MobileNav.tsx` - Mobile hamburger menu
- [ ] Create `src/components/layout/Footer.tsx` - Footer (optional)

#### Navigation

- [ ] Implement navigation menu with icons (lucide-react)
- [ ] Navigation items:
  - Dashboard (Home icon)
  - Patients (Users icon)
  - Appointments (Calendar icon)
  - Prescriptions (FileText icon)
  - Payments (CreditCard icon)
  - Medicines (Pill icon)
  - Library (BookOpen icon)
  - Settings (Settings icon)
- [ ] Highlight active route
- [ ] Show user info in header (name, email, avatar)
- [ ] Add dropdown menu: Profile, Settings, Logout
- [ ] Implement logout functionality

#### Responsive Design

- [ ] Test on desktop (1920x1080)
- [ ] Test on tablet (768x1024)
- [ ] Test on mobile (375x667)
- [ ] Sidebar collapses on mobile
- [ ] Mobile navigation works

**Deliverable:** Dashboard shell with working navigation

---

## Week 14: Patient Management (May 13-19)

### Day 1-2: Patient API & Hooks

- [ ] Create `src/types/patient.ts` - Patient TypeScript types
- [ ] Create `src/lib/api/patients.ts` - Patient API calls
- [ ] Create `src/lib/hooks/usePatients.ts` - React Query hooks
- [ ] Implement `usePatients()` - List patients
- [ ] Implement `usePatient(id)` - Get single patient
- [ ] Implement `useCreatePatient()` - Create mutation
- [ ] Implement `useUpdatePatient()` - Update mutation
- [ ] Implement `useDeletePatient()` - Delete mutation
- [ ] Test all hooks with React Query DevTools

---

### Day 3-4: Patient List Page

- [ ] Create `src/app/(dashboard)/patients/page.tsx` - List page
- [ ] Create `src/components/patients/PatientCard.tsx` - Patient card component
- [ ] Implement patient grid (responsive: 1/2/3 columns)
- [ ] Add search/filter functionality
- [ ] Show patient code, name, age, gender, phone
- [ ] Add "Add Patient" button → `/patients/new`
- [ ] Click card → `/patients/[id]`
- [ ] Show loading spinner while fetching
- [ ] Show error message if API fails
- [ ] Show "No patients" empty state

---

### Day 5-6: Create/Edit Patient Forms

- [ ] Create `src/app/(dashboard)/patients/new/page.tsx` - Create page
- [ ] Create `src/app/(dashboard)/patients/[id]/edit/page.tsx` - Edit page (optional, can edit in place)
- [ ] Create `src/components/patients/PatientForm.tsx` - Reusable form
- [ ] Form fields:
  - First name, Last name
  - Date of birth (date picker)
  - Gender (select)
  - Phone (required)
  - Email (optional)
  - Address (textarea)
  - Division, District, Upazila (cascading selects)
  - Emergency contact (name + phone)
  - Blood group (select)
- [ ] Implement form validation with zod
- [ ] Handle create success → redirect to patient detail
- [ ] Handle update success → show toast, stay on page
- [ ] Handle errors → show field-level errors
- [ ] Test with Bangladesh geographic data

---

### Day 7: Patient Detail Page

- [ ] Create `src/app/(dashboard)/patients/[id]/page.tsx` - Detail page
- [ ] Show patient profile card (photo placeholder, name, code, age, gender)
- [ ] Show contact information
- [ ] Show address with division/district/upazila
- [ ] Show emergency contact
- [ ] Show tags (if any)
- [ ] Show diagnoses (if any)
- [ ] Add "Edit" button
- [ ] Add "Delete" button with confirmation dialog
- [ ] Show loading state
- [ ] Handle not found (404)

**Deliverable:** Complete patient CRUD with all features working

---

## Week 15: Dashboard Analytics (May 20-26)

### Day 1-2: Dashboard API Integration

- [ ] Create `src/types/dashboard.ts` - Dashboard TypeScript types
- [ ] Create `src/lib/api/dashboard.ts` - Dashboard API calls
- [ ] Create `src/lib/hooks/useDashboard.ts` - Dashboard hooks
- [ ] Implement `useOverview()` - Overview stats
- [ ] Implement `useFinancialAnalytics()` - Financial charts
- [ ] Implement `usePatientAnalytics()` - Patient demographics
- [ ] Test API integration with date range filters

---

### Day 3-4: Overview Dashboard

- [ ] Create `src/app/(dashboard)/page.tsx` - Main dashboard
- [ ] Install recharts: `npm install recharts`
- [ ] Create stat cards component (4 columns):
  - Total Patients
  - Today's Appointments
  - This Month Revenue
  - Pending Payments
- [ ] Show patient growth chart (line chart)
- [ ] Show revenue trend chart (area chart)
- [ ] Show appointment status breakdown (bar chart)
- [ ] Add date range picker (This Week, This Month, Last 30 Days, Custom)
- [ ] Real-time data updates
- [ ] Loading skeleton components
- [ ] Responsive layout (stack on mobile)

---

### Day 5-6: Analytics Pages

- [ ] Create `src/app/(dashboard)/analytics/patients/page.tsx`
- [ ] Show patient demographics (gender pie chart)
- [ ] Show age distribution (bar chart)
- [ ] Show top diagnoses (list)
- [ ] Create `src/app/(dashboard)/analytics/financial/page.tsx`
- [ ] Show revenue by payment method (pie chart)
- [ ] Show daily revenue trend (line chart)
- [ ] Show invoice status (donut chart)
- [ ] Add export to CSV button (optional)

**Deliverable:** Dashboard with real-time analytics and charts

---

## Week 16: Appointments & Prescriptions (May 27 - June 2)

### Day 1-3: Appointments Module

- [ ] Create `src/lib/api/appointments.ts`
- [ ] Create `src/lib/hooks/useAppointments.ts`
- [ ] Create `src/app/(dashboard)/appointments/page.tsx` - Calendar view
- [ ] Install calendar library: `npm install react-big-calendar date-fns`
- [ ] Show appointments in calendar
- [ ] Click date → create appointment
- [ ] Click appointment → view/edit details
- [ ] Filter by status (Scheduled, Confirmed, Completed, Cancelled)
- [ ] Search by patient name
- [ ] Create appointment form (patient, date/time, type, notes)
- [ ] Handle conflict detection
- [ ] Show appointment detail modal/page

---

### Day 4-7: Prescriptions Module

- [ ] Create `src/lib/api/prescriptions.ts`
- [ ] Create `src/lib/hooks/usePrescriptions.ts`
- [ ] Create `src/app/(dashboard)/prescriptions/page.tsx` - List view
- [ ] Create `src/app/(dashboard)/prescriptions/[id]/page.tsx` - Detail view
- [ ] Create `src/app/(dashboard)/prescriptions/new/page.tsx` - Builder
- [ ] Prescription builder:
  - Select patient
  - Select visit (or create new)
  - Add prescription items (medicine, dosage, duration, instructions)
  - Search medicines from database
  - Add custom/free-text medicines
  - Preview prescription
- [ ] Implement draft → issued workflow
- [ ] Show immutable indicator (can't edit issued prescriptions)
- [ ] PDF download button
- [ ] Void prescription (with confirmation)
- [ ] Filter by patient, status, date range

**Deliverable:** Appointments calendar + Prescription builder working

---

## Week 17: Payments & Medicines (June 3-9)

### Day 1-3: Payments Module

- [ ] Create `src/lib/api/payments.ts`
- [ ] Create `src/lib/hooks/usePayments.ts`
- [ ] Create `src/app/(dashboard)/payments/page.tsx` - List view
- [ ] Payment list with filters (status, method, date range)
- [ ] Create payment form:
  - Select patient
  - Select visit (optional)
  - Amount
  - Payment method (Cash, bKash)
  - Notes
- [ ] Show payment detail modal
- [ ] Show invoice (auto-generated)
- [ ] Download invoice PDF
- [ ] Filter by patient, method, status, date range
- [ ] Show payment summary cards (total, pending, paid)

#### bKash Integration (if time permits)

- [ ] Create bKash payment flow (execute, query)
- [ ] Show payment status (pending, completed, failed)
- [ ] Handle webhook callbacks (backend already implemented)

---

### Day 4-5: Medicines Module

- [ ] Create `src/lib/api/medicines.ts`
- [ ] Create `src/lib/hooks/useMedicines.ts`
- [ ] Create `src/app/(dashboard)/medicines/page.tsx` - List view
- [ ] Medicine list with search/filter
- [ ] Filter by system (Homeopathy, Ayurveda, Unani, Herbal)
- [ ] Filter by category
- [ ] Search by name (EN/BN)
- [ ] Show medicine detail modal (name, category, indications, contraindications)
- [ ] Admin: Add/edit medicines (if admin user)

---

### Day 6-7: Settings & Profile

- [ ] Create `src/app/(dashboard)/settings/page.tsx`
- [ ] Profile settings:
  - Update name, email, phone
  - Change password
  - Upload avatar (if MinIO configured)
  - Language preference (EN/BN)
- [ ] 2FA settings:
  - Enable/disable 2FA
  - Show QR code
  - Verify TOTP code
  - Regenerate backup codes
- [ ] Notification preferences (placeholder for future)
- [ ] Test all settings save correctly

**Deliverable:** Payments, medicines, and settings complete

---

## Week 18: Polish, Testing & Launch (June 10-16)

### Day 1-2: UI Polish

- [ ] Review all pages for consistent styling
- [ ] Add loading states everywhere
- [ ] Add error boundaries
- [ ] Add empty states (no data)
- [ ] Add confirmation dialogs (delete actions)
- [ ] Toast notifications for all actions
- [ ] Fix any responsive layout issues
- [ ] Add keyboard shortcuts (optional)
- [ ] Add accessibility (aria-labels, focus management)

---

### Day 3-4: Language Switching (EN/BN)

- [ ] Create `src/components/shared/LanguageSwitcher.tsx`
- [ ] Add to header
- [ ] Complete translations in `src/messages/en.json`
- [ ] Complete translations in `src/messages/bn.json`
- [ ] Test all pages in Bengali
- [ ] Fix any text overflow issues in Bengali
- [ ] Persist language preference to backend

---

### Day 5-6: Testing & Bug Fixes

- [ ] Test all features end-to-end:
  - [ ] Login (password + 2FA)
  - [ ] Patient CRUD
  - [ ] Appointments (create, edit, cancel)
  - [ ] Prescriptions (create, issue, void, PDF)
  - [ ] Payments (cash, bKash)
  - [ ] Dashboard analytics
  - [ ] Settings
  - [ ] Logout
- [ ] Test on different browsers (Chrome, Firefox, Safari)
- [ ] Test on different devices (desktop, tablet, mobile)
- [ ] Fix all critical bugs
- [ ] Document known issues

---

### Day 7: Production Build & Documentation

- [ ] Create production build: `npm run build`
- [ ] Fix any build errors
- [ ] Test production build locally: `npm run start`
- [ ] Optimize images (if any)
- [ ] Review bundle size
- [ ] Update FRONTEND_SETUP.md with any new findings
- [ ] Create deployment guide (Vercel/Netlify)
- [ ] Add frontend section to ROADMAP.md
- [ ] Update README.md with frontend completion

**Deliverable:** Production-ready frontend, fully tested ✅

---

## Post-Launch (Week 19+)

### Immediate Follow-up

- [ ] Monitor production errors (Sentry integration)
- [ ] Gather user feedback
- [ ] Fix high-priority bugs
- [ ] Performance optimization (if needed)

### Phase 2 Preparation

- [ ] Medicine database advanced search
- [ ] Symptom search integration
- [ ] Advanced filtering/sorting
- [ ] Bulk actions (e.g., export patient data)

---

## Testing Checklist (Continuous)

### Authentication

- [x] Login with valid credentials
- [x] Login with invalid credentials shows error
- [x] 2FA flow works for enabled users
- [x] Token refresh happens automatically
- [x] Logout clears all tokens and redirects
- [x] Protected routes redirect to login

### Patient Management

- [ ] Create patient with all fields
- [ ] Create patient with only required fields
- [ ] Edit patient updates correctly
- [ ] Delete patient shows confirmation
- [ ] Search patients works
- [ ] Filter patients by gender/tags
- [ ] Patient detail page shows all info
- [ ] Geographic cascading (division → district → upazila) works

### Appointments

- [ ] Create appointment
- [ ] Edit appointment
- [ ] Cancel appointment
- [ ] Conflict detection prevents double-booking
- [ ] Calendar view shows all appointments
- [ ] Filter by status works

### Prescriptions

- [ ] Create draft prescription
- [ ] Add items (database medicines)
- [ ] Add items (custom medicines)
- [ ] Issue prescription (becomes immutable)
- [ ] Cannot edit issued prescription
- [ ] Void prescription works
- [ ] PDF download works

### Payments

- [ ] Create cash payment
- [ ] Create bKash payment
- [ ] Invoice auto-generated
- [ ] Filter by status/method/date works
- [ ] Payment summary cards accurate

### Dashboard

- [ ] Overview stats load
- [ ] Charts render correctly
- [ ] Date range filter updates data
- [ ] No errors in console

### UI/UX

- [ ] All forms validate correctly
- [ ] Error messages are clear
- [ ] Success toasts show for actions
- [ ] Loading spinners show during API calls
- [ ] Mobile navigation works
- [ ] Responsive on all screen sizes
- [ ] Dark mode toggle works (if implemented)

### i18n

- [ ] Language switcher changes all text
- [ ] Bengali translations complete
- [ ] No missing translation keys
- [ ] No text overflow in Bengali

---

## Success Criteria

**Week 13-14:**
- ✅ Authentication working (login, 2FA, logout)
- ✅ Dashboard layout complete
- ✅ Patient CRUD fully functional

**Week 15-16:**
- ✅ Dashboard analytics with charts
- ✅ Appointments calendar working
- ✅ Prescription builder functional

**Week 17-18:**
- ✅ Payments module complete
- ✅ All 71 backend APIs integrated
- ✅ Production build working
- ✅ No critical bugs

---

## Resources

**Documentation:**
- [FRONTEND_SETUP.md](../../FRONTEND_SETUP.md) - Complete setup guide
- [Next.js Docs](https://nextjs.org/docs) - Framework reference
- [shadcn/ui](https://ui.shadcn.com) - Component library
- [React Query Docs](https://tanstack.com/query/v3) - Data fetching
- [Tailwind CSS](https://tailwindcss.com/docs) - Styling

**Tools:**
- React Query DevTools - Debug API calls
- Next.js Dev Tools - Performance
- Chrome DevTools - Debugging

**Backend:**
- API Docs: http://localhost:8000/docs
- API Endpoints: [API_ENDPOINTS.md](../../API_ENDPOINTS.md)

---

**Last Updated:** May 1, 2026  
**Status:** Ready to start Week 13 ✅  
**Next Milestone:** Week 14 - Patient Management complete
