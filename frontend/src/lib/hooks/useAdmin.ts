import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { AxiosError } from 'axios'
import { adminApi } from '@/lib/api/admin'
import type {
  AdminProvisionRequest,
  AdminUpdateTenantRequest,
  AdminUpdateUserRequest,
} from '@/types/admin'

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    return detail || fallback
  }
  return fallback
}

// ============================================================================
// Dashboard
// ============================================================================

export function useAdminDashboard(enabled = true) {
  return useQuery(['admin', 'dashboard'], () => adminApi.getDashboard(), {
    enabled,
    staleTime: 30000,
  })
}

// ============================================================================
// Tenants
// ============================================================================

export function useAdminTenants(enabled = true) {
  return useQuery(['admin', 'tenants'], () => adminApi.listTenants(), {
    enabled,
    staleTime: 30000,
  })
}

export function useAdminTenantDetail(tenantId: string, enabled = true) {
  return useQuery(
    ['admin', 'tenants', tenantId],
    () => adminApi.getTenantDetail(tenantId),
    {
      enabled: enabled && Boolean(tenantId),
      staleTime: 30000,
    }
  )
}

export function useAdminPendingTenants(enabled = true) {
  return useQuery(['admin', 'tenants-pending'], () => adminApi.listPendingTenants(), {
    enabled,
    staleTime: 30000,
  })
}

export function useProvisionTenant() {
  const queryClient = useQueryClient()

  return useMutation((data: AdminProvisionRequest) => adminApi.provisionTenant(data), {
    onSuccess: (data) => {
      queryClient.invalidateQueries(['admin', 'tenants'])
      queryClient.invalidateQueries(['admin', 'tenants-pending'])
      queryClient.invalidateQueries(['admin', 'dashboard'])
      toast.success(data.message || 'Client account created')
    },
    onError: (error: unknown) => {
      toast.error(getErrorMessage(error, 'Failed to provision client'))
    },
  })
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

export function useUpdateTenant() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ tenantId, data }: { tenantId: string; data: AdminUpdateTenantRequest }) =>
      adminApi.updateTenant(tenantId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin', 'tenants'])
        queryClient.invalidateQueries(['admin', 'dashboard'])
        toast.success('Tenant updated')
      },
      onError: (error: unknown) => {
        toast.error(getErrorMessage(error, 'Failed to update tenant'))
      },
    }
  )
}

// ============================================================================
// Users / role distribution
// ============================================================================

export function useAdminUsers(
  params?: { role?: string; tenant_id?: string; is_active?: boolean },
  enabled = true
) {
  return useQuery(
    ['admin', 'users', params],
    () => adminApi.listUsers(params),
    {
      enabled,
      staleTime: 30000,
    }
  )
}

export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ userId, data }: { userId: string; data: AdminUpdateUserRequest }) =>
      adminApi.updateUser(userId, data),
    {
      onSuccess: (response) => {
        queryClient.invalidateQueries(['admin', 'users'])
        queryClient.invalidateQueries(['admin', 'dashboard'])
        toast.success(response.message || 'User updated')
      },
      onError: (error: unknown) => {
        toast.error(getErrorMessage(error, 'Failed to update user'))
      },
    }
  )
}
