# ADR 009: Patient identity across clinics: an optional, phone-verified identity that clinics link to by consent, never by automatic matching

- Status: **Accepted by the product owner on 2026-10-13; Phase 1 may be built.** The privacy/legal review and the
  other open items below must still be completed **before this goes live with real patients** (see "Before building").
- Date: 2026-10-13
- Related: ADR 002 (platform vs tenant data), `docs/architecture/multi-tenancy.md`,
  `docs/planning/future-scope-2026-09.md` (the 2026-09-28 addendum rejected public booking until this exists),
  `docs/planning/public-site-strategy-2026-10.md` §6.3, `docs/planning/billing-credits-spec-2026-10.md`.

## Context

Today a patient is a record a clinic keeps (`patients`, tenant-owned: name, date of birth, gender, phone, email,
address, medical history). A person who visits three doctors exists as three unrelated records. There is no patient
login, and one clinic can never see another clinic's data (row isolation by `tenant_id`, plus PostgreSQL row-level
policies as a second layer). That isolation is a hard requirement and this ADR does not weaken it.

The product now wants patients to be able to (eventually) book, see their own records, and move between doctors
without re-typing everything. The constraints are Bangladeshi realities, stated by the product owner:

- **OTP is not always possible.** The patient may not have the phone with them, may use a feature phone, may not
  read well, or may have no phone at all. Care must never be blocked by it.
