# Public Site — Product & Business Evaluation

**Date:** 2026-10-11
**Status:** Proposal for product-owner decision. **Phase 0 started 2026-10-11** — see §12 for what is built and what still needs a decision. Phases 1–3 are not built. Facts about the current site are
verified against the code; market claims are **assumptions** (no competitor or market research has been
done — see §9). No prices are proposed (consistent with `pricing-usage-onboarding-2026-10.md`).
**Goal being evaluated against:** (1) become known to general people, (2) convert more practitioners
into paid clinics.

---

## 1. Verdict

The public site today is a **reference catalog dressed as a marketing site**. It speaks to neither of
the two audiences that matter:

- **Patients / general public** cannot use a medicine or symptom list. Nothing on the site helps them
  decide anything, find a person, or come back.
- **Practitioners** already get the same catalog, with more detail, behind login — so the public list
  gives them no reason to sign up, and the site never asks.

Agree with the instinct: **take the medicine and symptom lists out of public view**, show their *size*
as proof, and spend the freed-up space on the three things that actually move the goal — **content**
(blog + curated video), a **practitioner directory driven by the paid plan**, and a **working signup
funnel**. The funnel is the part most likely to be underestimated; see §3.

---

## 2. What exists today (verified)

| Area | Reality |
|---|---|
| Public pages | Home, About, For Practitioners, Pricing, Institutions, Medicine directory, Symptom directory. |
| Content volume | 190 medicines, 77 symptoms, 77 institutions (home-page counters, live from the API). |
| Medicine/symptom pages | Full browse + search + paging, unauthenticated; each card links nowhere (no detail page). `GET /api/v1/public/medicines` and `/symptoms` are open, paginated and scrapable; `/medicines/{id}` returns the full record. |
| Rendering / SEO | Directory pages are client-rendered; the whole site shares one `<title>`; no sitemap, no robots, no Open Graph/share cards, no structured data. |
| Signup | Email/password signup page (`/register`) and a Google path exist, with a pending-approval state and lifecycle emails (built 2026-10-10, step 1 of `pricing-usage-onboarding-2026-10.md`). Not re-tested end to end for this document. |
| Pricing page | Rendered from the admin-configured plans; "Get Started" goes to `/register?plan=<key>`. Prices are not shown (none approved). |
| Trust / legal | No medical disclaimer, privacy policy, terms, contact page, testimonials, or practitioner/clinic count. |
| Analytics | None (we cannot currently say how many people visit or where they drop). |
| Practitioner directory | Not built. Decided in ADR-008 (read-only view over tenant data, opt-in flag) and gated on ≥20 public profiles. |
| Content/CMS | Not built. Track C in `future-scope-2026-09.md`, sequenced *after* the AI assistant, with that file's own note: "revisit if content-driven acquisition becomes the near-term growth priority." **It now is.** |

---

## 3. The funnel must be proven before traffic is bought

Signup now exists, but the path from "convinced visitor" to "paying clinic" has gaps that content and a
directory would multiply visitors into: **no price or trial on the pricing page**, a manual
**admin-approval wait** for every new tenant (a drop-off point unless approval is fast and the wait is
explained), no onboarding after first login, and no way to pay for a plan at all (no billing). Before
spending effort on traffic, walk the funnel end to end as a stranger and measure where people stop.
Those fixes are cheaper than any new content and decide whether extra visits turn into revenue.

---

## 4. The two audiences and one flywheel

```
 Patients find AltCare via blog / video / search  ──►  see verified practitioners nearby
        ▲                                                         │ contact / request
        │                                                         ▼
 More content, more doctors writing it  ◄──  Practitioners on Plus get listed + get patients
        ▲                                                         │ see "N patients found you"
        └────────────── renewals & word of mouth ◄────────────────┘
```

Patients are the *free marketing channel*; practitioners are the *customer*. Content earns the first
visit, the directory turns visits into a measurable benefit for paying clinics, and that measurable
benefit (leads) is what justifies and renews the subscription. The medicine/symptom catalog does not
appear in this loop — it belongs to the product, not the shop window.

---

## 5. The medicine and symptom lists

### Recommendation
Remove both lists from public navigation and from the public site. Keep **numbers** on the home page.
Keep the catalog as the product's gated value (Free and above, after signup).

### Why (in order of weight)
1. **Wrong audience.** A list of remedy names and symptom terms helps a practitioner, not a patient.
2. **Liability.** A public "symptom → remedy" browse invites self-medication. The project already
   treats content that makes treatment claims as needing medical-reviewer sign-off (Track C, AI
   assistant §7); an open catalog bypasses that posture. Legal review of health-claim and advertising
   rules in Bangladesh is needed before any public treatment content (not assessed here).
