import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { appointmentsApi } from '@/lib/api/appointments'
import type { AppointmentCreateRequest, AppointmentListParams } from '@/types/appointment'

export function useAppointments(params?: AppointmentListParams) {
  return useQuery(['appointments', params], () => appointmentsApi.list(params), {
    staleTime: 30000,
  })
}

export function useCreateAppointment() {
  const queryClient = useQueryClient()

  return useMutation((data: AppointmentCreateRequest) => appointmentsApi.create(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('appointments')
      toast.success('Appointment created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create appointment')
    },
  })
}
