import apiClient from './client'
import type {
  Patient,
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
  // List all patients
  list: async (params?: PatientListParams): Promise<Patient[]> => {
    const response = await apiClient.get('/patients', { params })
    return response.data
  },

  // Get single patient
  get: async (id: string): Promise<Patient> => {
    const response = await apiClient.get(`/patients/${id}`)
    return response.data
  },

  // Create patient
  create: async (data: PatientCreateRequest): Promise<Patient> => {
    const response = await apiClient.post('/patients', data)
    return response.data
  },

  // Update patient
  update: async (id: string, data: PatientUpdateRequest): Promise<Patient> => {
    const response = await apiClient.put(`/patients/${id}`, data)
    return response.data
  },

  // Delete patient
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/patients/${id}`)
  },

  // Search patients
  search: async (query: string): Promise<Patient[]> => {
    const response = await apiClient.get('/patients/search', {
      params: { q: query },
    })
    return response.data
  },

  // Patient tags
  getTags: async (patientId: string): Promise<PatientTag[]> => {
    const response = await apiClient.get(`/patients/${patientId}/tags`)
    return response.data
  },

  addTag: async (patientId: string, tag: string): Promise<PatientTag> => {
    const response = await apiClient.post(`/patients/${patientId}/tags`, { tag })
    return response.data
  },

  deleteTag: async (patientId: string, tagId: string): Promise<void> => {
    await apiClient.delete(`/patients/${patientId}/tags/${tagId}`)
  },

  // Patient diagnoses
  getDiagnoses: async (patientId: string): Promise<PatientDiagnosis[]> => {
    const response = await apiClient.get(`/patients/${patientId}/diagnoses`)
    return response.data
  },

  addDiagnosis: async (
    patientId: string,
    data: {
      diagnosis: string
      diagnosed_at?: string
      notes?: string
    }
  ): Promise<PatientDiagnosis> => {
    const response = await apiClient.post(`/patients/${patientId}/diagnoses`, data)
    return response.data
  },

  updateDiagnosis: async (
    patientId: string,
    diagnosisId: string,
    data: {
      diagnosis?: string
      diagnosed_at?: string
      notes?: string
    }
  ): Promise<PatientDiagnosis> => {
    const response = await apiClient.put(
      `/patients/${patientId}/diagnoses/${diagnosisId}`,
      data
    )
    return response.data
  },

  deleteDiagnosis: async (patientId: string, diagnosisId: string): Promise<void> => {
    await apiClient.delete(`/patients/${patientId}/diagnoses/${diagnosisId}`)
  },
}

// Geographic API (for address fields)
export const geographicApi = {
  // Get all divisions
  getDivisions: async (): Promise<Division[]> => {
    const response = await apiClient.get('/geographic/divisions')
    return response.data
  },

  // Get districts by division
  getDistricts: async (divisionId: string): Promise<District[]> => {
    const response = await apiClient.get(`/geographic/divisions/${divisionId}/districts`)
    return response.data
  },

  // Get upazilas by district
  getUpazilas: async (districtId: string): Promise<Upazila[]> => {
    const response = await apiClient.get(`/geographic/districts/${districtId}/upazilas`)
    return response.data
  },
}