3. **It gives away the thing that converts.** The curated catalog is a reason to sign up. Public, it is a
   reason to just use the site and never register — or to copy it.
4. **Scraping.** The open API serves the full catalog page by page. Admin-curated data is the one asset
   a competitor cannot rebuild cheaply.
5. **No conversion path.** Cards link nowhere and carry no call to action.
6. **Weak SEO anyway.** Thin, client-rendered, identical-format pages rank poorly; they will not be the
   traffic engine.

### Honest counter-argument
Single-medicine pages could capture long-tail searches ("Arnica 30C uses"). That is real traffic, but
it is also exactly the self-medication content in point 2. If wanted later, publish a **reviewed
teaser page per medicine** (name, discipline, general description, evidence label) with dosage,
potency and symptom mappings behind signup — as an editorial product, not a catalog dump.

### About showing numbers
Good for social proof, with a caveat: **190 medicines / 77 symptoms is modest, and a small number can
hurt more than help.** Lead with numbers that grow and mean more to the reader: *practitioners
on the platform, clinics, prescriptions issued, disciplines covered*; show catalog counts once they
are clearly impressive, or phrase it as "a growing library". Never show a number that is not live.

### What changes technically
- Public medicine/symptom *list and search* endpoints: remove or restrict to a counts endpoint.
  Rate-limit whatever remains public. (Verify nothing else — e.g. the prescription builder — relies on
  the unauthenticated routes before removing them.)
- Delete the two public pages and their nav/footer links; keep the institutions page only if
  decided in §6.5.

---

## 6. Your proposed additions — evaluated

### 6.1 Blog on alternative medical treatment — **Yes; this is the traffic engine**
- **Why it works:** it is the only item here that earns first-time, non-brand search and social visits
  from general people.
- **Make it Bengali-first.** Bengali health content is under-served relative to demand (assumption —
  validate in §9) and Bengali search has less competition than English.
- **Authors are doctors.** A byline plus a link to the author's profile turns the blog into
  practitioner promotion — a reason for doctors to write and to subscribe (see 6.3). It also solves the
  content-supply problem for a solo team.
- **Safety rules (non-negotiable):** medical-reviewer sign-off before publish (already the Track C rule);
  no dosing or "cure" claims; an evidence label per article (traditional use vs. studied); a standing
  disclaimer; a visible "when to see a doctor".
- **Topic shape:** conditions explained, herbs and remedies in context, lifestyle, myth-vs-evidence,
  "what to expect at a first visit". Avoid "treat X with Y" instructions.
- **Cost:** an editorial workflow (draft → review → publish), an author profile, and ongoing
  review time. The review step is the real recurring cost; decide who owns it before launch.

### 6.2 Famous YouTube videos — **Yes, as curation, with care**
- Embed via the official player (privacy-enhanced domain, lazy-loaded behind a thumbnail so pages stay
  fast on mobile data). Do not download or re-host.
- **Curate, don't aggregate.** "Famous" is not the same as "accurate"; popular alternative-medicine
  videos are a known misinformation vector. Apply the same reviewer check as articles.
- **Better than famous videos: practitioners' own channels.** Featuring a Plus doctor's video on their
  profile is a perk that sells the plan and fills the library at no production cost.
- Later: an AltCare channel (short Bengali explainers) once the review workflow exists.
- Embeds of a third party's video are a lighter lift than articles, so this can ship first.

### 6.3 Doctor list from Plus subscription — **Yes; this is the monetisation lever**
- It gives Plus a **visible, measurable return**: "listed in front of patients" and "N contacts this
  month". That is a stronger reason to pay than "payments & invoicing".
- Consistent with ADR-008: an opt-in public flag over real tenant/doctor data, not a second profile table
  that drifts out of date.
- **Two separate ideas, do not merge them:**
  - *Verified* = an admin checked the registration/credentials. Should be free and required to appear.
    It is the trust signal.
  - *Listed / featured* = a plan benefit. Suggested shape (structure only): Free — no public
    listing; Plus — full profile listing + contact; Pro — priority placement and richer profile.
  Paid placement without a verification layer looks like pay-to-play and damages the trust the whole
  strategy relies on. No public star ratings (already decided in the 2026-09-28 addendum).
- **Contact mechanism v1 (no patient accounts needed):** click-to-call / WhatsApp, plus an
  "request an appointment" form that emails the clinic and is counted. Real online booking needs the
  patient-identity ADR the addendum already requires — don't smuggle it in.
