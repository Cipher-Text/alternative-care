import apiClient from './client'
import type {
  Patient,
  PatientListItem,
  PatientCreateRequest,
  PatientUpdateRequest,
  PatientListParams,
  PatientTag,
  PatientDiagnosis,
  Division,
  District,
  Upazila,
} from '@/types/patient'

export const patientsApi = {
  list: async (params?: PatientListParams): Promise<PatientListItem[]> => {
    const response = await apiClient.get('/patients', { params })
    return response.data
  },

  get: async (id: string): Promise<Patient> => {
    const response = await apiClient.get(`/patients/${id}`)
    return response.data
  },

  create: async (data: PatientCreateRequest): Promise<Patient> => {
    const response = await apiClient.post('/patients', data)
    return response.data
  },

  update: async (id: string, data: PatientUpdateRequest): Promise<Patient> => {
    const response = await apiClient.patch(`/patients/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<Patient> => {
    const response = await apiClient.delete(`/patients/${id}`)
    return response.data
  },

  // Patient tags
  getTags: async (patientId: string): Promise<PatientTag[]> => {
    const response = await apiClient.get(`/patients/${patientId}/tags`)
    return response.data
  },

  addTag: async (
    patientId: string,
    data: { tag_type: PatientTag['tag_type']; tag_value: string; notes?: string }
  ): Promise<PatientTag> => {
    const response = await apiClient.post(`/patients/${patientId}/tags`, data)
    return response.data
  },

  deleteTag: async (tagId: number): Promise<void> => {
    await apiClient.delete(`/patients/tags/${tagId}`)
  },

  // Patient diagnoses
  getDiagnoses: async (patientId: string): Promise<PatientDiagnosis[]> => {
    const response = await apiClient.get(`/patients/${patientId}/diagnoses`)
    return response.data
  },

  addDiagnosis: async (
    patientId: string,
    data: { description: string; icd_code?: string; diagnosed_at: string }
  ): Promise<PatientDiagnosis> => {
    const response = await apiClient.post(`/patients/${patientId}/diagnoses`, data)
    return response.data
  },

  updateDiagnosis: async (
    diagnosisId: number,
    data: { description?: string; icd_code?: string; diagnosed_at?: string; is_active?: boolean }
  ): Promise<PatientDiagnosis> => {
    const response = await apiClient.patch(`/patients/diagnoses/${diagnosisId}`, data)
    return response.data
  },

  deleteDiagnosis: async (diagnosisId: number): Promise<PatientDiagnosis> => {
    const response = await apiClient.delete(`/patients/diagnoses/${diagnosisId}`)
    return response.data
  },
}

// Geographic API
export const geographicApi = {
  getDivisions: async (): Promise<Division[]> => {
    const response = await apiClient.get('/geographic/divisions')
    return response.data
  },

  getDistricts: async (divisionId: number): Promise<District[]> => {
    const response = await apiClient.get(`/geographic/divisions/${divisionId}/districts`)
    return response.data
  },

  getUpazilas: async (districtId: number): Promise<Upazila[]> => {
    const response = await apiClient.get(`/geographic/districts/${districtId}/upazilas`)
    return response.data
  },
}
