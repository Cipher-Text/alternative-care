# UX & Design Audit — the doctor's daily loop

**Date:** 2026-10-10
**Status:** P0-1 (PDFs) and P0-2/P0-3 (mobile navigation and overflow) fixed 2026-10-10 — see "Mobile fixes" at the end.
**Scope:** patient → appointment → prescription (build, issue, PDF) → payment, as a doctor
(`dr.rahman@example.com`), against the local build.
**Method:** browser session at phone (375×812), desktop (1024×768), light/dark; automated checks
for horizontal overflow, tap-target size, labels and heading structure; reading the code behind each
finding. Findings below are **verified**; what was **not** covered is listed at the end.

Severity: **P0** blocks real use · **P1** serious, fix before real clinics · **P2** polish.

---

## P0 — blocks real use

### 1. Prescription and invoice PDFs are placeholders — **FIXED 2026-10-10**

> Real PDFs now render server-side (WeasyPrint, bilingual labels, Bengali shaping verified,
> VOID stamp, multi-page tables). `GET /prescriptions/{id}/pdf` and
> `GET /payments/invoices/{id}/pdf`; the old POST `generate-pdf` endpoints and the fake
> `storage.example.com` URLs are gone. Original finding kept below.
`PrescriptionService.generate_pdf` (`backend/app/modules/prescription/service.py:242`) and the
invoice equivalent (`backend/app/modules/payment/service.py:~482`) build **no document**. They store
and return `https://storage.example.com/<id>.pdf`. The UI (`usePrescriptions.ts`) then toasts
**"PDF generated successfully"** and opens that dead link.

Why it matters: a prescription that cannot be printed or handed to a patient is not usable, and the
success message is actively misleading. WeasyPrint is already installed in the backend venv.

Fix: render server-side (clinic header, doctor name/degrees/registration number, patient, items,
advice, date, signature line), embed a font with Bengali glyphs, store in MinIO, serve as a real
download, and make the toast reflect reality. Same for invoices. **Effort: M.**

### 2. No navigation on phones
The sidebar is `hidden md:flex` (`components/layout/Sidebar.tsx`) and the header has no menu button.
At 375px the page had **zero visible links** — only language, theme and avatar. A doctor on a phone
can only move around through the dashboard shortcuts.

Fix: a slide-over drawer (hamburger in the header) or a bottom tab bar for the 4–5 daily
destinations. **Effort: S.**

### 3. Horizontal overflow at phone width on 8 pages
Measured against the real device width (note: on mobile the browser widens the layout viewport, so
`innerWidth`-based checks hide this):

| Page | Overflow at 375px |
|---|---|
| `/prescriptions` | 366px |
| `/prescriptions/[id]` | 331px |
| `/payments` | 225px |
| `/profile` | 181px |
| `/patients/[id]` | 175px |
| `/payments/invoices` | 144px |
| `/prescriptions/new` | 121px |
| `/appointments` | 71px |

No overflow on: dashboard, patients list, new patient, new appointment, medicines.

Common causes: page-header rows (`flex items-center justify-between` with a title and one or more
buttons) that never wrap, and wide tables with no scroll container. The prescription builder's
sticky action bar also squeezes its warning text into a narrow column.

Fix: one shared `PageHeader` that wraps on small screens; a responsive table wrapper
(`overflow-x-auto`) or card-list layout on mobile; stack the sticky action bar. **Effort: M.**

---

## P1 — serious

### 4. Bengali is mostly missing
- Only **8 of 104** UI files use translations; `messages/{en,bn}.json` hold just `common` (10),
  `auth` (71), `nav` (3) and `patients` (9) keys. Dashboard, prescriptions, appointments,
  payments, medicines and symptoms render in English even with the Bengali locale on.
- The UI fonts (DM Sans, Plus Jakarta Sans, `app/layout.tsx`) contain no Bengali glyphs, so Bengali
  text falls back to whatever the OS provides. Appearance will vary and may break on some Android
  and Windows devices.

Fix: load Noto Sans Bengali (or Hind Siliguri) via `next/font` and add it to the font stacks (small);
translate the daily loop first, then the rest (large). **Effort: S (font) + L (translation).**

