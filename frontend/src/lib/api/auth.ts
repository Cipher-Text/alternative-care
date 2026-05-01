import apiClient from './client'
import type {
  LoginRequest,
  LoginResponse,
  TwoFactorRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  User,
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
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}
