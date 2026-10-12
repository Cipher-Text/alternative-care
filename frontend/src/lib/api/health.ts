import apiClient from './client'
import type { HealthOptions, HealthProfile, HealthProfileInput, VisitInput, VisitListItem } from '@/types/health'

export const healthApi = {
  options: async (): Promise<HealthOptions> => (await apiClient.get('/health-options')).data,
  getProfile: async (patientId: string): Promise<HealthProfile> =>
    (await apiClient.get(`/patients/${patientId}/health-profile`)).data,
  /** Replaces the whole profile. */
  saveProfile: async (patientId: string, data: HealthProfileInput): Promise<HealthProfile> =>
    (await apiClient.put(`/patients/${patientId}/health-profile`, data)).data,
  visits: async (patientId: string): Promise<VisitListItem[]> =>
    (await apiClient.get('/appointments/visits', { params: { patient_id: patientId, limit: 50 } })).data,
  createVisit: async (data: VisitInput): Promise<VisitListItem> =>
    (await apiClient.post('/appointments/visits', data)).data,
}
