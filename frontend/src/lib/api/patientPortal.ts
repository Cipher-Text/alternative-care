import axios from 'axios'
import { clearPatientSession, getPatientToken, setPatientSession } from '@/lib/patientSession'
import type { PortalClinic, PortalMe, PortalRecords } from '@/types/patientPortal'
import type { PortalProfile } from '@/types/patientPortal'
import type { PortalShare, ShareInput } from '@/types/sharing'
import type { AppointmentRequestInput, PatientRequest, PortalProfileInput } from '@/types/appointmentRequest'
import type { VerifyRequestResponse } from '@/types/identity'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

/** A client of its own: it never carries the clinic staff token and never tries to refresh one. */
const patientClient = axios.create({ baseURL: `${API_URL}/patient` })

patientClient.interceptors.request.use((config) => {
  const token = getPatientToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** A 401 means the portal session ended (they last 12 hours): drop it so the page shows sign-in again. */
patientClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error?.response?.status === 401) clearPatientSession()
    return Promise.reject(error)
  }
)

export const patientPortalApi = {
  /** Sends a sign-in code. The answer is the same whether or not the phone has an account. */
  requestCode: async (phone: string): Promise<VerifyRequestResponse> =>
    (await patientClient.post('/auth/request', { phone })).data,
  /** On success the session is stored (sessionStorage) and the caller can load /me. */
  verify: async (challenge_id: string, code: string): Promise<void> => {
    const { data } = await patientClient.post<{ access_token: string; expires_at: string }>('/auth/verify', {
      challenge_id,
      code,
    })
    setPatientSession(data.access_token, data.expires_at)
  },
  signOut: (): void => clearPatientSession(),
  hasSession: (): boolean => getPatientToken() !== null,
  me: async (): Promise<PortalMe> => (await patientClient.get('/me')).data,
  records: async (profileId: string): Promise<PortalRecords> =>
    (await patientClient.get(`/profiles/${profileId}/records`)).data,
  /** A code from the clinic makes an earlier record visible in this account. */
  activate: async (code: string): Promise<PortalClinic> => (await patientClient.post('/links/activate', { code })).data,
  /** Removes a clinic from the account. The clinic keeps its own medical record. */
  revoke: async (linkId: string): Promise<void> => {
    await patientClient.post(`/links/${linkId}/revoke`)
  },
  /** Add yourself (once) or a child under 18 */
  addProfile: async (data: PortalProfileInput): Promise<PortalProfile> =>
    (await patientClient.post('/profiles', data)).data,
  requestAppointment: async (data: AppointmentRequestInput): Promise<PatientRequest> =>
    (await patientClient.post('/appointment-requests', data)).data,
  requests: async (): Promise<PatientRequest[]> => (await patientClient.get('/appointment-requests')).data,
  /** A waiting request, or a confirmed appointment that has not happened yet */
  cancelRequest: async (id: string): Promise<PatientRequest> =>
    (await patientClient.post(`/appointment-requests/${id}/cancel`)).data,
  /** Everything you shared, with who read it and when */
  shares: async (): Promise<PortalShare[]> => (await patientClient.get('/shares')).data,
  /** Needs a recent sign-in: otherwise 403 recent_sign_in_required */
  createShare: async (data: ShareInput): Promise<PortalShare> => (await patientClient.post('/shares', data)).data,
  /** Takes effect at once: nothing was copied */
  revokeShare: async (id: string): Promise<void> => {
    await patientClient.post(`/shares/${id}/revoke`)
  },
  prescriptionPdf: async (linkId: string, prescriptionId: string): Promise<Blob> =>
    (await patientClient.get(`/links/${linkId}/prescriptions/${prescriptionId}/pdf`, { responseType: 'blob' })).data,
}
