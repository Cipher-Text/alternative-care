/**
 * Pharmacy directory React Query hooks
 */

import { useMutation, useQueries, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { AxiosError } from 'axios'
import { pharmaciesApi } from '@/lib/api/pharmacies'
import { geographicApi } from '@/lib/api/patients'
import type { PharmacyFilters, PharmacyInput, PharmacyUpdate } from '@/types/pharmacy'
import type { District, Division } from '@/types/patient'

const KEY = 'pharmacies'

/** Pull a readable message out of an API error (422 details arrive as a list). */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string; loc?: Array<string | number> }
      const field = first.loc?.filter((p) => p !== 'body').join('.')
      return field ? `${field}: ${first.msg}` : (first.msg ?? fallback)
    }
  }
  return fallback
}

export function usePharmacies(filters?: PharmacyFilters, enabled = true) {
  return useQuery([KEY, filters], () => pharmaciesApi.list(filters), {
    enabled,
    staleTime: 30000,
    keepPreviousData: true, // no flash of an empty list while paging or searching
  })
}

export function usePharmacy(id: number | null, enabled = true) {
  return useQuery([KEY, 'detail', id], () => pharmaciesApi.get(id as number), {
    enabled: enabled && id !== null,
    staleTime: 0, // always edit the latest saved version
  })
}

export function useCreatePharmacy(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient()
  return useMutation((data: PharmacyInput) => pharmaciesApi.create(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(KEY)
      toast.success('Pharmacy added')
      options?.onSuccess?.()
    },
    onError: (error) => {
      toast.error(apiErrorMessage(error, 'Could not add the pharmacy'))
    },
  })
}

export function useUpdatePharmacy(options?: { onSuccess?: () => void; quiet?: boolean }) {
  const queryClient = useQueryClient()
  return useMutation(
    ({ id, data }: { id: number; data: PharmacyUpdate }) => pharmaciesApi.update(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(KEY)
        if (!options?.quiet) toast.success('Pharmacy updated')
        options?.onSuccess?.()
      },
      onError: (error) => {
      toast.error(apiErrorMessage(error, 'Could not update the pharmacy'))
    },
    }
  )
}

export function useDeactivatePharmacy() {
  const queryClient = useQueryClient()
  return useMutation((id: number) => pharmaciesApi.deactivate(id), {
    onSuccess: () => {
      queryClient.invalidateQueries(KEY)
      toast.success('Pharmacy deactivated')
    },
    onError: (error) => {
      toast.error(apiErrorMessage(error, 'Could not deactivate the pharmacy'))
    },
  })
}

export function useImportPharmacies() {
  const queryClient = useQueryClient()
  return useMutation((file: File) => pharmaciesApi.importCsv(file), {
    // The result (including per-row errors) is shown in the dialog, so no toast here
    onSuccess: (result) => {
      if (result.created > 0) queryClient.invalidateQueries(KEY)
    },
  })
}

/**
 * Every district in the country (64), loaded as one request per division and cached forever
 * (shares query keys with `useDistricts`). Returned sorted by name.
 */
export function useAllDistricts(divisions: Division[] | undefined) {
  const results = useQueries(
    (divisions ?? []).map((division) => ({
      queryKey: ['districts', division.id],
      queryFn: () => geographicApi.getDistricts(division.id),
      staleTime: Infinity,
    }))
  )
  const districts: District[] = results
    .flatMap((r) => (r.data as District[] | undefined) ?? [])
    .sort((a, b) => a.name_en.localeCompare(b.name_en))
  return { districts, isLoading: results.some((r) => r.isLoading) }
}
