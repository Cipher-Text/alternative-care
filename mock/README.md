# AltCare UI Mockups

Interactive HTML prototypes built before the React/Next.js app was implemented.
They serve as **design reference** and **stakeholder demo** artifacts.

> The real application is in `frontend/`. These mocks are read-only historical reference.

---

## Files

### [index.html](./index.html)
Navigation hub — links to the four mockup views.

### [landing.html](./landing.html)
**Public marketing page**

- Hero, value proposition, CTAs
- Feature showcase (12 features)
- Pricing tiers: Free / Plus / Pro with monthly/annual toggle
- Multi-specialisation section (Homeopathy, Ayurveda, Unani, Herbal)

### [doctor-view.html](./doctor-view.html)
**Practitioner interface**

Screens: Dashboard · Patient management · Prescription builder · Payments · Medicine search · Symptom search · Book library · AI assistant · Settings

### [admin-view.html](./admin-view.html)
**Platform admin interface**

Screens: Platform dashboard · Doctor approval queue · Tenants/Clinics · Global medicine DB · Global book library · Integration providers · Activity logs · Operators

### [doctors.html](./doctors.html)
**Public doctor directory**

Search/browse mock for a public "Find a Doctor" page — not yet wired to a real route (no `/doctors` route exists in `frontend/src/app`).

---

## Implementation Status

| Mock feature | Built in app? |
|---|---|
| Auth (login, 2FA) | ✅ Complete |
| Dashboard analytics | ✅ Complete |
| Patient management | ✅ Complete |
| Appointments / calendar | ✅ Complete |
| Prescription builder | ✅ Complete |
| Doctor profile (degrees, trainings) | ✅ Complete |
| Payments & invoicing | ✅ Complete |
| Medicine library | ✅ Complete |
| Symptom library | ✅ Complete |
| SMS/Email integrations | ✅ Complete |
| Book library | ⬜ Backend models only, no routes |
| AI assistant | ⬜ Stub endpoint (pro plan, not built) |
| Public landing page | ⬜ Not built (mock only) |
| Public doctor directory | ⬜ Not built (mock only) |
| Platform admin UI | ⬜ Not built (mock only) |

---

## Design Notes

### Color palette — mocks vs. app

The mocks use a **green** primary (`#0F6E56`) for the doctor view and **purple** (`#534AB7`) for the admin view. The built frontend uses **indigo** (`indigo-600` / `#4F46E5`) throughout. If you revisit the mock design, align to indigo.

### Typography
System default (`-apple-system`, `BlinkMacSystemFont`, `Inter`)

### Component style
- 8px border-radius on buttons and inputs
- 12–14px on cards
- 1px borders with subtle shadows

---

## How to Open

Double-click any `.html` file — no build step, no server needed. All styles and scripts are embedded.
