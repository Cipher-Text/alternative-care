# AltCare UI Mockups

Interactive HTML prototypes for the AltCare platform.

## Files

### 🏠 [index.html](./index.html)
Landing page to choose between mockup views.

### 🌐 [landing.html](./landing.html)
**Marketing Landing Page**

Public-facing website for attracting new practitioners and showcasing the platform.

**Sections included:**
- Hero section with value proposition and CTAs
- Platform statistics and trust indicators
- Multi-specialization support showcase (Homeopathy, Ayurveda, Unani, Herbal)
- 12 feature highlights with icons
- Benefits of alternative medicine (9 key benefits)
- Complete pricing comparison (Free, Plus, Pro)
- Monthly/Annual billing toggle with 20% discount
- Call-to-action sections
- Comprehensive footer with navigation

**Features demonstrated:**
- Smooth scrolling navigation
- Interactive pricing toggle
- Responsive grid layouts
- Gradient hero section
- Hover effects and animations
- Clean, modern design system
- Mobile-responsive structure

---

### 👨‍⚕️ [doctor-view.html](./doctor-view.html)
**Doctor / Practitioner Interface**

Complete clinic management system for alternative medicine practitioners.

**Screens included:**
- Dashboard with KPIs, patient calendar, charts
- Patient management with visit history timeline
- Prescription builder with PDF preview
- Payment tracking and invoice generation
- Medicine database search
- Symptom-based remedy search
- Book library with reading progress
- AI Assistant (RAG-powered clinical reference)
- Pricing plans comparison
- Settings (profile, clinic info, integrations)

**Features demonstrated:**
- Multi-specialization support (Homeopathy, Ayurveda, Unani, Herbal)
- Patient tagging system (special case, chronic, treatment, allergy)
- Real-time prescription builder
- Calendar with patient load visualization
- Charts and analytics

---

### 🔧 [admin-view.html](./admin-view.html)
**Platform Admin Interface**

Platform-wide administration and management for admins and operators.

**Screens included:**
- Platform Dashboard with tenant metrics
- Doctor Registration Approvals queue
- Tenants / Clinics management
- Global Medicine Database
- Global Book Library
- Integration Providers catalog (SMS, Email, Payment)
- Platform Activity Logs
- Platform Operators management

**Features demonstrated:**
- Multi-tenant overview and analytics
- Approval workflow for new doctors
- Global content curation (medicines, books)
- Integration provider management (Twilio, Banglalink, bKash, Nagad, Stripe, etc.)
- System-wide audit trail
- Team management

---

## How to Use

1. **Open in Browser:** Simply double-click any HTML file to open it in your default browser
2. **No Build Required:** These are standalone HTML files with embedded CSS and JavaScript
3. **Fully Interactive:** Click through navigation, buttons, and tabs to explore different screens

## Design System

### Color Palette
- **Primary (Green):** `#0F6E56` → `#1D9E75` — Main brand color for doctors
- **Secondary (Purple):** `#534AB7` → `#6B5FDB` — Platform admin accent
- **Functional Colors:**
  - Blue: Informational
  - Amber: Warnings
  - Red: Errors / Critical
  - Orange: Special indicators

### Typography
- **Font:** System default (`-apple-system`, `BlinkMacSystemFont`, `SF Pro Display`, `Inter`)
- **Sizes:** 10px–28px (responsive scaling)

### Components
- Cards with 1px borders and subtle shadows
- 8px border-radius for buttons and inputs
- 12-14px border-radius for cards
- Consistent 12-16px spacing units

## Technologies Demonstrated

- **No Framework:** Pure HTML/CSS/JavaScript
- **Responsive Grid Layouts:** CSS Grid and Flexbox
- **Interactive Navigation:** JavaScript-based SPA navigation
- **Modal Dialogs:** Overlay-based modals
- **Form Components:** Inputs, selects, textareas, tag inputs
- **Data Visualization:** CSS-based bar charts
- **Calendar UI:** Custom calendar with day cells and indicators

## Design Decisions

### UX Improvements in Admin View

1. **Clear Visual Hierarchy**
   - Purple accent color distinguishes admin interface from doctor (green)
   - Larger KPI cards with icons
   - Better spacing and breathing room

2. **Action-Oriented Layout**
   - Primary actions in top-right (Add Medicine, Add Provider, etc.)
   - Quick approval buttons in tables
   - Inline status badges

3. **Data-Dense Tables**
   - Uppercase column headers with letter-spacing
   - Hover states for better scannability
   - Monospace font for technical data (IDs, timestamps)

4. **Modal Workflows**
   - Forms in modals keep users in context
   - Clear cancel/submit actions
   - Validation-ready input fields

5. **Integration Provider Cards**
   - Visual branding (icons, colors for bKash, Nagad, etc.)
   - Usage statistics at a glance
   - Grid layout for easy scanning

### Mobile Considerations

Current mockups are desktop-optimized. For production:
- Sidebar collapses to hamburger menu on mobile
- Tables scroll horizontally or switch to card layout
- Modal dialogs fill screen on small devices
- Touch-friendly button sizes (minimum 44x44px)

## Next Steps

1. **Phase 1:** Convert to React/Next.js components with Tailwind CSS + shadcn/ui
2. **Phase 2:** Connect to FastAPI backend endpoints
3. **Phase 3:** Add real-time data updates via WebSockets
4. **Phase 4:** Implement mobile-responsive layouts

## Notes

- These are **visual prototypes**, not functional applications
- Data is static and hardcoded
- No actual API calls or database connections
- Perfect for stakeholder reviews, design feedback, and frontend development specs
