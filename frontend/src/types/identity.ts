/** Patient identity (ADR 009 phase 1; matches backend app/shared/schemas/identity.py). */

export type Relationship = 'self' | 'child' | 'spouse' | 'parent' | 'other'
export const RELATIONSHIPS: Relationship[] = ['self', 'child', 'spouse', 'parent', 'other']

export interface VerifyRequestResponse {
  challenge_id: string
  expires_at: string
  resend_after_seconds: number
  /** e.g. +88017*****111 */
  phone_masked: string
}

export interface VerifyConfirmResponse {
  /** Short-lived (about 15 minutes), tied to this clinic and staff member */
  verification_token: string
  expires_at: string
  /** Only a flag: names appear only after searching by the visitor's name */
  has_profiles: boolean
}

export interface ProfileSummary {
  id: string
  display_name: string
  age_years: number | null
  gender: string | null
  relationship: Relationship
  is_dependent: boolean
  /** This person already has a record at the searching clinic */
  linked_here: boolean
}

/** What a link shares: basic details only. Never anything clinical. */
export interface BasicDetails {
  profile_id: string
  display_name: string
  date_of_birth: string | null
  approx_birth_year: number | null
  gender: string | null
  division_id: number | null
  district_id: number | null
  upazila_id: number | null
  relationship: Relationship
  is_dependent: boolean
  /** The verified phone, +8801XXXXXXXXX */
  phone: string
}

export interface NewProfileInput {
  display_name: string
  date_of_birth?: string | null
  approx_birth_year?: number | null
  gender?: string | null
  division_id?: number | null
  district_id?: number | null
  upazila_id?: number | null
  relationship?: Relationship
  is_dependent?: boolean | null
}

/** Give exactly one of profile_id or new_profile. */
export interface LinkInput {
  verification_token: string
  patient_id: string
  profile_id?: string
  new_profile?: NewProfileInput
}

export interface LinkResponse {
  link_id: string
  patient_id: string
  profile_id: string
  profile_display_name: string
  linked_at: string
  profile_reused: boolean
}

/** Level 0 = details entered by the clinic; level 1 = phone-verified and linked. */
export interface PatientIdentityStatus {
  patient_id: string
  level: 0 | 1
  linked: boolean
  linked_at: string | null
  method: 'clinic_otp' | 'claim_code' | null
  profile_display_name: string | null
}

export interface ClaimCode {
  /** Shown once, e.g. ABCD-EFGH; only a hash is stored */
  code: string
  expires_at: string
}

export interface ClaimResult {
  linked: boolean
  clinic_name: string
  profile_display_name: string
}

/** Error `detail.code` values the UI should explain in plain words:
 * otp_cooldown (429, Retry-After header), otp_phone_limit (429), otp_clinic_daily_cap (429),
 * plan_limit_reached / feature_not_in_plan / plan_expired (403, clinic plan), otp_invalid, otp_expired,
 * otp_locked (400), invalid_verification (403: verify again), already_linked,
 * profile_already_linked_here (409, has existing_patient_id), profile_limit (409),
 * invalid_claim_code (404), clinic_unavailable (403, public claim). SMS unavailable is a 503. */
export const SCRIPT_VERSION = '2026-10-v1'
