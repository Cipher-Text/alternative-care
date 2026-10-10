import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { plansApi } from '@/lib/api/plans'
import { getErrorMessage } from '@/types/api'
import type { OverrideRequest, PlanUpdateRequest } from '@/types/plans'

export function usePublicPlans() {
  return useQuery(['plans', 'public'], () => plansApi.listPublic(), {
    staleTime: 60000,
    retry: false,
  })
}

export function useAdminPlans() {
  return useQuery(['admin', 'plans'], () => plansApi.adminList())
}

export function usePlanAudit() {
  return useQuery(['admin', 'plans', 'audit'], () => plansApi.adminAudit())
}

export function useUpdatePlan() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ key, payload }: { key: string; payload: PlanUpdateRequest }) =>
      plansApi.adminUpdate(key, payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin', 'plans'])
        queryClient.invalidateQueries(['plans', 'public'])
        toast.success('Plan saved')
      },
      onError: (error) => {
        toast.error(getErrorMessage(error, 'Failed to save plan'))
      },
    }
  )
}

export function useTenantEntitlements(tenantId: string) {
  return useQuery(['admin', 'tenant-entitlements', tenantId], () =>
    plansApi.tenantEntitlements(tenantId)
  )
}

export function useSetTenantOverride(tenantId: string) {
  const queryClient = useQueryClient()
  return useMutation(
    ({ key, payload }: { key: string; payload: OverrideRequest }) =>
      plansApi.setOverride(tenantId, key, payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin', 'tenant-entitlements', tenantId])
        queryClient.invalidateQueries(['admin', 'plans', 'audit'])
        toast.success('Override saved')
      },
      onError: (error) => {
        toast.error(getErrorMessage(error, 'Failed to save override'))
      },
    }
  )
}

export function useRemoveTenantOverride(tenantId: string) {
  const queryClient = useQueryClient()
  return useMutation((key: string) => plansApi.removeOverride(tenantId, key), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin', 'tenant-entitlements', tenantId])
      queryClient.invalidateQueries(['admin', 'plans', 'audit'])
      toast.success('Override removed')
    },
    onError: (error) => {
        toast.error(getErrorMessage(error, 'Failed to remove override'))
      },
  })
}

export function useMyEntitlements(enabled = true) {
  return useQuery(['entitlements', 'me'], () => plansApi.mine(), { enabled, staleTime: 30000 })
}
