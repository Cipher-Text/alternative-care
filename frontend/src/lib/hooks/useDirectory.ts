import { useQuery, useMutation, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { directoryApi, verifyTenant } from '@/lib/api/directory'
import type { ListingInput, RequestStatus } from '@/types/directory'

type ApiError = { response?: { data?: { detail?: unknown } } }

/** The API's `detail` is a string for our own errors and an array for validation errors. */
function detailOf(error: unknown): string | undefined {
  const detail = (error as ApiError)?.response?.data?.detail
  return typeof detail === 'string' ? detail : undefined
}

export function useDirectoryListing(enabled = true) {
  return useQuery(['directory', 'listing'], () => directoryApi.getListing(), {
    enabled,
    staleTime: 30000,
  })
}

export function useSaveListing() {
  const t = useTranslations('directoryAdminUi')
  const queryClient = useQueryClient()
  return useMutation((data: ListingInput) => directoryApi.saveListing(data), {
    onSuccess: (listing) => {
      queryClient.setQueryData(['directory', 'listing'], listing)
      toast.success(t('toast.saved'))
    },
    onError: (error) => {
      toast.error(detailOf(error) || t('toast.saveFailed'))
    },
  })
}

/** `silent` callers (the dashboard card) get no retries and no error UI: they just hide. */
export function useDirectoryStats(enabled = true) {
  return useQuery(['directory', 'stats'], () => directoryApi.stats(), {
    enabled,
    staleTime: 60000,
    retry: false,
  })
}

export function useDirectoryRequests(params?: { status?: RequestStatus; limit?: number; offset?: number }) {
  return useQuery(['directory', 'requests', params], () => directoryApi.requests(params), {
    staleTime: 15000,
    keepPreviousData: true,
  })
}

export function useUpdateRequestStatus() {
  const t = useTranslations('directoryAdminUi')
  const queryClient = useQueryClient()
  return useMutation(
    ({ id, status }: { id: string; status: RequestStatus }) => directoryApi.updateRequest(id, status),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['directory', 'requests'])
        queryClient.invalidateQueries(['directory', 'stats'])
        toast.success(t('toast.requestUpdated'))
      },
      onError: (error) => {
        toast.error(detailOf(error) || t('toast.requestFailed'))
      },
    }
  )
}

/** Admin: verify or remove verification for a tenant. */
export function useVerifyTenant(tenantId: string) {
  const t = useTranslations('directoryAdminUi')
  const queryClient = useQueryClient()
  return useMutation((data: { verified: boolean; note?: string }) => verifyTenant(tenantId, data), {
    onSuccess: (result) => {
      queryClient.invalidateQueries(['admin', 'tenants'])
      toast.success(result.is_verified ? t('verification.doneVerified') : t('verification.doneRemoved'))
    },
    onError: (error) => {
      toast.error(detailOf(error) || t('verification.failed'))
    },
  })
}
