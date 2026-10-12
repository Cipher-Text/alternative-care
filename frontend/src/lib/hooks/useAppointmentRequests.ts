import { useMutation, useQuery, useQueryClient } from 'react-query'
import { appointmentRequestsApi } from '@/lib/api/appointmentRequests'
import type { ConfirmInput, RequestStatus } from '@/types/appointmentRequest'

const KEY = 'appointmentRequests'

interface ListParams {
  status?: RequestStatus
  limit?: number
  offset?: number
}

/** The clinic's appointment requests (personal data: fetched one page at a time). */
export function useAppointmentRequests(params: ListParams, enabled = true) {
  return useQuery([KEY, params], () => appointmentRequestsApi.list(params), { enabled, keepPreviousData: true })
}

/** Confirming books an appointment and may create a patient record, so those lists are refreshed too. */
export function useConfirmAppointmentRequest() {
  const queryClient = useQueryClient()
  return useMutation(({ id, data }: { id: string; data: ConfirmInput }) => appointmentRequestsApi.confirm(id, data), {
    onSuccess: () => {
      queryClient.invalidateQueries(KEY)
      queryClient.invalidateQueries('appointments')
      queryClient.invalidateQueries('appointment')
      queryClient.invalidateQueries('patients')
    },
  })
}

export function useDeclineAppointmentRequest() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ id, reason, notifySms }: { id: string; reason: string; notifySms: boolean }) =>
      appointmentRequestsApi.decline(id, reason, notifySms),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(KEY)
      },
    }
  )
}

/** Reload the list (used when a request was already answered elsewhere: `not_open`). */
export function useRefreshAppointmentRequests() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries(KEY)
}
