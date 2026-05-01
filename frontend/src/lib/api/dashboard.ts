import apiClient from './client'
import type {
  DateRangeFilter,
  OverviewStats,
  FinancialAnalytics,
  PatientAnalytics,
  AppointmentAnalytics,
  VisitAnalytics,
  PrescriptionAnalytics,
} from '@/types/dashboard'

export const dashboardApi = {
  // Overview stats
  getOverview: async (params?: DateRangeFilter): Promise<OverviewStats> => {
    const response = await apiClient.get('/dashboard/overview', { params })
    return response.data
  },

  // Financial analytics
  getFinancial: async (params?: DateRangeFilter): Promise<FinancialAnalytics> => {
    const response = await apiClient.get('/dashboard/financial', { params })
    return response.data
  },

  // Patient analytics
  getPatients: async (params?: DateRangeFilter): Promise<PatientAnalytics> => {
    const response = await apiClient.get('/dashboard/patients', { params })
    return response.data
  },

  // Appointment analytics
  getAppointments: async (params?: DateRangeFilter): Promise<AppointmentAnalytics> => {
    const response = await apiClient.get('/dashboard/appointments', { params })
    return response.data
  },

  // Visit analytics
  getVisits: async (params?: DateRangeFilter): Promise<VisitAnalytics> => {
    const response = await apiClient.get('/dashboard/visits', { params })
    return response.data
  },

  // Prescription analytics
  getPrescriptions: async (params?: DateRangeFilter): Promise<PrescriptionAnalytics> => {
    const response = await apiClient.get('/dashboard/prescriptions', { params })
    return response.data
  },
}
