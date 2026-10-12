/** Closed lists come from GET /health-options (codes only); labels are in messages/<locale>/health.json. */
export interface HealthOptions {
  chronic_conditions: string[]
  allergy_types: string[]
  allergy_severities: string[]
  family_history: string[]
  habit_statuses: string[]
  diet_types: string[]
  red_flags: string[]
  referral_urgencies: string[]
  blood_sugar_types: string[]
  safety_flags: string[]
}

export interface AllergyEntry {
  type: string
  substance: string
  severity: string | null
}

export interface HealthProfileInput {
  chronic_conditions: string[]
  allergies: AllergyEntry[]
  family_history: string[]
  smoking: string | null
  alcohol: string | null
  betel_tobacco: string | null
  diet_type: string | null
  pregnant: boolean
  lmp_date: string | null
  breastfeeding: boolean
  on_allopathic_medicines: boolean
  on_blood_thinners: boolean
  recent_surgery: boolean
  current_medicines_note: string | null
  past_surgeries_note: string | null
}

export interface HealthProfile extends HealthProfileInput {
  patient_id: string
  /** false until a profile has been saved: every field is then an empty default */
  exists: boolean
  updated_at: string | null
  /** Warnings for the patient and prescription screens */
  safety_flags: string[]
}

export interface Vitals {
  temperature_c: number | null
  pulse_bpm: number | null
  bp_systolic: number | null
  bp_diastolic: number | null
  respiratory_rate: number | null
  spo2_percent: number | null
  weight_kg: number | null
  height_cm: number | null
  blood_sugar_mmol: number | null
  blood_sugar_type: string | null
  pain_score: number | null
}

export interface VisitListItem extends Vitals {
  id: string
  patient_id: string
  doctor_id: string
  visit_date: string
  visit_type: string
  chief_complaint: string | null
  provisional_diagnosis: string | null
  red_flags: string[] | null
  referral_urgency: string | null
  status: string
}

export type VisitInput = Partial<Vitals> & {
  patient_id: string
  doctor_id: string
  visit_date: string
  visit_type: string
  chief_complaint?: string
  examination_notes?: string
  red_flags?: string[]
  referral_urgency?: string
  provisional_diagnosis?: string
  treatment_plan?: string
}
