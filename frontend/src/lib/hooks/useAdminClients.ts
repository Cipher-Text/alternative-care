import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { AxiosError } from 'axios'
import { authApi } from '@/lib/api/auth'
import type { AdminCreateTenantDoctorRequest } from '@/types/auth'

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    return detail || fallback
  }

  return fallback
}

export function usePendingTenants(enabled = true) {
  return useQuery(['admin', 'pending-tenants'], () => authApi.listPendingTenants(), {
    enabled,
    staleTime: 30000,
  })
}

export function useProvisionClient() {
  const queryClient = useQueryClient()

  return useMutation(
    (payload: AdminCreateTenantDoctorRequest) => authApi.provisionClient(payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['admin', 'pending-tenants'])
        toast.success(data.message || 'Client account created')
      },
      onError: (error: unknown) => {
        toast.error(getErrorMessage(error, 'Failed to provision client'))
      },
    }
  )
}

export function useApproveTenant() {
  const queryClient = useQueryClient()

  return useMutation((tenantId: string) => authApi.approveTenant(tenantId), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin', 'pending-tenants'])
      toast.success('Tenant approved')
    },
    onError: (error: unknown) => {
      toast.error(getErrorMessage(error, 'Failed to approve tenant'))
    },
  })
}
