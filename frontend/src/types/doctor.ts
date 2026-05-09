// Doctor Profile Types

export interface DoctorProfile {
  // User fields
  id: string
  email: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  language: 'en' | 'bn'
  is_active: boolean

  // Tenant/Clinic fields
  tenant_id: string
  clinic_name: string | null
  clinic_address: string | null
  division_id: number | null
  district_id: number | null
  upazila_id: number | null
  specializations: string[]
  license_number: string | null
  is_verified: boolean
  verified_at: string | null

  // Subscription
  plan: string
  plan_started_at: string
  plan_expires_at: string | null
}

export interface DoctorProfileUpdate {
  // User fields
  full_name?: string
  phone?: string
  avatar_url?: string
  language?: 'en' | 'bn'

  // Clinic fields
  clinic_name?: string
  clinic_address?: string
  division_id?: number
  district_id?: number
  upazila_id?: number
  license_number?: string
}

// Doctor Degree Types

export interface DoctorDegree {
  id: number
  user_id: string
  tenant_id: string

  degree_type: string
  degree_name: string
  specialization: string | null
  institution_name: string
  institution_location: string | null
  start_year: number | null
  completion_year: number
  certificate_url: string | null
  display_order: number

  is_verified: boolean
  verified_at: string | null
  verified_by: string | null
  created_at: string
  updated_at: string | null
}

export interface DoctorDegreeCreate {
  degree_type: string
  degree_name: string
  specialization?: string | null
  institution_name: string
  institution_location?: string | null
  start_year?: number | null
  completion_year: number
  certificate_url?: string | null
  display_order?: number
}

export interface DoctorDegreeUpdate {
  degree_type?: string
  degree_name?: string
  specialization?: string | null
  institution_name?: string
  institution_location?: string | null
  start_year?: number | null
  completion_year?: number
  certificate_url?: string | null
  display_order?: number
}

// Doctor Training Types

export interface DoctorTraining {
  id: number
  user_id: string
  tenant_id: string

  training_type: string
  title: string
  provider: string
  description: string | null
  skills: string | null
  start_date: string | null
  completion_date: string
  expiry_date: string | null
  certificate_url: string | null
  credential_id: string | null
  display_order: number

  is_verified: boolean
  verified_at: string | null
  verified_by: string | null
  created_at: string
  updated_at: string | null
}

export interface DoctorTrainingCreate {
  training_type: string
  title: string
  provider: string
  description?: string | null
  skills?: string | null
  start_date?: string | null
  completion_date: string
  expiry_date?: string | null
  certificate_url?: string | null
  credential_id?: string | null
  display_order?: number
}

export interface DoctorTrainingUpdate {
  training_type?: string
  title?: string
  provider?: string
  description?: string | null
  skills?: string | null
  start_date?: string | null
  completion_date?: string
  expiry_date?: string | null
  certificate_url?: string | null
  credential_id?: string | null
  display_order?: number
}
