/** Appointment requests (ADR 009 phase 3; matches backend app/shared/schemas/appointment_request.py). */

import type { Relationship } from './identity'

export type RequestStatus = 'requested' | 'confirmed' | 'declined' | 'cancelled'
export type RequestWindow = 'morning' | 'afternoon' | 'evening' | 'any'
export const REQUEST_WINDOWS: RequestWindow[] = ['morning', 'afternoon', 'evening', 'any']

/** The booked visit, once the clinic confirmed. */
export interface RequestedAppointment {
  date: string // YYYY-MM-DD
  time: string // HH:MM
  duration_minutes: number
  status: string
}

// ---- patient side

/** Adds yourself ('self', once) or a child under 18. Another adult signs in with their own phone. */
export interface PortalProfileInput {
  display_name: string
  date_of_birth?: string | null
  approx_birth_year?: number | null
  gender?: 'male' | 'female' | 'other' | null
  division_id?: number | null
  district_id?: number | null
  upazila_id?: number | null
  relationship: 'self' | 'child'
}

export interface AppointmentRequestInput {
  practitioner_slug: string
  profile_id: string
  /** Today up to 60 days ahead */
  preferred_date: string
  preferred_window: RequestWindow
  /** Optional, max 300 characters. Health information: keep it short. */
  reason?: string | null
  /** Must be true: the clinic receives the basic details and links its record to the profile */
  consent: boolean
}

export interface PatientRequest {
  id: string
  status: RequestStatus
  clinic_name: string
  practitioner_slug: string | null
  doctor_name: string | null
  profile_id: string
  profile_name: string
  preferred_date: string
  preferred_window: RequestWindow
  reason: string | null
  created_at: string
  appointment: RequestedAppointment | null
  decline_reason: string | null
  /** 'patient' or 'clinic' */
  cancelled_by: string | null
}

// ---- clinic side

/** What the clinic sees: the basic details the patient agreed to share. */
export interface Requester {
  display_name: string
  age_years: number | null
  gender: string | null
  phone: string
  relationship: Relationship | string
  is_dependent: boolean
}

export interface ClinicRequest {
  id: string
  status: RequestStatus
  requester: Requester
  preferred_date: string
  preferred_window: RequestWindow
  reason: string | null
  /** The practitioner they asked for (default doctor when confirming) */
  doctor_id: string | null
  doctor_name: string | null
  created_at: string
  appointment: RequestedAppointment | null
  patient_id: string | null
  /** This person already has a record here (linked earlier by consent): confirming reuses it */
  existing_patient_id: string | null
  decline_reason: string | null
  cancelled_by: string | null
}

export interface ConfirmInput {
  appointment_date: string
  appointment_time: string // HH:MM
  duration_minutes?: number // 15-240, default 30
  doctor_id?: string | null
  /** Best-effort text to the patient from the clinic's own SMS allowance */
  notify_sms?: boolean
}

/** Error `detail.code` values to explain in plain words. Patient side: not_accepting_requests,
 * date_out_of_range, request_in_progress, too_many_open_requests, child_must_be_under_18, self_profile_exists,
 * profile_limit, not_cancellable (409/422), 404 = practitioner not available or not your profile.
 * Clinic side: not_open, slot_taken (choose another time), date_in_past, doctor_not_found,
 * plan_limit_reached (403, the clinic's patient limit), 404. */
