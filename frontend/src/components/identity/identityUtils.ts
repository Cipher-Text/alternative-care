import { rawDetail } from '@/lib/apiErrors'
import type { Patient } from '@/types/patient'
import type { NewProfileInput, Relationship } from '@/types/identity'

/** Bangladesh mobile: 01XXXXXXXXX, 8801XXXXXXXXX or +8801XXXXXXXXX (operator digit 3-9). */
const BD_MOBILE = /^(?:\+?88)?(01[3-9]\d{8})$/

/** The number as the API expects it (+8801XXXXXXXXX), or null if it is not a Bangladesh mobile. */
export function normalizeBdPhone(input: string): string | null {
  const m = input.replace(/[\s-]/g, '').match(BD_MOBILE)
  return m ? `+88${m[1]}` : null
}

/** +8801XXXXXXXXX -> 01XXXXXXXXX (how the patient form shows numbers). */
export function toLocalPhone(phone: string): string {
  const m = phone.replace(/[\s-]/g, '').match(BD_MOBILE)
  return m ? m[1] : phone
}

export interface IdentityErrorInfo {
  status?: number
  code?: string
  /** Seconds from a Retry-After header, when the server sent one */
  retryAfter?: number
  /** For profile_already_linked_here */
  existingPatientId?: string
}

/** Reads `detail.code` from an axios error (clinic side) or the public fetch error (claim page). */
export function identityError(error: unknown): IdentityErrorInfo {
  const e = error as {
    status?: number
    code?: unknown
    response?: { status?: number; headers?: Record<string, unknown> }
  }
  const detail = rawDetail(error)
  const obj = detail && typeof detail === 'object' && !Array.isArray(detail) ? (detail as Record<string, unknown>) : {}
  const code = typeof obj.code === 'string' ? obj.code : typeof e?.code === 'string' && !e.code.startsWith('ERR_') ? e.code : undefined
  const retry = Number(e?.response?.headers?.['retry-after'])
  return {
    status: e?.response?.status ?? e?.status,
    code,
    retryAfter: Number.isFinite(retry) && retry > 0 ? Math.ceil(retry) : undefined,
    existingPatientId: typeof obj.existing_patient_id === 'string' ? obj.existing_patient_id : undefined,
  }
}

export function isRelationship(v: string): v is Relationship {
  return ['self', 'child', 'spouse', 'parent', 'other'].includes(v)
}

/** Basic details of a saved clinic record, in the shape a new profile needs. Nothing clinical. */
export function newProfileFromPatient(
  patient: Pick<Patient, 'full_name' | 'date_of_birth' | 'gender' | 'division_id' | 'district_id' | 'upazila_id'>,
  relationship: Relationship,
  approxBirthYear?: number | null
): NewProfileInput {
  return {
    display_name: patient.full_name,
    date_of_birth: patient.date_of_birth || null,
    approx_birth_year: patient.date_of_birth ? null : approxBirthYear ?? null,
    gender: patient.gender,
    division_id: patient.division_id,
    district_id: patient.district_id,
    upazila_id: patient.upazila_id,
    relationship,
  }
}
