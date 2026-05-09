export type PrescriptionStatus = 'draft' | 'issued' | 'voided'

// Prescription Item Types
export interface PrescriptionItemBase {
  medicine_id?: number | null
  medicine_name?: string | null
  dosage: string
  frequency: string
  duration?: string | null
  quantity?: number | null
  instructions?: string | null
  display_order?: number
}

export interface PrescriptionItemCreate extends PrescriptionItemBase {}

export interface PrescriptionItemUpdate {
  medicine_id?: number | null
  medicine_name?: string | null
  dosage?: string
  frequency?: string
  duration?: string | null
  quantity?: number | null
  instructions?: string | null
  display_order?: number
}

export interface PrescriptionItem extends PrescriptionItemBase {
  id: number
  prescription_id: string
  tenant_id: string
  created_at: string
  updated_at?: string | null
}

// Prescription Types
export interface PrescriptionBase {
  patient_id: string
  visit_id?: string | null
  diagnosis?: string | null
  doctors_notes?: string | null
  advice?: string | null
}

export interface PrescriptionCreateRequest extends PrescriptionBase {
  items?: PrescriptionItemCreate[]
  status?: 'draft' | 'issued'
}

export interface PrescriptionUpdateRequest {
  diagnosis?: string | null
  doctors_notes?: string | null
  advice?: string | null
  status?: PrescriptionStatus
}

export interface Prescription extends PrescriptionBase {
  id: string
  tenant_id: string
  prescribed_by: string
  status: PrescriptionStatus
  pdf_url?: string | null
  pdf_generated_at?: string | null
  created_at: string
  updated_at?: string | null
  created_by?: string | null
  updated_by?: string | null
  items: PrescriptionItem[]
}

export interface PrescriptionListItem {
  id: string
  patient_id: string
  visit_id?: string | null
  prescribed_by: string
  diagnosis?: string | null
  status: PrescriptionStatus
  pdf_url?: string | null
  created_at: string
}

// API Query Parameters
export interface PrescriptionListParams {
  patient_id?: string
  visit_id?: string
  status?: PrescriptionStatus
  limit?: number
  offset?: number
}

// PDF Generation Response
export interface PrescriptionPDFResponse {
  pdf_url: string
}
