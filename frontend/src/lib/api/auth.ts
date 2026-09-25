import apiClient from './client'
import type {
  LoginRequest,
  LoginResponse,
  TwoFactorRequest,
  GoogleLoginRequest,
  GoogleAuthResponse,
  GoogleRegisterRequest,
  RefreshTokenResponse,
  UserProfileResponse,
  RegisterResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  VerifyEmailRequest,
  VerifyEmailResponse,
  ResendVerificationRequest,
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

  // Sign in with Google (ID token from Google Identity Services)
  googleLogin: async (data: GoogleLoginRequest): Promise<GoogleAuthResponse> => {
    const response = await apiClient.post('/auth/google', data)
    return response.data
  },

  // Complete registration for a Google-verified identity
  googleRegister: async (data: GoogleRegisterRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post('/auth/google/register', data)
    return response.data
  },

  // Refresh token — no body needed, the httpOnly refresh_token cookie is
  // sent automatically (D8)
  refresh: async (): Promise<RefreshTokenResponse> => {
    const response = await apiClient.post('/auth/refresh', {})
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

  // Request a password reset email
  forgotPassword: async (data: ForgotPasswordRequest): Promise<ForgotPasswordResponse> => {
    const response = await apiClient.post('/auth/password/forgot', data)
    return response.data
  },

  // Reset password using the token from the forgot-password email
  resetPassword: async (data: ResetPasswordRequest): Promise<ResetPasswordResponse> => {
    const response = await apiClient.post('/auth/password/reset', data)
    return response.data
  },

  // Verify email using the token from the verification email
  verifyEmail: async (data: VerifyEmailRequest): Promise<VerifyEmailResponse> => {
    const response = await apiClient.post('/auth/email/verify', data)
    return response.data
  },

  // Resend the email verification link
  resendVerification: async (data: ResendVerificationRequest): Promise<ForgotPasswordResponse> => {
    const response = await apiClient.post('/auth/email/resend', data)
    return response.data
  },
}
