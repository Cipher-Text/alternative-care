import { apiClient } from './client'
import type { ClinicRequest, ConfirmInput, RequestStatus } from '@/types/appointmentRequest'

/** Clinic staff (doctors and receptionists): see, confirm or decline appointment requests. */
export const appointmentRequestsApi = {
  list: async (params?: { status?: RequestStatus; limit?: number; offset?: number }): Promise<ClinicRequest[]> =>
    (await apiClient.get('/appointment-requests', { params })).data,
  /** Books the appointment through the normal rules, creates and links the patient record if needed */
  confirm: async (id: string, data: ConfirmInput): Promise<ClinicRequest> =>
    (await apiClient.post(`/appointment-requests/${id}/confirm`, data)).data,
  decline: async (id: string, reason: string, notify_sms = true): Promise<ClinicRequest> =>
    (await apiClient.post(`/appointment-requests/${id}/decline`, { reason, notify_sms })).data,
}