### 5. Dark mode: primary buttons disappear
In dark mode `--primary` (15 23 42) equals `--background` (15 23 42) in `globals.css`. Measured
contrast between a primary button and the page: **1.0 : 1**. Text stays readable but the main call
to action (Add Patient, Issue Prescription…) has no visible shape. `docs/DESIGN.md` already names
Sage `#059669` for CTAs — a dark-mode primary of that family fixes it. **Effort: S.**

### 6. Dead and missing navigation
- Sidebar "Library" → `/library` returns **404** (no such page).
- Symptoms has pages but no sidebar entry for doctors.

### 7. Accessibility basics
- Every page has **two `<h1>`**: the sidebar logo ("AltCare") and the page title.
- Unlabeled inputs: patients search, new-patient form (5), appointment form, prescription search,
  and the Add-Medicine dialog (fields rely on placeholders; the visible "Dosage *" label is not
  tied to its input).
- Icon-only buttons with no accessible name (the back arrow on patient and prescription detail,
  and the new-patient form).
- Tap targets under 36px: the appointments calendar controls (Today / Back / Next / Month / Week /
  Day) and day cells.

**Effort: S–M.**

---

## P2 — polish

- Medicine autocomplete shows a **"0%"** relevance figure that means nothing to a doctor.
- Patient suggestions say "Unknown age" when date of birth is empty; consider prompting for it.
- Several empty states say "Add your first…" but the receptionist role cannot (handled separately).
- The product is called AltCare but `docs/DESIGN.md` describes a "Verdana Health" system; keep the
  tokens, rename the document.

---

## What works well
- The prescription builder is clear: patient search with autocomplete, a medicine dialog that
  searches names and aliases, required-field hints, and a sticky action bar that explains why
  Issue is disabled.
- Layout is sound on dashboard, patients list/new, new appointment and medicines at 375px.
- Primary token matches the design doc (navy `#0F172A`); heading/body fonts match the spec.

## Not covered (do not assume these are fine)
Tablet widths · keyboard-only and screen-reader use · slow networks / loading and error states ·
print stylesheets · form validation messages in Bengali · the appointment calendar's behaviour with
real data (none exists in the dev database) · invoice creation flow · admin pages.

## Recommended order
1. Real PDFs (P0-1), including the Bengali font — nothing else matters if a prescription cannot be
   printed.
2. Mobile navigation + overflow fixes (P0-2, P0-3) — one pass, shared components.
3. Dark-mode primary + Bengali font + dead nav items + a11y basics (P1-5, 4-font, 6, 7) — small, high
   value, mostly one-line changes.
4. Translate the daily loop into Bengali (P1-4), then the rest.

---

## Mobile fixes (2026-10-10)

- **Navigation:** a hamburger in the header opens a slide-over drawer (`MobileNav`, Radix Dialog:
  focus trap, Esc, screen-reader title) with the same role-aware links as the sidebar
  (`NavLinks`). It closes after navigating. The header shows the wordmark on phones.
- **Overflow at 375px:** all audited pages now measure 0px overflow (was 71–366px on eight
  pages). Fixes: header and action rows wrap (`flex-wrap`), filter rows stack, fixed `p-8` page
  padding is `p-4 sm:p-8`, tab rows scroll horizontally instead of pushing the page wider, the
  prescription builder's sticky action bar stacks on small screens, profile summary row wraps.
- **Headings:** the sidebar logo is no longer an `<h1>`; payments pages now have a real `<h1>`.
- **Nav list:** removed "Library" (404) and added "Symptoms".
- **Dark-mode primary buttons (fixed):** the dark `--primary` is now emerald-700 (`#047857`) instead
  of the page's own navy. Measured: button vs page 3.26:1 (was 1.0:1), label text 5.48:1.
- **Bengali font (fixed):** Noto Sans Bengali is loaded via `next/font` and added to the font
  stacks (Latin keeps DM Sans / Plus Jakarta Sans; Bengali glyphs fall back per character), with
  extra line height for `:lang(bn)`. Verified on the Bengali login page.
- **Still open from this audit:** Bengali *translation* (8 of 104 files translated), unlabeled
  inputs, icon-only buttons without names, calendar tap targets under 36px (third-party calendar),
  autocomplete "0%" chip.
