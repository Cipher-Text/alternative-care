import apiClient from './client'
import type {
  LoginRequest,
  LoginResponse,
  TwoFactorRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserProfileResponse,
  AdminCreateTenantDoctorRequest,
  RegisterResponse,
  TenantResponse,
} from '@/types/auth'

export const authApi = {
  // Login
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login', data)
    return response.data
  },

  // Login with 2FA
  loginWith2FA: async (data: TwoFactorRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login-2fa', data)
    return response.data
  },

  // Refresh token
  refresh: async (data: RefreshTokenRequest): Promise<RefreshTokenResponse> => {
    const response = await apiClient.post('/auth/refresh', data)
    return response.data
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  // Get current user
  getCurrentUser: async (): Promise<UserProfileResponse> => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  // Admin: provision tenant + primary doctor
  provisionClient: async (data: AdminCreateTenantDoctorRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post('/auth/admin/provision-client', data)
    return response.data
  },

  // Admin: list tenants pending approval
  listPendingTenants: async (): Promise<TenantResponse[]> => {
    const response = await apiClient.get('/auth/admin/tenants/pending')
    return response.data
  },

  // Admin: approve tenant
  approveTenant: async (tenantId: string): Promise<TenantResponse> => {
    const response = await apiClient.post(`/auth/admin/tenants/${tenantId}/approve`)
    return response.data
  },
}
