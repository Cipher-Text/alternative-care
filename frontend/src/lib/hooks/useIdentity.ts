import { useMutation, useQuery, useQueryClient } from 'react-query'
import { identityApi } from '@/lib/api/identity'
import { authApi } from '@/lib/api/auth'
import type { LinkInput } from '@/types/identity'

const statusKey = (patientId: string) => ['identity', 'status', patientId]

/** Whether the patient record is level 0 (clinic-entered) or level 1 (phone-verified and linked). */
export function usePatientIdentity(patientId: string) {
  return useQuery(statusKey(patientId), () => identityApi.status(patientId), {
    enabled: !!patientId,
    staleTime: 30000,
    retry: false,
  })
}

/** Link a clinic patient record to a verified profile (needs a fresh verification token). */
export function useLinkIdentity() {
  const queryClient = useQueryClient()
  return useMutation((data: LinkInput) => identityApi.link(data), {
    onSuccess: (res) => {
      queryClient.invalidateQueries(statusKey(res.patient_id))
    },
  })
}

/** Doctor only: remove the link. The clinic keeps its own record. */
export function useRevokeIdentity(patientId: string) {
  const queryClient = useQueryClient()
  return useMutation((note?: string) => identityApi.revoke(patientId, note), {
    onSuccess: () => {
      queryClient.invalidateQueries(statusKey(patientId))
    },
  })
}

/** Create a one-time claim code. The code is only returned here, so it is not cached. */
export function useCreateClaimCode(patientId: string) {
  return useMutation(() => identityApi.createClaimCode(patientId))
}

/** The signed-in user's clinic name, for the consent script. Undefined while loading or unavailable. */
export function useClinicName(enabled = true): string | undefined {
  const { data } = useQuery('identityClinicName', () => authApi.getCurrentUser(), {
    enabled,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  return data?.tenant?.clinic_name || data?.tenant?.name || undefined
}
