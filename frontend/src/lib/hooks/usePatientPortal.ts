import { useMutation, useQuery, useQueryClient } from 'react-query'
import { patientPortalApi } from '@/lib/api/patientPortal'

/** Every patient portal query lives under this key so signing out can drop them all. */
const ROOT = 'patientPortal'
const meKey = [ROOT, 'me']
const recordsKey = (profileId: string) => [ROOT, 'records', profileId]

/** The signed-in patient's profiles and clinics. Only runs while a portal session exists. */
export function usePortalMe(enabled: boolean) {
  return useQuery(meKey, () => patientPortalApi.me(), { enabled, retry: false, refetchOnWindowFocus: false })
}

/** Read-only records of one profile. */
export function usePortalRecords(profileId: string | undefined) {
  return useQuery(recordsKey(profileId ?? ''), () => patientPortalApi.records(profileId as string), {
    enabled: !!profileId && patientPortalApi.hasSession(),
    retry: false,
    refetchOnWindowFocus: false,
  })
}

/** Enter a clinic's portal code; refreshes the account so the clinic shows up. */
export function useActivatePortalCode() {
  const queryClient = useQueryClient()
  return useMutation((code: string) => patientPortalApi.activate(code), {
    onSuccess: () => {
      queryClient.invalidateQueries(ROOT)
    },
  })
}

/** Remove a clinic from the account (the clinic keeps its own record). */
export function useRevokePortalLink() {
  const queryClient = useQueryClient()
  return useMutation((linkId: string) => patientPortalApi.revoke(linkId), {
    onSuccess: () => {
      queryClient.invalidateQueries(ROOT)
    },
  })
}

/** Ends the portal session and removes everything cached from it. */
export function usePortalSignOut() {
  const queryClient = useQueryClient()
  return () => {
    patientPortalApi.signOut()
    queryClient.removeQueries(ROOT)
  }
}