- **Cold start:** ADR-008 gates this at ≥20 public profiles. Seed it with the clinics you can recruit
  first (offer a time-limited free listing), and let content (6.1) bring the patient side before the
  doctor side looks empty.
- **Data/consent:** doctors choose what is shown (fee, hours, location); the leads form collects patient
  phone/name — it needs a privacy policy and consent text first (§7).

### 6.4 What a PM would add that was not on your list
1. **Two-door home page.** One hero, two paths: "Find a practitioner" (patients) and "Run your clinic"
   (doctors). Today's hero is a search box into a catalog.
2. **Discipline hubs** (`/homeopathy`, `/ayurveda`, `/unani`, `/herbal`): landing pages that gather the
   articles, videos and practitioners for each discipline. They are the SEO structure and the browse
   path for patients. They depend on discipline becoming a real entity (taxonomy section of
   `future-scope-2026-09.md`).
3. **SEO foundation:** server-rendered pages, a distinct title/description per page, sitemap, robots,
   Open Graph images (Facebook/WhatsApp sharing is the main distribution channel — assumption),
   structured data for articles and practitioners. Mobile-first and light: assume mid-range phones on
   mobile data.
4. **Trust layer:** medical disclaimer, privacy policy, terms, a contact/WhatsApp number, a "how we
   verify" page, practitioner and clinic counts.
5. **Analytics:** privacy-friendly, with a defined funnel (§8). Without it none of this can be judged.
6. **Practitioner-facing proof:** a short demo (video or screenshots) of the clinic workflow, a real
   price or at least a real trial, and early-adopter quotes as soon as they exist. The For-Practitioners
   page today lists features; it does not show the product.
7. **Referral loop:** a doctor's public profile and articles carry "Powered by AltCare"; a simple
   doctor-to-doctor referral reward costs little and fits a trust-driven market.

### 6.5 Existing pages: keep, change, remove
| Page | Decision |
|---|---|
| Medicine directory | **Remove** (§5). Replace with a counter on Home. |
| Symptom directory | **Remove** (§5). |
| Institutions directory | **Keep, de-emphasise.** Useful to students/curious visitors, a small SEO asset, almost no revenue effect. Move to the footer; low maintenance priority (it goes stale — see future-scope). |
| Pricing | **Keep; fix.** Show real prices or a real trial, a working Get Started, and the *listing* benefit per plan. |
| For Practitioners | **Keep; rebuild** around proof (demo, outcomes), not feature bullets. |
| About | **Keep; extend** with who is behind it, verification approach, contact. |
| Pharmacy directory | Already practitioner-only (login). Keep it that way — it is a retention perk. |

---

## 7. Risks and constraints

| Risk | Why it matters | Mitigation |
|---|---|---|
| Health-claim liability | Public treatment content may make claims; regulators and platforms care. | Reviewer sign-off, no dosing/cure claims, evidence labels, disclaimer; legal review before launch. |
| Pay-to-play perception | Paid listings can undermine trust. | Verification is free and separate from placement; label sponsored/featured. |
| Cold-start (directory) | An empty directory looks dead. | ≥20 gate, seeded free listings, content first. |
| Review bottleneck | Every article and video needs a reviewer. | Name the owner now; start with a small publishing cadence. |
| Lead data (patient phone/name) | Privacy and misuse. | Consent text, minimal fields, retention rule, clinic-only access. |
| Content freshness | Stale content erodes trust and SEO. | Review dates on every article; owner per discipline. |
| Solo-developer capacity | Everything above competes with the Stage 3–4 plan. | §10 sequencing and explicit displacement. |

---

## 8. How to know it is working

Define before building; targets need your baseline data and are intentionally not invented here.

- **Awareness (general people):** unique visitors, organic-search share, returning visitors, shares of
  articles/videos, Bengali vs. English split.
- **Directory:** listed practitioners, profile views, leads per listed doctor per month.
- **Conversion (practitioners):** visit → signup, signup → approved, approved → first prescription
  ("activated"), activated → paid (Plus), and *why they paid* (ask). Churn and renewal at 3 and 6 months.
- **Quality:** share of articles reviewed within SLA; reported content issues.
- **Leading indicator of the whole thesis:** do doctors with listings renew more than doctors without?

---

## 9. What was not done (assumptions to validate)

- No competitor or market research (existing Bangladesh directories, telehealth apps, practice-management
  tools, willingness to pay, Bengali search volume). The conclusions above are reasoning from the code
  and general product practice, not from market data. Recommended before committing to the content
  plan: 1–2 days of competitor review and ~10 practitioner interviews on what would make them pay.
- No legal review (health-content and advertising rules, data protection for leads).
- Revenue effect of listing-as-Plus-benefit is a hypothesis; §8's last metric tests it cheaply.

