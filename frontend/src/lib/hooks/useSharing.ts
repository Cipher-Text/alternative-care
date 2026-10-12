import { useMutation, useQuery, useQueryClient } from 'react-query'
import { patientPortalApi } from '@/lib/api/patientPortal'
import { identityApi } from '@/lib/api/identity'
import type { ShareInput } from '@/types/sharing'

/** Portal side: under the portal root so signing out (removeQueries('patientPortal')) clears it. */
const portalSharesKey = ['patientPortal', 'shares']
/** Clinic side. */
const sharingKey = (patientId: string) => ['sharing', patientId]
const sharedRecordsKey = (patientId: string) => ['sharing', patientId, 'records']

/** Everything the signed-in patient shared, with who read it. */
export function usePortalShares(enabled: boolean) {
  return useQuery(portalSharesKey, () => patientPortalApi.shares(), {
    enabled: enabled && patientPortalApi.hasSession(),
    retry: false,
    refetchOnWindowFocus: false,
  })
}

/** Share one clinic's records with another (the API needs a recent sign-in). */
export function useCreateShare() {
  const queryClient = useQueryClient()
  return useMutation((data: ShareInput) => patientPortalApi.createShare(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(portalSharesKey)
    },
  })
}

/** Stop a share. Access ends at once because nothing was copied. */
export function useRevokeShare() {
  const queryClient = useQueryClient()
  return useMutation((id: string) => patientPortalApi.revokeShare(id), {
    onSuccess: () => {
      queryClient.invalidateQueries(portalSharesKey)
    },
  })
}

/** Clinic side: names, dates and read counts only. Never loads the records themselves. */
export function usePatientSharing(patientId: string, enabled = true) {
  return useQuery(sharingKey(patientId), () => identityApi.sharing(patientId), {
    enabled: enabled && !!patientId,
    staleTime: 30000,
    retry: false,
  })
}

/**
 * Doctors only. Every successful load is logged and visible to the patient, so it must not reload by itself
 * (no refetch on focus, reconnect or interval) and is not kept in the cache after the page is left.
 */
export function useSharedRecords(patientId: string, enabled: boolean) {
  return useQuery(sharedRecordsKey(patientId), () => identityApi.sharedRecords(patientId), {
    enabled: enabled && !!patientId,
    retry: false,
    cacheTime: 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: 'always',
  })
}
