# AltCare — Future Scope: Directory & Content (Track D / Track C)

**Date:** 2026-09-23
**Status:** Direction decided, not scheduled. Nothing here has a date.
**Relationship to `revision-2026-09.md`:** that document is active — Stages 0–4 are dated, gate real work, and D1–D10 are architecture decisions in force now. This document is deliberately separate: everything below sits behind Stage 4 or later, and mixing "ships in weeks" with "no date yet" at equal weight in one document defeats the point of gate-based sequencing. Read `revision-2026-09.md` first; this is what comes after it, not instead of it.

---

## Why this exists

The product owner's scope for AltCare is wider than the clinic-management core: practitioner/clinic/college directories and editorial content (articles on conditions, herbs, medicines), alongside the already-planned book library. A feature-by-feature audit against the checked-in code (95 named items) found 38 (40%) with zero footprint anywhere in the repo — no model, no roadmap line, not even a rejected-idea note. That's the gap this document closes: direction and sequencing, decided once, instead of re-litigated every time the topic comes up.

Per `revision-2026-09.md` §9's own rule ("re-adding a cut item requires writing down what it displaces"), the same discipline applies to *adding* scope — nothing below is free, and each item names what it costs.

---

## Track D — Directory

**Practitioner + Clinic Directory.** Already decided, not new: `revision-2026-09.md` §2.1 already gates this on ≥20 public profiles, produced by Stage 3's public pages. What's new here is *how* it's built when that gate is met: a read-only public view over existing `Tenant`/doctor `User` data (an opt-in "publicly listed" flag on Tenant), not a new profile table a tenant fills out separately. A parallel table would drift from the operational record the moment a clinic updates its address in Settings and the public listing doesn't move — the same class of bug the D1 keystone migration exists to prevent, one layer up. Full reasoning, including the alternative considered and why it's the one call here with real reversal cost: `docs/architecture/adr/008-directory-from-tenant-data.md`.

**College / Institution Directory.** New, not previously scoped anywhere. Admin-curated platform catalog data, same shape as the existing Medicine/Symptom global catalog — a college, its type, disciplines taught, location, and courses offered. Unlike the practitioner directory, this has no supply cold-start problem: an admin can seed a first batch of known institutions on day one, so it doesn't need the ≥20-profile gate. It's sequenced *with* the practitioner directory anyway, for one reason — shipping the directory pattern once, covering both, costs less than building it twice.

**Cost of maintaining accuracy:** a college listing has no live source to stay in sync with, unlike the practitioner directory. It goes stale unless someone checks it periodically. That's an ongoing admin cost this feature creates, not a one-time build cost — worth deciding who owns it before this ships, not after.

---

## Track C — Content/CMS

Editorial articles about conditions, herbs, and medicines, with one mandatory step: a medical reviewer signs off before an article can go public. Same clinical-liability posture as the AI assistant in `revision-2026-09.md` §7 — content making treatment claims carries that risk whether a model or a person wrote it, and gets reviewed the same way.

**Sequencing:** after the AI assistant (Stage 4), not parallel with it. This is a business call, not a technical one — nothing about content/CMS requires the AI assistant to exist first. It's ordered this way because the AI assistant is the product's stated moat and Track K's payoff, and a solo developer's time is the actual constraint. **Revisit this ordering if content-driven customer acquisition becomes the near-term growth priority** — if it does, this can move ahead of the AI assistant without re-doing anything above.

---

## Knowledge taxonomy — bundled into a future Stage 2 migration, not its own stage

Three gaps in the existing Medicine/Symptom catalog, meant to land in the *same* migration wave as `revision-2026-09.md`'s D1 keystone fix when that work is actually scheduled — splitting them into a separate later stage means doing catalog-table schema surgery twice instead of once:

- **Discipline as a real entity, not a string.** Today "homeopathy/ayurveda/unani/herbal" is a free-text array on Tenant and a free-text field on Medicine/Book, in both places uncontrolled. Promote it to a referenced catalog table. A fifth discipline today means grepping for string literals across the codebase; with a table, it's one admin-curated row.
- **Condition, distinct from Symptom.** A canonical diagnosis (e.g. "Migraine") is not the same thing as a patient-reported complaint (e.g. "headache") — Symptom already models the latter well and shouldn't be stretched to cover the former.
- **Therapy, distinct from Medicine.** A non-substance intervention (e.g. a specific procedure) is a different kind of thing than a substance/remedy, and Medicine's fields (dosage, potency) don't fit it.
- **One shared evidence/reference subsystem, not five separate features.** "Medical Reference Management," "Evidence Classification," "Evidence-Based Content Labelling," "Traditional Knowledge Labelling," and "Reference & Citation Tracking" were named as five items in the original scope list. They're one subsystem viewed from five angles — a bibliography of sources, and a way to say how strong the evidence behind a claim is. Building five separate features here would mean five overlapping CRUD surfaces answering the same underlying question.

**Explicitly rejected:** a separate "Herbal Medicine Library," distinct from the existing Medicine catalog. Medicine already covers all four disciplines; a herbal-only table would be the same mistake D1 already fixed (a parallel `global_medicines` table) at smaller scale.

**What's deliberately not decided here:** exact table names, columns, and enum values. That level of detail is real design work best done at the start of whichever stage actually picks this up — locking it in now, before real requirements have surfaced from building Track D/C, would mean guessing and then redoing it. The decisions above (discipline is an entity; condition and therapy are distinct from symptom and medicine; evidence is one subsystem, not five) are the part worth deciding early, because reversing *those* later is expensive. Column names are not.

---

## What this document is not

Not a commitment to build any of this by a date. Not a full architecture spec — that gets written when a stage here actually starts, informed by whatever's true at that point. It exists so that "directory," "content," and "taxonomy" have one answer instead of being re-decided from scratch (or left undocumented) every time they come up.
