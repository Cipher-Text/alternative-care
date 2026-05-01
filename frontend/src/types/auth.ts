export interface User {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string | null
  plan?: string | null
  language: string
  is_2fa_enabled: boolean
  is_active?: boolean
  is_email_verified?: boolean
  phone?: string | null
  last_login_at?: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  tokens: {
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
  }
  user: User
  requires_2fa: boolean
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
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfileResponse {
  user: User
  tenant: {
    id: string
    name: string
    email: string
    clinic_name: string | null
    specializations: string[]
    plan: string
    is_verified: boolean
    is_approved: boolean
    is_active: boolean
  } | null
}
