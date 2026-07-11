import apiClient from './client'
import type {
  AdminDashboard,
  AdminTenantListItem,
  AdminTenantDetail,
  AdminTenantItem,
  AdminUpdateTenantRequest,
  AdminProvisionRequest,
  AdminProvisionResponse,
  AdminUsersResponse,
  AdminUpdateUserRequest,
  AdminUpdateUserResponse,
} from '@/types/admin'

export const adminApi = {
  // Dashboard
  getDashboard: async (): Promise<AdminDashboard> => {
    const response = await apiClient.get('/admin/dashboard')
    return response.data
  },

  // Tenants
  listTenants: async (): Promise<AdminTenantListItem[]> => {
    const response = await apiClient.get('/admin/tenants')
    return response.data
  },

  getTenantDetail: async (tenantId: string): Promise<AdminTenantDetail> => {
    const response = await apiClient.get(`/admin/tenants/${tenantId}`)
    return response.data
  },

  listPendingTenants: async (): Promise<AdminTenantItem[]> => {
    const response = await apiClient.get('/admin/tenants/pending')
    return response.data
  },

  provisionTenant: async (data: AdminProvisionRequest): Promise<AdminProvisionResponse> => {
    const response = await apiClient.post('/admin/tenants', data)
    return response.data
  },

  approveTenant: async (tenantId: string): Promise<AdminTenantItem> => {
    const response = await apiClient.post(`/admin/tenants/${tenantId}/approve`)
    return response.data
  },

  updateTenant: async (tenantId: string, data: AdminUpdateTenantRequest): Promise<AdminTenantItem> => {
    const response = await apiClient.patch(`/admin/tenants/${tenantId}`, data)
    return response.data
  },

  // Users
  listUsers: async (params?: {
    role?: string
    tenant_id?: string
    is_active?: boolean
  }): Promise<AdminUsersResponse> => {
    const response = await apiClient.get('/admin/users', { params })
    return response.data
  },

  updateUser: async (
    userId: string,
    data: AdminUpdateUserRequest
  ): Promise<AdminUpdateUserResponse> => {
    const response = await apiClient.patch(`/admin/users/${userId}`, data)
    return response.data
  },
}
