import { useMutation, useQuery, useQueryClient } from 'react-query'
import { patientPortalApi } from '@/lib/api/patientPortal'
import type { AppointmentRequestInput, PortalProfileInput } from '@/types/appointmentRequest'

/** Every patient portal query lives under this key so signing out can drop them all. */
const ROOT = 'patientPortal'
const meKey = [ROOT, 'me']
const requestsKey = [ROOT, 'requests']
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

/** The signed-in patient's appointment requests, newest first. */
export function usePortalRequests(enabled: boolean) {
  return useQuery(requestsKey, async () => {
    const items = await patientPortalApi.requests()
    return [...items].sort((a, b) => b.created_at.localeCompare(a.created_at))
  }, { enabled, retry: false, refetchOnWindowFocus: false })
}

/** Add yourself or a child; the account's profiles and records are reloaded. */
export function useAddPortalProfile() {
  const queryClient = useQueryClient()
  return useMutation((data: PortalProfileInput) => patientPortalApi.addProfile(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(ROOT)
    },
  })
}

/** Ask a practitioner for an appointment (asking is the consent to share basic details with the clinic). */
export function useRequestAppointment() {
  const queryClient = useQueryClient()
  return useMutation((data: AppointmentRequestInput) => patientPortalApi.requestAppointment(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(ROOT)
    },
  })
}

/** Cancel a waiting request or a confirmed appointment that has not happened yet. */
export function useCancelPortalRequest() {
  const queryClient = useQueryClient()
  return useMutation((id: string) => patientPortalApi.cancelRequest(id), {
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
