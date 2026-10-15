# Doctor workflow analysis: patient, visit, prescription (2026-10-15)

Status: analysis and proposal. **Phase 1 (section 7) was built on 2026-10-16**; phases 2 to 4 are not. The proposal still needs a review by
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
- Not done from section 7 phase 2: nothing outstanding. The case form's own "remedy / potency" entry is still there; removing the
  duplicate is phase 3.

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
