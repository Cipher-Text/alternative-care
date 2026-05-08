import apiClient from './client'
import type {
  Appointment,
  AppointmentCreateRequest,
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
}
