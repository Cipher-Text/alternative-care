/** Patient-controlled sharing between clinics (ADR 009 phase 4; matches backend app/shared/schemas/sharing.py). */

export type ShareCategory = 'prescriptions' | 'diagnoses'
export const SHARE_CATEGORIES: ShareCategory[] = ['prescriptions', 'diagnoses']
export type ShareDays = 7 | 30 | 90
export const SHARE_DAYS: ShareDays[] = [7, 30, 90]

/** active | expired | revoked (the patient stopped it) | ended (a clinic was removed from the account) */
export type ShareStatus = 'active' | 'expired' | 'revoked' | 'ended'

export interface ShareInput {
  /** The clinic whose records are shared (a clinic link from `me()`, `clinics[].link_id`) */
  source_link_id: string
  /** The clinic that may read them (another link for the SAME person) */
  recipient_link_id: string
  categories: ShareCategory[]
  days: ShareDays
  /** Must be true */
  consent: boolean
}

/** Patient side: a share the patient made, with who read it. */
export interface PortalShare {
  id: string
  profile_id: string
  profile_name: string
  source_clinic: string
  recipient_clinic: string
  categories: ShareCategory[]
  status: ShareStatus
  created_at: string
  expires_at: string
  revoked_at: string | null
  access_count: number
  last_accessed_at: string | null
}

/** Clinic side: what a clinic sees about a share (never the records). */
export interface ShareSummary {
  share_id: string
  /** The OTHER clinic */
  clinic_name: string
  categories: ShareCategory[]
  status: ShareStatus
  expires_at: string
  access_count: number
  last_accessed_at: string | null
}

export interface PatientSharing {
  /** Shared WITH this clinic about this patient */
  incoming: ShareSummary[]
  /** This clinic's records shared with others */
  outgoing: ShareSummary[]
}

export interface SharedPrescriptionItem {
  medicine: string
  dosage: string
  frequency: string
  duration: string | null
  instructions: string | null
}

export interface SharedPrescription {
  source_clinic: string
  shared_until: string
  date: string
  doctor_name: string | null
  diagnosis: string | null
  advice: string | null
  items: SharedPrescriptionItem[]
}

export interface SharedDiagnosis {
  source_clinic: string
  shared_until: string
  description: string
  icd_code: string | null
  diagnosed_at: string
  is_active: boolean
}

/** Read-only, read LIVE from the source clinic. Opening it is logged and visible to the patient. */
export interface SharedRecords {
  prescriptions: SharedPrescription[]
  diagnoses: SharedDiagnosis[]
  shares: ShareSummary[]
}

/** Error `detail.code` values: recent_sign_in_required (403: sign in again with a new code), share_exists (409),
 * different_people (422), same_clinic (422), already_revoked (409), 404 (not your link/share, or the patient is
 * not linked at this clinic). */
