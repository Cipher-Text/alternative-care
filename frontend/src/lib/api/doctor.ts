import apiClient from './client'
import type {
  DoctorProfile,
  DoctorProfileUpdate,
  DoctorDegree,
  DoctorDegreeCreate,
  DoctorDegreeUpdate,
  DoctorTraining,
  DoctorTrainingCreate,
  DoctorTrainingUpdate,
} from '@/types/doctor'

export const doctorApi = {
  // ===== Profile =====

  // Get doctor profile
  getProfile: async (): Promise<DoctorProfile> => {
    const response = await apiClient.get('/doctor/profile')
    return response.data
  },

  // Update doctor profile
  updateProfile: async (data: DoctorProfileUpdate): Promise<DoctorProfile> => {
    const response = await apiClient.patch('/doctor/profile', data)
    return response.data
  },

  // ===== Degrees =====

  // List degrees
  listDegrees: async (): Promise<DoctorDegree[]> => {
    const response = await apiClient.get('/doctor/degrees')
    return response.data
  },

  // Get single degree
  getDegree: async (id: number): Promise<DoctorDegree> => {
    const response = await apiClient.get(`/doctor/degrees/${id}`)
    return response.data
  },

  // Create degree
  createDegree: async (data: DoctorDegreeCreate): Promise<DoctorDegree> => {
    const response = await apiClient.post('/doctor/degrees', data)
    return response.data
  },

  // Update degree
  updateDegree: async (id: number, data: DoctorDegreeUpdate): Promise<DoctorDegree> => {
    const response = await apiClient.patch(`/doctor/degrees/${id}`, data)
    return response.data
  },

  // Delete degree
  deleteDegree: async (id: number): Promise<void> => {
    await apiClient.delete(`/doctor/degrees/${id}`)
  },

  // ===== Trainings =====

  // List trainings
  listTrainings: async (activeOnly?: boolean): Promise<DoctorTraining[]> => {
    const response = await apiClient.get('/doctor/trainings', {
      params: { active_only: activeOnly },
    })
    return response.data
  },

  // Get single training
  getTraining: async (id: number): Promise<DoctorTraining> => {
    const response = await apiClient.get(`/doctor/trainings/${id}`)
    return response.data
  },

  // Create training
  createTraining: async (data: DoctorTrainingCreate): Promise<DoctorTraining> => {
    const response = await apiClient.post('/doctor/trainings', data)
    return response.data
  },

  // Update training
  updateTraining: async (id: number, data: DoctorTrainingUpdate): Promise<DoctorTraining> => {
    const response = await apiClient.patch(`/doctor/trainings/${id}`, data)
    return response.data
  },

  // Delete training
  deleteTraining: async (id: number): Promise<void> => {
    await apiClient.delete(`/doctor/trainings/${id}`)
  },
}