- **Phones are shared** (a mother's phone is used for her child and her own mother) and **numbers get recycled**.
- **Patients give inconsistent details** to different doctors (spelling, age, even a different number).
- **The patient may not be able to use an app.** Anything that needs one excludes many users.

## Decision

1. **Two different things: a clinic's record and a platform identity.** A clinic's patient record stays exactly as it
   is: tenant-owned, always creatable by staff with no OTP. A new platform-level **person identity** is separate and
   optional. It holds who the person is and which clinic records belong to them; it holds **no clinical data**.
2. **Three levels of certainty** (a record carries its level; nothing ever silently upgrades):
   - **Level 0, clinic-entered:** details as the patient said them. Works everywhere, no OTP. Stays inside that clinic.
     The phone is kept as unverified contact information and is **never used for matching**.
   - **Level 1, phone-verified:** the patient read out an SMS code at the clinic, proving they hold the phone. An
     identity is found or created for that verified phone and the clinic's record is linked to it.
   - **Level 2, self-registered:** the patient later signs up with a phone code and can see their linked records.
3. **Linking happens only with the patient's consent**, by one of three routes: the in-clinic code (level 1), a
   **claim code** the clinic gives the patient for an existing record (printed on the prescription or sent by SMS),
   or a clinic-sent **invite link** for after the visit. Linking is never inferred.
4. **No automatic matching, ever.** Not on name, age, address, or an unverified phone. A wrong match would show one
   person's health data to a stranger, which is worse than a duplicate record.
5. **Family profiles under one phone.** The verified phone is the **account holder**; it holds up to about 10
   **profiles** (self, child, spouse, parent), each a separate person for records and consent. A profile is marked
   **dependent** (a child under 18, or someone who cannot act for themselves) or **adult**. The holder acts as
   guardian only for dependents. Another adult's data is never visible to the holder without that adult's own
   verification or consent. Two profiles with the same name and date of birth under one phone are one profile.
6. **What a link shares:** only the person's **basic details**: name, age or date of birth, gender, area. Never
   diagnoses, prescriptions or notes. **Clinical sharing between clinics is a separate, later feature** (below), always
   explicit, per clinic, time-limited and revocable. A clinic's record is never overwritten by identity data;
   differing values are shown side by side and every field remembers who entered it (clinic or patient).
7. **Consent is tied to reading out the code, and is specific, voluntary, recorded and revocable** (details in
   "Consent design"). Refusing costs nothing: the visit proceeds at level 0.
8. **AltCare (the platform) pays for the OTP SMS** (decided by the product owner). To keep that cost tied to paying
   clinics, verifications are limited by a **per-plan entitlement** (a new `monthly_patient_verifications` limit in
   the plan config; the values are an open decision below), on top of the abuse limits in "OTP rules".
9. **A clinic learns that an identity exists only after its staff has just passed an OTP for that phone.** There is
   no unauthenticated lookup, so the system cannot be used to find out who has a profile. At the clinic, staff type
   the visitor's name and see only a matching profile (or add a new one); the whole family list is not shown.
10. **Self-registration comes later and never trusts the phone alone.** A new account sees only records linked by
    consent. To claim an **older** record it also needs the clinic's claim code, which defeats a recycled number
    being used to read a previous owner's history. A patient's phone can be changed only after a fresh verification
    of the new number and a check against the old identity.
11. **Tenant isolation is unchanged.** The patient portal is a separate sign-in context (no tenant, no clinic role).
    It can read a clinic's data only through a link row and only for that linked profile's own records, through
    patient-specific services that apply the same per-record filter. It never uses a clinic's access, and no clinic
    credential can reach the identity tables except through the OTP-gated lookup in rule 9.

## Flows

| Situation | What happens |
|---|---|
| First visit, patient reads out the code | Identity created for the verified phone; the clinic's record is linked; basic details become the verified profile. |
| Second clinic, patient reads out the code | Identity found; the clinic confirms "is this you?" in person; basic details prefill; the clinic's own record is created and linked. |
| No code (no phone, feature phone, forgot it) | Staff enter details; record stays level 0; phone kept as unverified contact; nothing links; the visit is not delayed. The clinic can send an invite link later. |
| Second clinic, different details, no code | A separate record is made. We cannot know it is the same person, and that is safe: it is today's behaviour. |
| Second clinic, different details, with a code | Identity found by the verified phone; the clinic's record keeps what staff typed; differences are shown, never merged or overwritten. |
| Shared phone | One account holder, several profiles; staff pick or add the right person; consent and links are per profile. |
| Recycled number | A new holder passing the OTP gets only what links after that point; older records need the clinic's claim code; clinical history is never exposed on the phone alone. |
| Patient revokes | The clinic's link is removed; the clinic keeps its own medical record (it may have to retain it); the patient's identity no longer prefills for that clinic. |

## Consent design (to be reviewed by a native speaker and a lawyer)

- **What the patient agrees to**, in plain Bengali, read aloud by staff: creating or finding their AltCare profile
  for this phone; sharing their basic details (name, age, gender, area) with this clinic; linking this clinic's record
  to the profile. Medical history is explicitly not shared with any other doctor without their permission.
- **The act of consent is reading out the code.** No pre-ticked boxes. The screen shows the script, and the staff
  member confirms the patient was told; that confirmation is recorded.
- **The SMS stays short** (Bengali is 70 characters per segment, so long text multiplies the cost): the clinic name,
  the code, and "share only if you agree". The fuller wording is the script and a notice at the clinic.
- **An immutable consent log:** which person, clinic, staff member, date and time, the version of the wording, the
  channel, and the verified code's reference.
- **Revocation** is possible from any later visit and from the patient's own account once they have one. Children's
  consent is given and revoked by the guardian holder.
- **Data minimisation and purpose limits:** identities hold only phone, name, date of birth or age, gender, area and
  profile relationships. Retention and deletion of identities that have no links is an open question below.

Draft wording for review (not final):

- Script: "আমরা আপনার ফোনে একটি কোড পাঠাচ্ছি। কোডটি বললে আপনি রাজি হচ্ছেন যে [ক্লিনিক]-এর সঙ্গে আপনার মূল তথ্য (নাম, বয়স, লিঙ্গ, এলাকা) AltCare প্রোফাইলে যুক্ত হবে। আপনার চিকিৎসার তথ্য আপনার অনুমতি ছাড়া অন্য কোনো ডাক্তারের কাছে যাবে না। রাজি না হলে কোড দেবেন না, তবুও চিকিৎসা পাবেন।"
- SMS: "AltCare: [ক্লিনিক] আপনার তথ্য যুক্ত করতে চায়। কোড 482913। রাজি হলে কোডটি বলুন।"

## OTP rules (the platform pays, so abuse is a cost problem)

6-digit code, 5-minute expiry, single use, at most 3 attempts, a cooldown per phone, a maximum number of sends per
phone per hour, a daily cap per clinic, a limit per IP, and the plan entitlement above. Codes are stored hashed.
Cost reference: about 0.4 to 0.64 taka per SMS at current provider rates, so 100 clinics verifying 30 patients a day
is roughly 45,000 taka a month, which is why verification is capped per plan.

## Data model (a sketch, not final)

All platform-level (`tenant_id` NULL) and treated as personal data:

| Table | Holds |
|---|---|
| `person_accounts` | Verified phone (normalised, stored so it can be looked up but not displayed in logs), verified at, status. |
| `person_profiles` | Under an account: display name, date of birth or age, gender, area, relationship, dependent or adult, status. |
| `patient_links` | `tenant_id`, clinic `patient_id`, `profile_id`, method (clinic code, claim code, invite), status (linked, revoked), consent event. |
| `consent_events` | The immutable log described above. |
| `otp_challenges` | Hashed code, phone, purpose, clinic, attempts, expiry, outcome. |
| `claim_codes` | Hashed code for one clinic record, expiry, used flag. |
| `data_shares` (later phase) | An explicit, time-limited grant from a profile to a clinic for named categories of records. |

The clinic's `patients` row gains a nullable link and per-field provenance (clinic-entered or patient-verified) but
keeps all its current columns and behaviour.

## Alternatives considered and rejected

- **Automatic matching by name, age and phone.** Fast, and wrong often enough to leak health data to strangers.
- **One global patient record shared by every clinic.** Breaks tenant isolation and ADR 002.
- **Require an OTP for every patient.** Blocks care for patients without a phone or a signal. Verification must be an
  upgrade, not a gate.
- **National ID as the identifier.** Collecting it is sensitive, many patients (children) have none, and it adds legal
  exposure. Not used.
- **App-only login.** Excludes feature-phone users. SMS works on any phone.

## Phasing

1. **Identity and linking:** accounts, OTP at the clinic, profiles, consent log, claim codes, the clinic-side prompt,
   per-plan entitlement. No patient login yet.
2. **Patient self-registration and a read-only view** of their own linked appointments, prescriptions and receipts.
3. **Appointment requests with clinic confirmation**, replacing the call-back form.
4. **Patient-controlled sharing between clinics** (referrals with history) using `data_shares`.

Each phase ships only with tests that prove a clinic cannot reach another clinic's data and a patient cannot reach
another patient's.

## Consequences

- AltCare now stores personal data (phone, names) **outside any clinic**. That is a new data-protection and breach
  surface, with obligations for retention, deletion requests and incident handling.
- OTP SMS becomes a platform cost that scales with usage, controlled by the plan cap and the abuse limits.
- Duplicate records within and across clinics still exist for unverified patients; that is accepted. A
  within-clinic merge tool is a separate, later feature.
- A recycled phone number remains a residual risk, reduced (not removed) by claim codes and in-person confirmation.
- This changes the patient model and adds a second sign-in context. Reversing it later would mean unwinding links and
  the consent log, so the cost of reversal is real.

## Before building (open items)

1. **Privacy and legal review.** Not assessed here: Bangladesh's data-protection rules for health data, the
   retention duty for medical records, consent for minors and age of majority, SMS and sender rules for OTP traffic,
   and whether the consent wording is sufficient.
2. **Per-plan verification caps** (the numbers for Free, Plus, Pro, Enterprise) and the abuse-limit values.
3. **Native-speaker review** of the consent script and SMS wording.
4. **Retention** of identities that have no links, and deletion on request.
5. **Date of birth versus age** and how coarse the area should be.
6. **SMS delivery reliability** and a fallback (for example a voice call) when codes do not arrive; SIM-swap risk.
7. **Who may revoke** for a child and for an adult on someone else's phone.
8. Confirm that national ID is deliberately **not** used.

## Phase 1 implementation notes (built 2026-10-13)

What exists: tables `person_accounts`, `person_profiles`, `otp_challenges`, `patient_links`,
`identity_consent_events`, `identity_claim_codes` (migration `b9d5f2a8c1e6`); clinic API under `/identity/*` and the
public claim flow under `/public/identity/claim/*`; the entitlement `monthly_patient_verifications` (Free 20,
Plus 300, Pro 1,000, Enterprise 5,000; counts every code sent that month, a failed send is not counted).

Decisions made while building (all adjustable):
- **Phone numbers:** only Bangladesh mobiles (`01[3-9]XXXXXXXX`), stored as `+8801XXXXXXXXX`.
- **OTP limits (settings):** code valid 300 s, 3 attempts, 60 s cooldown per phone, 3 codes per phone per hour,
  200 codes per clinic per day, plus the monthly plan cap. The code is a keyed hash, never stored or logged
  (in development with no SMS provider the code is written to the server log so the flow can be tried).
- **Verification token:** 15 minutes, tied to the clinic and the staff member, at most 10 name searches and 5 links.
- **No enumeration:** after a verified code staff learn only whether the phone has any profile; names appear only
  for profiles matching the name they type (at most 5).
- **One active link per clinic record and per profile per clinic** (partial unique indexes); revoking keeps the
  clinic's record, writes a revoke event, and allows linking again after a fresh verification.
- **Claim codes:** 8 characters (no look-alike letters), hashed, valid 30 days, single use, one live code per
  record. The patient needs no login: phone code plus claim code plus consent. The clinic's plan is not revealed to
  the patient (a capped clinic shows "this clinic cannot verify right now").
- **Consent log** records the wording version (`2026-10-v1`), the staff member and that they confirmed telling the
  patient (clinic route) or none (claim route, where the patient consents on screen).
- **Not in Phase 1:** a patient login or self-registration screen, family management by the holder, sharing between
  clinics, provider fallback (voice) for undelivered codes, per-clinic admin reports of verification usage.

Known limits: only the clinic that verified can see a profile, but a **recycled phone number** still lets its new
holder pass a clinic OTP and find profiles by typing a name (only basic details are exposed, and the clinic
confirms the person in front of them); the profile name search is a simple contains match; dates of birth are
stored as given.

## Phase 2 implementation notes (built 2026-10-13)

What exists: patient sign-in with a phone code (`/patient/auth/request|verify`, a `patient` token that is a different
type from staff tokens, so neither is ever accepted where the other is expected), and a read-only portal API
(`/patient/me`, `/patient/profiles/{id}/records`, `/patient/links/activate`, `/patient/links/{id}/revoke`, a
prescription PDF); clinic staff give a **portal code** for an already-linked patient
(`/identity/patients/{id}/portal-code`). Migration `c3e7a9f4b1d2` adds `person_accounts.portal_registered_at`,
`patient_links.portal_access_at`, a `purpose` on claim codes, the `portal_login` code purpose and the
`portal_access` consent kind.

How the rules were applied:
- **Recycled-number defence (rule 10):** a link made before the phone first signed in to the portal has no
  `portal_access_at`, so it is hidden until a clinic's portal code activates it. A link made afterwards (the holder is
  in front of the clinic) or through the public claim page (the patient proved the phone and the clinic's code) is
  visible at once. A profile with no visible clinic is not returned at all, so a new holder of an old number does not
  even learn the earlier owner's name.
- **Who is visible:** the holder's own profile and their dependents only. Another adult under the same phone is
  never shown and their record cannot be activated (`profile_not_visible`). A phone can have only **one** account
  holder profile (relationship `self`); everyone else is a family member (this tightened Phase 1).
- **Read-only and minimal:** appointments, issued prescriptions (diagnosis, advice, medicines) and paid receipts.
  Never the doctor's private notes, visit examination notes, appointment notes, drafts or voided prescriptions.
- **Isolation:** the portal reads a clinic's rows only through a link, only that linked patient's own rows, one clinic
  at a time with row-level security bound to it (`bind_tenant`), and clears the binding afterwards.
- **Sign-in cost and abuse:** the platform pays; per phone (cooldown, 3 per hour), per IP, and a platform-wide daily
  ceiling (`OTP_MAX_PORTAL_PER_DAY`, 3,000). The answer to a code request is identical for any phone. Sessions last
  12 hours (`PATIENT_TOKEN_HOURS`) and live in sessionStorage; a longer "remember me" would trade SMS cost for
  convenience and is not built.
- **Patient removal:** the patient can remove a clinic from their account; that revokes the link, logs a revoke
  event (method `portal`) and leaves the clinic's own record.

Known limits: row-level security was written to bind per clinic but is **not exercised** in dev or CI (a superuser
connection bypasses it), so it has not been proven against a restricted database role; the prescription PDF depends on
the PDF renderer being available (503 otherwise); no patient-initiated booking, messaging, record sharing between
clinics, data export, or account deletion yet; a holder cannot manage family profiles from the portal; the portal is
reachable only by a link in the public footer.

Phase 3 (appointment requests with clinic confirmation) and Phase 4 (patient-controlled sharing between clinics)
remain, together with the open legal and consent-wording items above.

## Phase 3 implementation notes (built 2026-10-13)

What exists: a signed-in patient asks a public practitioner for an appointment (`POST /patient/appointment-requests`),
the clinic's doctors and receptionists confirm or decline (`/appointment-requests`), and the patient can cancel
(`/patient/appointment-requests/{id}/cancel`). The holder can also add themselves or a child as a profile from the
portal (`POST /patient/profiles`). Migration `d6f1b8c3a5e7` adds `appointment_requests`, `person_profiles.source`
and the `appointment` link method.

How the rules were applied:
- **Asking is the consent.** The request form carries the wording (version `request-2026-10-v1`): the clinic
  receives the person's basic details and links its record to their profile. The clinic sees a **snapshot** taken at
  request time (name, age or birth date, gender, area, verified phone, relationship), never the live profile.
- **Confirming goes through the normal rules.** The slot is checked before anything is created (a conflict leaves no
  half-made record), the patient record is created through the patient service (so the plan's patient cap applies and
  surfaces as `plan_limit_reached`), then linked by consent (method `appointment`, portal access granted because
  the patient asked), and the appointment is booked and marked confirmed.
- **No automatic matching (rule 4) still holds:** a clinic record with the same name and phone that is not linked is
  left alone and a new record is created; a person already linked at the clinic reuses their record.
- **Who can ask:** the holder's own profile or a child under 18 only. A portal can add only `self` (once) and
  `child`; an adult dependent can only be recorded by a clinic. Only a currently public practitioner can be asked
  (listed, verified, approved, in plan), only if they accept requests, only for a date within 60 days.
- **Limits:** one waiting request per person per clinic (a database constraint) and at most 5 waiting per account.
- **Texts to the patient** (confirm and decline) are best effort from the **clinic's own SMS allowance**; with none
  left the action still succeeds without a text.
- The unverified call-back form stays for people who cannot receive a code (rule: verification never blocks care).

Known limits and risks: the request `reason` is free text and health information, stored with the snapshot; **no
retention or deletion rule exists yet** (open item 4 applies to it too). A portal-created profile and its requests
belong to the phone, so a **recycled number's new holder** sees them (Phase 2's hiding only covers clinic-created
profiles); an inactivity lock or a second factor for long-dormant accounts is not built. The clinic is not notified
when a patient cancels (it sees the change on the requests page). No rescheduling, waiting list, appointment
reminders, or per-doctor availability (confirming relies on the existing slot check only). Phase 4 (sharing between
clinics) remains.
