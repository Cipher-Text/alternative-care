/**
 * Admin client hooks, backed by the /admin/* endpoints.
 * The legacy /auth/admin/* endpoints have been removed.
 */
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { AxiosError } from 'axios'
import { adminApi } from '@/lib/api/admin'
import type { AdminAddTenantDoctorRequest, AdminProvisionRequest } from '@/types/admin'

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    return detail || fallback
  }
  return fallback
}

export function usePendingTenants(enabled = true) {
  return useQuery(['admin', 'tenants-pending'], () => adminApi.listPendingTenants(), {
    enabled,
    staleTime: 30000,
  })
}

export function useAdminClients(enabled = true) {
  return useQuery(['admin', 'tenants'], () => adminApi.listTenants(), {
    enabled,
    staleTime: 30000,
  })
}

export function useAdminClient(tenantId: string, enabled = true) {
  return useQuery(
    ['admin', 'tenants', tenantId],
    () => adminApi.getTenantDetail(tenantId),
    {
      enabled: enabled && Boolean(tenantId),
      staleTime: 30000,
    }
  )
}

export function useProvisionClient() {
  const queryClient = useQueryClient()

  return useMutation(
    (payload: AdminProvisionRequest) => adminApi.provisionTenant(payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['admin', 'tenants'])
        queryClient.invalidateQueries(['admin', 'tenants-pending'])
        queryClient.invalidateQueries(['admin', 'dashboard'])
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

  return useMutation((tenantId: string) => adminApi.approveTenant(tenantId), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin', 'tenants'])
      queryClient.invalidateQueries(['admin', 'tenants-pending'])
      queryClient.invalidateQueries(['admin', 'dashboard'])
      toast.success('Tenant approved')
    },
    onError: (error: unknown) => {
      toast.error(getErrorMessage(error, 'Failed to approve tenant'))
    },
  })
}

export function useCreateTenantDoctor(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation(
    (payload: AdminAddTenantDoctorRequest) => adminApi.createTenantDoctor(tenantId, payload),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['admin', 'tenants'])
        queryClient.invalidateQueries(['admin', 'tenants', tenantId])
        queryClient.invalidateQueries(['admin', 'dashboard'])
        queryClient.invalidateQueries(['admin', 'users'])
        toast.success(data.message || 'Doctor added to clinic')
      },
      onError: (error: unknown) => {
        toast.error(getErrorMessage(error, 'Failed to add doctor'))
      },
    }
  )
}
