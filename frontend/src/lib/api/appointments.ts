import apiClient from './client'
import type {
  Appointment,
  AppointmentCreateRequest,
  AppointmentUpdateRequest,
  AppointmentListParams,
} from '@/types/appointment'

export const appointmentsApi = {
  list: async (params?: AppointmentListParams): Promise<Appointment[]> => {
    const response = await apiClient.get('/appointments', { params })
    return response.data
  },

  create: async (data: AppointmentCreateRequest): Promise<Appointment> => {
    const response = await apiClient.post('/appointments', data)
    return response.data
  },

  get: async (id: string): Promise<Appointment> => {
    const response = await apiClient.get(`/appointments/${id}`)
    return response.data
  },

  update: async (id: string, data: AppointmentUpdateRequest): Promise<Appointment> => {
    const response = await apiClient.patch(`/appointments/${id}`, data)
    return response.data
  },
}
