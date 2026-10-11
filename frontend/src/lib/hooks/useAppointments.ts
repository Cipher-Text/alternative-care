import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { appointmentsApi } from '@/lib/api/appointments'
import type {
  AppointmentCreateRequest,
  AppointmentListParams,
  AppointmentUpdateRequest,
} from '@/types/appointment'

export function useAppointments(params?: AppointmentListParams) {
  return useQuery(['appointments', params], () => appointmentsApi.list(params), {
    staleTime: 30000,
  })
}

export function useAppointment(id: string) {
  return useQuery(['appointment', id], () => appointmentsApi.get(id), {
    enabled: !!id,
    staleTime: 30000,
  })
}

export function useCreateAppointment() {
  const t = useTranslations('apptHooksUi')
  const queryClient = useQueryClient()

  return useMutation((data: AppointmentCreateRequest) => appointmentsApi.create(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('appointments')
      toast.success(t('created'))
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('createFailed'))
    },
  })
}

export function useUpdateAppointment() {
  const t = useTranslations('apptHooksUi')
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: string; data: AppointmentUpdateRequest }) =>
      appointmentsApi.update(id, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries('appointments')
        queryClient.invalidateQueries(['appointment', variables.id])
        toast.success(t('updated'))
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || t('updateFailed'))
      },
    }
  )
}
