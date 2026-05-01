import { useQuery } from 'react-query'
import { dashboardApi } from '@/lib/api/dashboard'
import type { DateRangeFilter } from '@/types/dashboard'

export function useOverviewStats(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'overview', params], () =>
    dashboardApi.getOverview(params)
  )
}

export function useFinancialAnalytics(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'financial', params], () =>
    dashboardApi.getFinancial(params)
  )
}

export function usePatientAnalytics(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'patients', params], () =>
    dashboardApi.getPatients(params)
  )
}

export function useAppointmentAnalytics(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'appointments', params], () =>
    dashboardApi.getAppointments(params)
  )
}

export function useVisitAnalytics(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'visits', params], () =>
    dashboardApi.getVisits(params)
  )
}

export function usePrescriptionAnalytics(params?: DateRangeFilter) {
  return useQuery(['dashboard', 'prescriptions', params], () =>
    dashboardApi.getPrescriptions(params)
  )
}