---

## 10. Suggested sequencing (and what it displaces)

| Phase | Work | Effort | Notes |
|---|---|---|---|
| **0 — Make the funnel work** | End-to-end funnel test and fixes (approval speed/wording, first-login onboarding); real price or trial on Pricing; a way to pay (billing); per-page titles + sitemap + robots + share cards; disclaimer/privacy/terms; analytics; remove public medicine/symptom lists; Home rebuilt as two doors with live practitioner/clinic counts | M | Do first; nothing else pays off until it works. |
| **1 — Content** | Minimal CMS: article (title, Bengali body, discipline, author, evidence label, reviewer, review date), draft→review→publish, video embed block; publish a first batch (~10) with 2–3 friendly practitioners | M–L | Track C pulled forward; reviewer owner required. |
| **2 — Practitioner directory** | Verification admin flow (free), opt-in listing flag, profile page (ADR-008 field list), contact/"request appointment" with lead counting, "leads this month" in the doctor's dashboard, entitlement `feature_directory_listing` in the plan config | L | Gated at ≥20 profiles; recruit before launch. |
| **3 — Growth** | Discipline hubs, teaser pages (reviewed), referral loop, own video channel, patient accounts ADR if booking is wanted | L | Decide from Phase 0–2 metrics. |

**What this displaces:** `future-scope-2026-09.md` sequences Track C and the directory *after* the AI
assistant (Stage 4). Because the stated goal is now popularity and paid clinics, this document
recommends **moving Phases 0–2 ahead of Stage 4** and treating the AI assistant as a Pro-tier
differentiator that follows. That is a real reordering of the roadmap and should be an explicit
decision, not a side effect.

---

## 11. Decisions needed from the product owner

1. Approve removing the public medicine/symptom lists (and restricting the open API) — yes/no.
2. Who reviews articles and videos, and at what cadence? (Without a named owner, Phase 1 stalls.)
3. Directory benefit: listing starts at **Plus** (as proposed) or a minimal listing for everyone?
4. Is a reordering ahead of the AI assistant (§10) accepted?
5. Contact model for v1: click-to-call/WhatsApp + request form (proposed) vs. waiting for patient
   accounts.
6. Primary language for launch content: Bengali-first (proposed) or bilingual from day one.
7. Willing to do the market/legal checks in §9 before Phase 1?

---

## 12. Phase 0 progress (2026-10-11)

**Built**
- Public medicine and symptom lists removed: both pages deleted, nav/footer links removed, and the
  open API endpoints (`/public/medicines*`, `/public/symptoms*`) removed. `GET /api/v1/public/stats`
  returns counts only (medicines, symptoms, institutions, clinics, practitioners; cached 5 min).
  Route count 159 → 154.
- Home rebuilt: practitioner-first hero (Get Started / See pricing / Sign in), "two doors" (patients
  door is an honest *Coming soon* — the directory and articles do not exist yet), disciplines, closing CTA.
  Live numbers show only when large enough to help (practitioners/clinics ≥ 10, medicines ≥ 100,
  symptoms ≥ 50, institutions ≥ 50) and only when at least two qualify.
- SEO basics: per-page titles and descriptions (en/bn), title template, `sitemap.xml`, `robots.txt`
  (private areas disallowed), a generated share image, canonical base via `NEXT_PUBLIC_SITE_URL`.
- Legal pages `/privacy`, `/terms`, `/disclaimer` (en/bn), linked from the footer; terms/privacy
  consent line under the signup form. **Working drafts — need legal review**, and the statements in
  them (e.g. "not used for advertising", cookie use, no deletion timeline) must be confirmed by the owner.
- Optional cookieless analytics (Plausible) behind `NEXT_PUBLIC_ANALYTICS_DOMAIN`; nothing loads when unset.
- First-run checklist on the doctor dashboard (add patient → schedule → issue prescription), hidden
  once done and for receptionists.

**Still needs a decision or an owner (not built)**
- Real prices or a trial on Pricing: prices are set in `/admin/plans`; the page already renders them.
  No price is proposed here.
- Subscription billing (paying for a plan) — not built; needs a payment-method and invoicing decision.
- Approval wait: signup, pending state and emails exist, but every tenant still waits for manual
  approval; decide the target turnaround and wording. Email sending is a no-op locally until
  `EMAIL_PROVIDER` is set, so the full signup email path was not exercised.
- `NEXT_PUBLIC_CONTACT_EMAIL`, `NEXT_PUBLIC_SITE_URL`, analytics domain: set per deployment.
- Not exercised: a stranger-eyes end-to-end signup walkthrough on a deployed environment.

