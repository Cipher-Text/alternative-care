export interface Patient {
  id: string
  tenant_id: string
  patient_code: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: 'male' | 'female' | 'other'
  phone: string
  email?: string
  address?: string
  division_id?: string
  district_id?: string
  upazila_id?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  blood_group?: string
  created_at: string
  updated_at: string
}

export interface PatientCreateRequest {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: 'male' | 'female' | 'other'
  phone: string
  email?: string
  address?: string
  division_id?: string
  district_id?: string
  upazila_id?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  blood_group?: string
}

export interface PatientUpdateRequest extends Partial<PatientCreateRequest> {}

export interface PatientListParams {
  skip?: number
  limit?: number
  search?: string
  gender?: string
  tag_id?: string
}

export interface PatientTag {
  id: string
  tenant_id: string
  patient_id: string
  tag: string
  created_at: string
}

export interface PatientDiagnosis {
  id: string
  tenant_id: string
  patient_id: string
  diagnosis: string
  diagnosed_at: string
  notes?: string
  created_at: string
  updated_at: string
}

// Geographic types
export interface Division {
  id: string
  name_en: string
  name_bn: string
  code: string
}

export interface District {
  id: string
  division_id: string
  name_en: string
  name_bn: string
  code: string
}

export interface Upazila {
  id: string
  district_id: string
  name_en: string
  name_bn: string
  code: string
}
