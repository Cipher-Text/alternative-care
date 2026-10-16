# Doctor workflow analysis: patient, visit, prescription (2026-10-15)

Status: analysis and proposal. **All four phases (section 7) were built on 2026-10-16.** The proposal still needs a review by
practising doctors before the one-screen design is built.

### Phase 1 as built (2026-10-16)
- Prescriptions show the **patient's name** (list and detail, linked to the patient), the **prescriber's name**, and the **linked visit**
  (date and complaint, linked) instead of raw ids; the list search also matches the patient's name and phone.
- The "Visit ID" text box is a **visit picker** (that patient's visits); choosing one fills an empty diagnosis and advice from the visit.
- The **patient page** has "New prescription" (patient prefilled), a **Prescriptions** card, an **Add diagnosis** action, and each visit
  has **Write prescription** (patient and visit prefilled) and **Finish visit**.
- **Start consultation** on the dashboard's today list and on the appointment page: opens the visit started from the appointment or
  starts one (linked, appointment becomes "in progress", complaint taken from the appointment reason); finishing the visit completes the
  appointment. One visit per appointment (409 `visit_exists` otherwise); a visit can only be linked to that patient's appointment.
- **Editing a draft prescription saves its medicines** (the update accepts `items` and replaces the draft's list).
- A prescription can no longer point at another clinic's patient or at another patient's visit (422/404).
- Not done from section 7 phase 1: nothing outstanding.

### Phase 2 as built (2026-10-16)
- **Medicine rows from the visit.** "Write prescription" on a visit now also fills the **medicine rows** from that visit's case details
  (`frontend/src/lib/prescriptions/medicineRowsFromCase.ts`, unit-tested): homeopathy's medicines list (name and potency) or its older
  single remedy (with dose form and repetition), Unani's drug (with drug form), Ayurveda's formulation (with the anupana as an
  instruction). Dosage and frequency are left for the doctor where the case form did not record them; the form says so and blocks
  issuing until each row is finished. Only a still-untouched form is filled.
- **A visit shows its prescriptions:** a chip per prescription (draft / issued / voided, date, linked), and "Continue draft prescription"
  when a draft exists.
- Already from phase 1 and counted here: diagnosis and advice prefilled from the visit; a prescription shows its visit.
- Not done from section 7 phase 2: nothing outstanding.

## 1. What was checked

The real screens and routes, from the code and in the running app as the homeopath (Dr. Rahman, Bengali UI): the patient page,
the visit dialog and the per-visit case details, the appointment pages, the prescription list, builder and detail pages, the
dashboard "today" panel, and payments. The question was not "does each screen work" (they do) but "can a doctor get through a
consultation without thinking about our data model".

## 2. How a doctor thinks: the paper sheet

The clinic's own paper case form (two pages, added to the app on 2026-10-15) is a single sheet per consultation. Top to bottom:
patient header (name, age, sex, occupation, date, serial, weight, height, BP, sugar) -> chief complaints -> cause and
modalities -> physical and mental generals -> women and children sections -> past history and miasm -> **prescription and
follow-up tracker** (medicine, dilution, patient's condition, next medicine, next follow-up date).

So the doctor's mental model is **one case sheet per consultation, ending in the medicine**. "Visit" and "prescription" are not two
tasks to them; they are the beginning and the end of the same sheet.

## 3. The journey today (one follow-up consultation)

| Step | Where | Notes |
|---|---|---|
| 1. Find the patient | Dashboard "today" -> patient page | The patient page is long: details, identity, sharing, health background, case profile, then visits, tags, diagnoses |
| 2. Write the visit | Patient page -> "Write a visit" dialog | Date, type, complaint, history, examination, 11 vitals, red flags, provisional diagnosis, treatment plan, follow-up date and note |
| 3. Take the homeopathy case details | The saved visit -> "Show details" -> another dialog | 20 visit fields (and 88 patient-level ones on the profile card) |
| 4. Write the prescription | Sidebar -> Prescriptions -> New | **Pick the patient again.** A raw "Visit ID" text box. Diagnosis again. Notes. Advice. Medicines. Issue. |
| 5. Close the appointment | Appointments -> the appointment -> Edit -> "Mark completed" | Nothing links it to the visit or prescription |
| 6. Take the money | Payments -> new | `visit_id` exists in the database, but no screen uses it |

About 25 clicks, four screens, the patient chosen twice, and the diagnosis typed up to three times.

## 4. Findings

### A. Defects (a doctor would call these bugs)

1. **The prescription list shows no patient name.** It shows `patient_id.substring(0, 8)...` and a fragment of the prescription id.
   The list schema (`PrescriptionListItem`) carries no patient name. A doctor cannot tell whose prescription is whose.
2. **The prescription detail page shows the patient as a raw UUID** ("Patient ID") and the visit as a raw UUID.
3. **"Visit ID" is a free-text box** on the prescription form. Nobody can paste a UUID from memory, so in practice it is never filled.
4. **The patient page has no "New prescription" button** and the prescriptions list cannot be filtered to one patient from there.
   The only ways in are the sidebar and a dashboard quick action, both of which start blank.
5. **Diagnoses history is read-only.** `addDiagnosis` exists in the API and hooks, but no screen calls it.
6. **Editing a draft prescription does not save medicine changes.** The edit save sends only diagnosis, notes and advice; the builder
   has add and delete item calls available but does not use them, and there is no item-update endpoint.
7. **The appointment is a dead end.** The model comment says a visit is "created when appointment is completed", but the UI never does
   that and never links `visit.appointment_id`. "Start consultation" does not exist.

### B. Structural overlap (the confusion you reported)

The same facts are asked for in several places:

| Fact | Where it is entered today |
|---|---|
| Complaint | `visit.chief_complaint`; homeopathy visit "location / sensation / accompanying"; the new homeopathy "chief complaints" list (12 rows) |
| Diagnosis | `visit.provisional_diagnosis`; `prescription.diagnosis`; the patient's diagnoses history (read-only) |
| Treatment | `visit.treatment_plan`; `prescription.advice` and `doctors_notes`; homeopathy "next step" |
| The medicine | the homeopathy visit "remedy / potency / dose form / repetition"; the prescription items; the paper form's tracker |
| Follow-up | `visit.follow_up_date` and note; "next follow-up date" on the paper form; the appointment to be booked separately |
| History | the shared Health background; the homeopathy profile (past illnesses, family, vaccination); the patient record's own text fields |

The two records are meant to differ (a visit is the private working record and can be edited; a prescription is the issued, immutable,
printable paper), but nothing in the screens says so or connects them.

### C. Information layering on the patient page

Five stacked cards before the first visit: details, identity and sharing, health background, case profile, visits. Doctors reach the
visit list only after scrolling past everything that rarely changes. The things changed every consultation (visits, medicines) sit
lowest; the things changed once (identity, background) sit highest.

## 5. What each object should be (definitions to put in the product)

- **Patient**: who they are and what stays true between visits (details, identity, health background, constitution / case profile).
- **Appointment**: a slot in the diary (reception's tool). It ends in a visit.
- **Visit (consultation)**: what happened this time. The working record, editable, private. Includes the case-taking for this time and
  the decision (diagnosis, plan, medicines, next follow-up).
- **Prescription**: the issued paper the patient takes home. Created *from* a visit, immutable once issued, printable, voidable.
- **Payment**: money for a visit.

## 6. Proposal: one consultation screen

The doctor works on one page per consultation, top to bottom, like the paper sheet:

1. Patient strip (name, age, allergies/red-flag banner, last visit) and vitals.
2. Chief complaints (the 12-line list) and case details for the clinic's system(s).
3. Diagnosis and treatment plan, **entered once**.
4. Medicines: the inline rows (with the medicine dropdown), kind (dilution / mother tincture / biochemic), next medicines.
5. Follow-up date (this creates the follow-up appointment suggestion).
6. **Issue prescription** (PDF) and **Take payment**, both prefilled from this page.

Entry points: "Start consultation" on today's appointment, and on the patient page. Both create the visit and link the appointment.

The Prescriptions menu remains the archive (find, reprint, void) and a quick "repeat medicine" without a visit. Records stay separate in
the database; existing visits and prescriptions are untouched.

## 7. Phasing

1. **Fix the defects (small, no redesign).** Patient name on the prescription list and detail; a visit picker instead of the Visit ID box;
   "New prescription" on the patient page (patient prefilled) and the patient's prescriptions listed there; a way to add a diagnosis;
   save medicine changes when editing a draft; link the appointment when a visit is started and offer "mark completed".
2. **Connect visit and prescription.** "Write prescription" on a visit, prefilled (diagnosis <- provisional diagnosis, advice <- plan,
   medicine rows <- the visit's medicine list); a visit shows its prescriptions; a prescription shows its visit.
3. **One consultation screen.** Medicines and Issue inside the visit; remove the duplicated "remedy and potency" entry from the case form;
   one place for diagnosis and plan.
4. **Close the loop.** Follow-up date creates the next appointment; payment started from the visit.

### Phase 3 as built (2026-10-16): the consultation screen

- **New screen `/consultations/{visitId}`** (`frontend/src/components/consultation/`): one page per visit, top to bottom: complaint and
  history (complaint, history of the present illness, examination), vitals and warning signs, case details for each system the clinic
  practises, **diagnosis, plan and follow-up entered once**, **medicines**, then a sticky bar with **Save**, **Issue prescription** and
  **Finish consultation** (with an "unsaved changes" indicator and a leave-page guard). Read-only for people who may not write visits.
- **Visits can now be edited.** Before this, a visit could only be created (a create-only pop-up), so a visit started from an
  appointment could not be filled in. Every field is sent on save, an emptied box as null.
- **One Save does everything:** it updates the visit, saves the case-detail answers that changed, and creates or updates the draft
  prescription linked to the visit, with the **diagnosis taken from the visit's diagnosis and the advice from its plan** (no second
  entry). **Issue** saves, then issues that prescription (an issued prescription is permanent, so the editor then starts a fresh one,
  and the issued one shows with its PDF button). **Finish** saves and completes the visit and its appointment.
- **The duplicate medicine entry is gone from the screen.** The case-form fields the Medicines section replaces (homeopathy: medicines
  list, remedy, potency, dose form, repetition; Unani: drug and form; Ayurveda: formulation and anupana) are not drawn, and their saved
  values are kept. A visit that only has medicines in those older fields gets them as the first medicine rows, once.
- **Entry points:** "Start consultation" (dashboard, appointment page) opens this screen; "Record a visit" on the patient page starts a
  blank walk-in visit for today and opens it; each visit on the patient page has "Open consultation" and still shows its prescriptions.
  The old visit pop-up is removed. The separate prescription form (`/prescriptions/new`) remains for a quick repeat prescription.
- Tests: the form-to-payload logic is unit-tested (`tests/unit/visit-draft.test.js`); the flow was walked in the browser.
- Not done: the follow-up date does not yet create the next appointment, and payment is not started from the screen (phase 4).

### Phase 4 as built (2026-10-16): closing the loop

- **Follow-up appointment from the consultation.** A "Follow-up appointment" card under the consultation takes the follow-up date the
  doctor set and books it with a time and one click (30 minutes, the diary's own clash check refuses a taken time). If an appointment
  already exists on that date it says so and links to it. No new data model: the dashboard's "follow-ups due" list already leaves out
  a patient who has an upcoming appointment, so booking the follow-up removes them from it (checked against the real list).
- **Payment from the visit.** A "Payment" card shows the clinic's usual fee (consultation fee, or the follow-up fee for a follow-up
  visit; the profile stores paisa), what has been paid for this visit, anything still due, and "Record payment" (amount prefilled with the
  fee, cash or bKash, optional note). It is also visible to the front desk (`payments.read` / `payments.write`), who can record the
  payment after the doctor finishes.
- **Backend:** a payment must now belong to this clinic's patient and a visit (if given) must be that patient's (404 / 422, like
  prescriptions); the payment list carries `visit_id` and can already be filtered by it.
- Tests: fee and follow-up-date logic unit-tested (`tests/unit/visit-draft.test.js`); the payment checks have service and route tests.
- Not done: an invoice is still created separately from the Payments page; the appointment's reason is written in the doctor's
  interface language ("Follow-up: ..."); slot suggestions (free times) are not offered, only the clash refusal.

## 8. Risks and open questions

- Is a doctor who sees 40 patients a day better served by the full sheet, or by a fast mode (complaint, diagnosis, medicines only)? Both
  need to exist; the case-taking sections must be collapsible and optional (they are).
- The paper sheet has no separate "visit" and "prescription". Confirm with the clinic's doctors that a single page is what they want, and
  whether the issued paper should ever be started without a consultation (repeat prescriptions).
- Receptionists: they read visits and take payments, but must not see sensitive case answers (already enforced) or write prescriptions.
- Existing duplicated fields cannot simply be deleted: they hold saved data. They would be hidden in the new screen and migrated later.

## 9. How to know it worked

Steps and clicks for a follow-up consultation (target: under 10, one screen); diagnosis typed once; no screen shows a raw id;
every prescription shows a patient name; a doctor can explain the difference between visit and prescription in one sentence.
