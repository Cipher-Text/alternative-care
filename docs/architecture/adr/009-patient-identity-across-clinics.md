# ADR 009: Patient identity across clinics: an optional, phone-verified identity that clinics link to by consent, never by automatic matching

- Status: **Proposed.** Needs owner sign-off and a privacy/legal review before any code (see "Before building").
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
