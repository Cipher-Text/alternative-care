/**
 * Pharmacy directory types
 * Matches backend schemas from app/shared/schemas/pharmacy.py
 */

export type PharmacyDiscipline = 'homeopathy' | 'ayurveda' | 'unani' | 'herbal'
export type PharmacyType = 'retail' | 'wholesale' | 'manufacturer' | 'depot'

export const PHARMACY_TYPES: Array<{ value: PharmacyType; label: string }> = [
  { value: 'retail', label: 'Retail pharmacy' },
  { value: 'wholesale', label: 'Wholesaler' },
  { value: 'manufacturer', label: 'Manufacturer' },
  { value: 'depot', label: 'Depot' },
]

export const PHARMACY_DISCIPLINES: Array<{ value: PharmacyDiscipline; label: string }> = [
  { value: 'homeopathy', label: 'Homeopathy' },
  { value: 'ayurveda', label: 'Ayurveda' },
  { value: 'unani', label: 'Unani' },
  { value: 'herbal', label: 'Herbal' },
]

/** Editable fields (create payload) */
export interface PharmacyInput {
  name_en: string
  name_bn: string | null
  pharmacy_type: PharmacyType
  disciplines: PharmacyDiscipline[]
  notes_en: string | null
  notes_bn: string | null
  address: string | null
  district_id: number | null
  upazila_id: number | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  whatsapp: string | null
  email: string | null
  website_url: string | null
  opening_hours: string | null
  delivers: boolean
  source_url: string | null
  is_active: boolean
}

export interface Pharmacy extends PharmacyInput {
  id: number
  is_verified: boolean
  verified_at: string | null
  verified_by: string | null
  last_confirmed_at: string | null
  distance_km: number | null
  created_at: string
  updated_at: string | null
}

export interface PharmacyListItem {
  id: number
  name_en: string
  name_bn: string | null
  pharmacy_type: PharmacyType
  disciplines: PharmacyDiscipline[]
  address: string | null
  district_id: number | null
  upazila_id: number | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  whatsapp: string | null
  opening_hours: string | null
  delivers: boolean
  is_verified: boolean
  last_confirmed_at: string | null
  is_active: boolean
  distance_km: number | null
}

export interface PharmacyUpdate extends Partial<PharmacyInput> {
  is_verified?: boolean
  /** Not stored: stamps last_confirmed_at ("re-checked today") */
  mark_confirmed?: boolean
}

export interface PharmacyFilters {
  search?: string
  discipline?: PharmacyDiscipline
  pharmacy_type?: PharmacyType
  district_id?: number
  delivers?: boolean
  /** Near-me search: both required together */
  lat?: number
  lon?: number
  radius_km?: number
  is_active?: boolean
  limit?: number
  offset?: number
}

export interface PharmacyImportResult {
  created: number
  skipped: number
  errors: Array<{ row: number; message: string }>
}

/** A listing not re-checked for this long is flagged as possibly out of date. */
export const STALE_AFTER_DAYS = 180
