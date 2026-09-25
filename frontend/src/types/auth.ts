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
  // Omitted when requires_2fa is true — the client resubmits
  // email/password/totp_code (e.g. via loginWith2FA) to get these.
  // refresh_token is never present — it's delivered only via an httpOnly
  // cookie (D8), never in a JS-readable response body.
  tokens?: {
    access_token: string
    token_type: string
    expires_in: number
  }
  user?: User
  requires_2fa: boolean
}

export interface TwoFactorRequest {
  email: string
  password: string
  totp_code: string
}

export interface GoogleLoginRequest {
  id_token: string
  totp_code?: string
}

export interface GoogleAuthResponse {
  // Exactly one outcome holds per response: tokens+user (success),
  // requires_2fa (resubmit id_token+totp_code), or needs_registration
  // (no account yet — collect clinic details and call googleRegister).
  tokens?: {
    access_token: string
    token_type: string
    expires_in: number
  }
  user?: User
  requires_2fa: boolean
  needs_registration: boolean
  email?: string
  full_name?: string
}

export interface GoogleRegisterRequest {
  id_token: string
  phone?: string | null
  language: 'en' | 'bn'
  clinic_name?: string | null
  clinic_address?: string | null
  division_id?: number | null
  district_id?: number | null
  upazila_id?: number | null
  specializations: MedicalSystem[]
  license_number?: string | null
}

export interface RefreshTokenResponse {
  access_token: string
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

export interface ForgotPasswordRequest {
  email: string
}

export interface ForgotPasswordResponse {
  message: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface ResetPasswordResponse {
  message: string
}

export interface VerifyEmailRequest {
  token: string
}

export interface VerifyEmailResponse {
  message: string
}

export interface ResendVerificationRequest {
  email: string
}
