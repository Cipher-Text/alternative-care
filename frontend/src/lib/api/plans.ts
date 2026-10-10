import apiClient from './client'
import type {
  AdminPlansResponse,
  OverrideRequest,
  PlanAuditEntry,
  PlanConfig,
  PlanUpdateRequest,
  PublicPlansResponse,
  TenantEntitlements,
} from '@/types/plans'

export const plansApi = {
  // Public pricing (no auth)
  listPublic: async (): Promise<PublicPlansResponse> => {
    const response = await apiClient.get('/plans')
    return response.data
  },

  // Admin plan editor
  adminList: async (): Promise<AdminPlansResponse> => {
    const response = await apiClient.get('/admin/plans')
    return response.data
  },

  adminUpdate: async (key: string, payload: PlanUpdateRequest): Promise<PlanConfig> => {
    const response = await apiClient.put(`/admin/plans/${key}`, payload)
    return response.data
  },

  adminAudit: async (limit = 100): Promise<PlanAuditEntry[]> => {
    const response = await apiClient.get('/admin/plans/audit', { params: { limit } })
    return response.data
  },

  // Per-tenant entitlements and overrides (admin)
  tenantEntitlements: async (tenantId: string): Promise<TenantEntitlements> => {
    const response = await apiClient.get(`/admin/tenants/${tenantId}/entitlements`)
    return response.data
  },

  setOverride: async (
    tenantId: string,
    key: string,
    payload: OverrideRequest
  ): Promise<TenantEntitlements> => {
    const response = await apiClient.put(`/admin/tenants/${tenantId}/entitlements/${key}`, payload)
    return response.data
  },

  removeOverride: async (tenantId: string, key: string): Promise<TenantEntitlements> => {
    const response = await apiClient.delete(`/admin/tenants/${tenantId}/entitlements/${key}`)
    return response.data
  },

  // The signed-in clinic's own limits and usage
  mine: async (): Promise<TenantEntitlements> => {
    const response = await apiClient.get('/entitlements/me')
    return response.data
  },
}
