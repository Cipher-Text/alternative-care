import apiClient from './client'
import type { CaseData, CaseDefinitions, CaseRecord } from '@/types/caseTaking'

export const caseTakingApi = {
  definitions: async (system: string): Promise<CaseDefinitions> => (await apiClient.get(`/case-taking/${system}`)).data,
  getPatient: async (patientId: string, system: string): Promise<CaseRecord> =>
    (await apiClient.get(`/case-taking/patients/${patientId}/${system}`)).data,
  /** Replaces the whole form. */
  savePatient: async (patientId: string, system: string, data: CaseData): Promise<CaseRecord> =>
    (await apiClient.put(`/case-taking/patients/${patientId}/${system}`, { data })).data,
  getVisit: async (visitId: string, system: string): Promise<CaseRecord> =>
    (await apiClient.get(`/case-taking/visits/${visitId}/${system}`)).data,
  saveVisit: async (visitId: string, system: string, data: CaseData): Promise<CaseRecord> =>
    (await apiClient.put(`/case-taking/visits/${visitId}/${system}`, { data })).data,
}
