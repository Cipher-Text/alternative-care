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

export type MedicalSystem = 'homeopathy' | 'ayurveda' | 'unani' | 'herbal'
export type SubscriptionPlan = 'free' | 'plus' | 'pro'

export interface AdminCreateTenantDoctorRequest {
  email: string
  password: string
  full_name: string
  phone?: string | null
  language: 'en' | 'bn'
  clinic_name?: string | null
  clinic_address?: string | null
  division_id?: number | null
  district_id?: number | null
  upazila_id?: number | null
  specializations: MedicalSystem[]
  license_number?: string | null
  tenant_name?: string | null
  plan: SubscriptionPlan
  auto_approve: boolean
}

export interface RegisterResponse {
  message: string
  user_id: string
  tenant_id: string
  email: string
  requires_approval: boolean
}

export interface TenantResponse {
  id: string
  name: string
  email: string
  clinic_name: string | null
  specializations: string[]
  plan: string
  is_verified: boolean
  is_approved: boolean
  is_active: boolean
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
