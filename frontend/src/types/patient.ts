// PatientListItem — lightweight list view (matches backend PatientListItem)
export interface PatientListItem {
  id: string
  full_name: string
  phone: string | null
  date_of_birth: string | null
  gender: 'male' | 'female' | 'other' | null
  next_visit_date: string | null
  is_active: boolean
}

// Patient — full record (matches backend PatientResponse)
export interface Patient {
  id: string
  tenant_id: string
  full_name: string
  date_of_birth: string | null
  gender: 'male' | 'female' | 'other' | null
  blood_group: 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-' | null
  phone: string | null
  email: string | null
  whatsapp: string | null
  address: string | null
  division_id: number | null
  district_id: number | null
  upazila_id: number | null
  chief_complaint: string | null
  medical_history: string | null
  photo_url: string | null
  next_visit_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string | null
  created_by: string | null
  updated_by: string | null
}

// PatientCreateRequest — matches backend PatientCreate
export interface PatientCreateRequest {
  full_name: string
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  blood_group?: 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-'
  phone?: string
  email?: string
  whatsapp?: string
  address?: string
  division_id?: number
  district_id?: number
  upazila_id?: number
  chief_complaint?: string
  medical_history?: string
  photo_url?: string
  next_visit_date?: string
}

// PatientUpdateRequest — all fields optional, plus is_active toggle
export type PatientUpdateRequest = Partial<PatientCreateRequest> & {
  is_active?: boolean
}

export interface PatientListParams {
  limit?: number
  offset?: number
  search?: string
  is_active?: boolean
}

export interface PatientTag {
  id: number
  tenant_id: string
  patient_id: string
  tag_type: 'special_case' | 'chronic' | 'treatment' | 'allergy'
  tag_value: string
  notes: string | null
  created_at: string
  updated_at: string | null
}

export interface PatientDiagnosis {
  id: number
  tenant_id: string
  patient_id: string
  visit_id: string | null
  description: string
  icd_code: string | null
  diagnosed_at: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

// Geographic types
export interface Division {
  id: number
  name_en: string
  name_bn: string
  code: string
}

export interface District {
  id: number
  division_id: number
  name_en: string
  name_bn: string
  code: string
}

export interface Upazila {
  id: number
  district_id: number
  name_en: string
  name_bn: string
  code: string
}
