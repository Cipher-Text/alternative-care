// The consultation form's values as typed (strings), and the check that turns them into what the API takes. Pure on purpose
// (types only as imports) so it can be tested without the app. Mirrors the limits of the backend's VitalsFields.

export const NONE = '__none'

/** Number fields: [form key, i18n label key, min, max, whole numbers only] */
export const NUMBER_FIELDS = [
  ['temperature_c', 'temperature', 30, 45, false],
  ['pulse_bpm', 'pulse', 20, 250, true],
  ['respiratory_rate', 'respiratoryRate', 4, 80, true],
  ['spo2_percent', 'spo2', 50, 100, true],
  ['weight_kg', 'weight', 0.3, 500, false],
  ['height_cm', 'height', 30, 260, false],
  ['pain_score', 'pain', 0, 10, true],
] as const

export type VisitDraft = Record<string, string>

export interface VisitLike {
  visit_date: string
  visit_type: string
  chief_complaint?: string | null
  history_of_present_illness?: string | null
  examination_notes?: string | null
  provisional_diagnosis?: string | null
  treatment_plan?: string | null
  follow_up_date?: string | null
  follow_up_notes?: string | null
  referral_urgency?: string | null
  blood_sugar_type?: string | null
  red_flags?: string[] | null
  temperature_c?: number | null
  pulse_bpm?: number | null
  bp_systolic?: number | null
  bp_diastolic?: number | null
  respiratory_rate?: number | null
  spo2_percent?: number | null
  weight_kg?: number | null
  height_cm?: number | null
  blood_sugar_mmol?: number | null
  pain_score?: number | null
}

export function bmiOf(weightKg: number | null | undefined, heightCm: number | null | undefined): number | null {
  if (!weightKg || !heightCm) return null
  const m = heightCm / 100
  return Math.round((weightKg / (m * m)) * 10) / 10
}

const str = (v: unknown): string => (v === null || v === undefined ? '' : String(v))

/** What the form shows for a saved visit. */
export function draftFromVisit(v: VisitLike): VisitDraft {
  const draft: VisitDraft = {
    visit_date: v.visit_date,
    visit_type: v.visit_type,
    chief_complaint: str(v.chief_complaint),
    history_of_present_illness: str(v.history_of_present_illness),
    examination_notes: str(v.examination_notes),
    provisional_diagnosis: str(v.provisional_diagnosis),
    treatment_plan: str(v.treatment_plan),
    follow_up_date: str(v.follow_up_date),
    follow_up_notes: str(v.follow_up_notes),
    referral_urgency: v.referral_urgency || NONE,
    blood_sugar_type: v.blood_sugar_type || NONE,
    bp_systolic: str(v.bp_systolic),
    bp_diastolic: str(v.bp_diastolic),
    blood_sugar_mmol: str(v.blood_sugar_mmol),
  }
  for (const [key] of NUMBER_FIELDS) draft[key] = str(v[key as keyof VisitLike])
  return draft
}

export interface VisitMessages {
  numberInvalid: (min: number, max: number) => string
  bpPair: string
  bpOrder: string
  sugarPair: string
}

const text = (v: string | undefined): string | null => (v?.trim() ? v.trim() : null)

/**
 * The PATCH body for a visit, or the problems to show. Every field is sent, an empty one as null, so that clearing a box
 * clears it on the server too.
 */
export function visitPayload(
  draft: VisitDraft,
  flags: string[],
  msgs: VisitMessages
): { errors: Record<string, string>; payload: Record<string, unknown> } {
  const errors: Record<string, string> = {}
  const payload: Record<string, unknown> = {}
  const num = (key: string): number | null => (draft[key]?.trim() ? Number(draft[key]) : null)

  for (const [key, , min, max, whole] of NUMBER_FIELDS) {
    const n = num(key)
    if (n === null) payload[key] = null
    else if (!Number.isFinite(n) || n < min || n > max || (whole && !Number.isInteger(n))) errors[key] = msgs.numberInvalid(min, max)
    else payload[key] = n
  }

  const sys = num('bp_systolic')
  const dia = num('bp_diastolic')
  if ((sys === null) !== (dia === null)) errors.bp = msgs.bpPair
  else if (sys === null || dia === null) Object.assign(payload, { bp_systolic: null, bp_diastolic: null })
  else if (!Number.isInteger(sys) || !Number.isInteger(dia) || sys < 40 || sys > 300 || dia < 20 || dia > 200) errors.bp = msgs.numberInvalid(20, 300)
  else if (dia >= sys) errors.bp = msgs.bpOrder
  else Object.assign(payload, { bp_systolic: sys, bp_diastolic: dia })

  const sugar = num('blood_sugar_mmol')
  const sugarType = draft.blood_sugar_type && draft.blood_sugar_type !== NONE ? draft.blood_sugar_type : null
  if (sugar === null) {
    if (sugarType) errors.sugar = msgs.sugarPair
    else Object.assign(payload, { blood_sugar_mmol: null, blood_sugar_type: null })
  } else if (!Number.isFinite(sugar) || sugar < 1 || sugar > 60) errors.sugar = msgs.numberInvalid(1, 60)
  else Object.assign(payload, { blood_sugar_mmol: sugar, blood_sugar_type: sugarType })

  Object.assign(payload, {
    visit_type: draft.visit_type,
    chief_complaint: text(draft.chief_complaint),
    history_of_present_illness: text(draft.history_of_present_illness),
    examination_notes: text(draft.examination_notes),
    provisional_diagnosis: text(draft.provisional_diagnosis),
    treatment_plan: text(draft.treatment_plan),
    follow_up_date: draft.follow_up_date?.trim() ? draft.follow_up_date : null,
    follow_up_notes: text(draft.follow_up_notes),
    red_flags: flags.length > 0 ? flags : null,
    referral_urgency: draft.referral_urgency && draft.referral_urgency !== NONE ? draft.referral_urgency : null,
  })
  return { errors, payload }
}

/** Case-form fields that the Medicines section replaces: shown nowhere on the consultation screen (their saved values stay). */
export const SUPERSEDED_BY_MEDICINES: Record<string, string[]> = {
  homeopathy: ['prescribed', 'remedy', 'potency', 'dose_form', 'repetition'],
  unani: ['ilaj_dawa_drug', 'drug_form'],
  ayurveda: ['formulation', 'anupana'],
}

/**
 * The clinic's usual fee for this kind of visit, in taka (the profile stores paisa), or null when none is set. A follow-up uses
 * the follow-up fee when there is one, otherwise the consultation fee.
 */
export function visitFeeBdt(
  visitType: string,
  fees: { consultation_fee?: number | null; follow_up_fee?: number | null } | null | undefined
): number | null {
  if (!fees) return null
  const paisa = visitType === 'follow_up' ? fees.follow_up_fee ?? fees.consultation_fee : fees.consultation_fee
  return paisa && paisa > 0 ? paisa / 100 : null
}

/** Can a follow-up appointment be booked for this date? A real calendar day, not before the visit itself. */
export function canBookFollowUp(followUpDate: string | undefined, visitDate: string): boolean {
  if (!followUpDate || !/^\d{4}-\d{2}-\d{2}$/.test(followUpDate)) return false
  return !Number.isNaN(Date.parse(`${followUpDate}T00:00:00Z`)) && followUpDate >= visitDate
}
