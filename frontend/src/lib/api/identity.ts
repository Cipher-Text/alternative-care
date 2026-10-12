import { apiClient } from './client'
import type { PatientSharing, SharedRecords } from '@/types/sharing'
import type {
  BasicDetails,
  ClaimCode,
  ClaimResult,
  LinkInput,
  LinkResponse,
  PatientIdentityStatus,
  ProfileSummary,
  Relationship,
  VerifyConfirmResponse,
  VerifyRequestResponse,
} from '@/types/identity'

/** Clinic staff (doctor, receptionist). The platform pays for the SMS codes; revoke is doctor-only. */
export const identityApi = {
  requestCode: async (phone: string): Promise<VerifyRequestResponse> =>
    (await apiClient.post('/identity/verify/request', { phone })).data,
  /** `script_confirmed` must be true: the staff member read the consent script to the patient */
  confirmCode: async (challenge_id: string, code: string, script_confirmed: boolean): Promise<VerifyConfirmResponse> =>
    (await apiClient.post('/identity/verify/confirm', { challenge_id, code, script_confirmed })).data,
  searchProfiles: async (verification_token: string, name: string): Promise<ProfileSummary[]> =>
    (await apiClient.post('/identity/profiles/search', { verification_token, name })).data,
  prefill: async (verification_token: string, profile_id: string): Promise<BasicDetails> =>
    (await apiClient.post('/identity/profiles/prefill', { verification_token, profile_id })).data,
  link: async (data: LinkInput): Promise<LinkResponse> => (await apiClient.post('/identity/link', data)).data,
  status: async (patientId: string): Promise<PatientIdentityStatus> =>
    (await apiClient.get(`/identity/patients/${patientId}`)).data,
  revoke: async (patientId: string, note?: string): Promise<PatientIdentityStatus> =>
    (await apiClient.post(`/identity/patients/${patientId}/revoke`, { note })).data,
  /** For an already-linked patient: a code they enter in their portal account to see this clinic's records */
  /** Clinic names and dates only: who the patient shares records with, and who shared with this clinic */
  sharing: async (patientId: string): Promise<PatientSharing> =>
    (await apiClient.get(`/identity/patients/${patientId}/sharing`)).data,
  /** Doctors only. Records another clinic's patient chose to share, read live; opening it is logged. */
  sharedRecords: async (patientId: string): Promise<SharedRecords> =>
    (await apiClient.get(`/identity/patients/${patientId}/shared-records`)).data,
  createPortalCode: async (patientId: string): Promise<ClaimCode> =>
    (await apiClient.post(`/identity/patients/${patientId}/portal-code`)).data,
  createClaimCode: async (patientId: string): Promise<ClaimCode> =>
    (await apiClient.post(`/identity/patients/${patientId}/claim-code`)).data,
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function publicPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    const err = new Error(typeof detail === 'string' ? detail : detail?.message || `request failed: ${res.status}`)
    Object.assign(err, { status: res.status, code: typeof detail === 'object' ? detail?.code : undefined })
    throw err
  }
  return data as T
}

/** Public, no login: a patient links a record using the claim code the clinic gave them. */
export const claimApi = {
  request: (phone: string, claim_code: string) =>
    publicPost<VerifyRequestResponse>('/public/identity/claim/request', { phone, claim_code }),
  confirm: (challenge_id: string, code: string, relationship: Relationship, consent: boolean) =>
    publicPost<ClaimResult>('/public/identity/claim/confirm', { challenge_id, code, relationship, consent }),
}
