export interface User {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string | null
  plan: string
  language: string
  two_factor_enabled: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface TwoFactorRequest {
  email: string
  password: string
  totp_code: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
}
