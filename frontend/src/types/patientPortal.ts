/** Patient portal (ADR 009 phase 2; matches backend app/shared/schemas/identity.py, Portal* models). */

import type { Relationship } from './identity'

export interface PortalClinic {
  link_id: string
  clinic_name: string
  linked_at: string
}

export interface PortalProfile {
  id: string
  display_name: string
  age_years: number | null
  gender: string | null
  relationship: Relationship
  is_dependent: boolean
  /** Clinics whose records this holder may see. A profile with none is not returned at all. */
  clinics: PortalClinic[]
}

export interface PortalMe {
  /** e.g. +88017*****111 */
  phone_masked: string
  profiles: PortalProfile[]
}

export interface PortalAppointment {
  clinic_name: string
  doctor_name: string | null
  date: string // YYYY-MM-DD
  time: string // HH:MM
  duration_minutes: number
  status: string
  reason: string | null
}

export interface PortalPrescriptionItem {
  medicine: string
  dosage: string
  frequency: string
  duration: string | null
  instructions: string | null
}

export interface PortalPrescription {
  id: string
  /** Needed to download the PDF */
  link_id: string
  clinic_name: string
  doctor_name: string | null
  date: string
  diagnosis: string | null
  advice: string | null
  items: PortalPrescriptionItem[]
}

export interface PortalReceipt {
  clinic_name: string
  date: string
  amount: number
  currency: string
  method: string
  description: string | null
  invoice_number: string | null
}

/** Read-only. Doctors' private notes, examination notes and unissued prescriptions are never included. */
export interface PortalRecords {
  appointments: PortalAppointment[]
  prescriptions: PortalPrescription[]
  receipts: PortalReceipt[]
}

/** Error `detail.code` values: otp_invalid / otp_expired / otp_locked (400), otp_cooldown / otp_phone_limit /
 * otp_portal_daily_cap (429), invalid_portal_code (404: wrong, used, expired, or not yours),
 * profile_not_visible (409: another adult's record). A 401 means the session ended: sign in again. */