---

## 13. Phase 1 progress (2026-10-11)

**Built**
- `articles` table and `app/modules/content` (migration `e7b2a9c4d1f3`): kind (article / video), discipline,
  evidence label (general info / traditional use / limited evidence / studied), English and Bengali
  title, summary and Markdown body, YouTube id, author, reviewer credit, review and re-review dates.
- Workflow: draft → in review → published. Doctors and admins write; doctors see only their own and can
  edit only drafts; **only an admin can publish** (records the reviewer's public credit), return with a note,
  or unpublish. Submit requires a title, summary and body (or a video link). Receptionists and operators
  have no access. 10 tests in `tests/integration/test_content_routes.py`.
- Public: `/articles` (server-rendered list, filters, paging) and `/articles/[slug]` (Markdown without raw
  HTML, evidence label with plain explanation, reviewer and next-review date, overdue notice, medical
  disclaimer, "when to see a doctor", JSON-LD, click-to-load `youtube-nocookie` embed); sitemap includes
  published articles. Authoring UI at `/content` (list, editor with preview, review actions), "Articles"
  in the doctor and admin nav.

**Not done / needs you**
- **No articles are published.** The first batch (~10) must be written and reviewed by people you trust;
  nothing here writes or reviews medical content.
- **Who reviews** is still undecided. Today any platform admin can publish, including their own article;
  a second-reviewer rule is not enforced (decide whether to require it).
- Bengali strings written by us have had no native-speaker review.
- Not exercised: the editor dialogs and read-only states beyond a smoke check; video playback.
- Doctors authoring is not tied to a plan; decide whether it is a Plus benefit (strategy §6.3).

---

## 14. Phase 2 progress (2026-10-12)

**Built**
- **Listing** (`practitioner_listings`, migration `f3c8d5a1b9e4`): one opt-in public listing per clinic over
  real tenant data (ADR-008): headline/bio (en, bn), languages, hours, availability, and what to show
  (fee, phone, WhatsApp, call-back requests). Name, qualifications, registration *body* and address
  always show when listed; the registration **number** never does. No ratings.
- **Gates — all must hold:** doctor opted in, **admin verified** the clinic (free; `tenants.is_verified`
  now has an admin endpoint with an audit note), clinic approved/active, **plan includes
  `feature_directory_listing`** (new entitlement; default Free off, Plus and Pro on, editable in the
  plan config), and a bio exists. Verification and plan are separate gates so paying never replaces
  verification. The doctor's page shows exactly which gate is missing.
- **No launch threshold (decided 2026-10-15):** `/practitioners`, the nav link and the sitemap show whatever is
  visible: one profile shows one, a hundred show a hundred. The earlier "hidden until 20 profiles" rule
  (`DIRECTORY_MIN_PROFILES`, with a teaser page) was removed. Quality comes from the verification gate, not a count.
- **Contact v1:** `tel:` / WhatsApp taps (counted) and a "request a call back" form with mandatory consent,
  a honeypot and an IP rate limit; stored per clinic, emailed to the clinic (best effort), inbox with
  New/Contacted/Closed, month-to-date numbers on `/directory` and a card on the doctor dashboard.
  Explicitly *not* booking (needs the patient-identity ADR).
- Public pages: `/practitioners`, `/practitioners/[slug]` (JSON-LD `Physician`), `/verification`; privacy
  page has an "Appointment requests" section.
- 12 tests in `tests/integration/test_directory_routes.py`; full suite 839 passed.

**Not done / needs you**
- **Directory plan benefit is still a default, not a decision:** Plus+ (as proposed in §6.3). Change it in
  the plan config if you decide on a minimal free listing.
- **Verification is manual and undefined in practice:** who checks documents, against which registers
  (no central Unani/Ayurveda register exists — see future-scope), and how long it takes. The admin UI only
  records a decision and a note; it does not show the doctor's uploaded documents (degree certificates have
  a `certificate_url` field, no upload flow yet).
- **Legal review needed** for the privacy "Appointment requests" section (retention period and legal basis
  are left as "to be confirmed"), and for the consent wording.
- No photo/upload for profiles (clinic logo only); no map embed; no "Featured/Pro priority" ordering
  (deliberately skipped — it needs a clear "sponsored" label first).
- Recruiting: nothing shows publicly until 20 verified, opted-in clinics exist. The list endpoint resolves
  the plan gate per clinic (fine for hundreds; cache or denormalise if it grows).
- Bengali strings have had no native-speaker review. Operators cannot verify (admin only).
- Seeded dev address shows "Debidwar, Dhaka, Dhaka" — an upazila/district mismatch in seed data.
