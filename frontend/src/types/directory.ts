/** Practitioner directory (matches backend app/shared/schemas/directory.py). */

export type Availability = 'in_person' | 'online' | 'both'
export type RequestStatus = 'new' | 'contacted' | 'closed'

export const AVAILABILITY_OPTIONS: Availability[] = ['in_person', 'online', 'both']

/** Machine-readable reasons a listing is not public yet. */
export type ListingBlocker = 'not_listed' | 'not_verified' | 'not_approved' | 'not_in_plan' | 'no_profile_text'

export interface Eligibility {
  is_listed: boolean
  verified: boolean
  approved: boolean
  in_plan: boolean
  has_profile_text: boolean
  public: boolean
  blockers: ListingBlocker[]
}

/** The doctor's own listing. `exists` is false until first saved (then fields are defaults). */
export interface Listing {
  exists: boolean
  id: string | null
  slug: string | null
  is_listed: boolean
  listed_at: string | null
  headline_en: string | null
  headline_bn: string | null
  bio_en: string | null
  bio_bn: string | null
  languages: string[]
  consultation_hours: string | null
  availability: Availability
  show_fee: boolean
  show_phone: boolean
  show_whatsapp: boolean
  accepts_requests: boolean
  eligibility: Eligibility | null
}

export type ListingInput = Partial<
  Pick<
    Listing,
    | 'is_listed'
    | 'headline_en'
    | 'headline_bn'
    | 'bio_en'
    | 'bio_bn'
    | 'languages'
    | 'consultation_hours'
    | 'availability'
    | 'show_fee'
    | 'show_phone'
    | 'show_whatsapp'
    | 'accepts_requests'
  >
>

export interface DirectoryStats {
  month: string // YYYY-MM
  requests: number
  calls: number
  whatsapp: number
  open_requests: number
}

export interface ContactRequest {
  id: string
  patient_name: string
  patient_phone: string
  message: string | null
  preferred_time: string | null
  status: RequestStatus
  created_at: string
}

export interface PublicDegree {
  degree_name: string
  institution_name: string
  completion_year: number
  is_verified: boolean
}

/** Card on the public list. */
export interface PublicPractitionerItem {
  slug: string
  display_name: string
  clinic_name: string | null
  headline_en: string | null
  headline_bn: string | null
  disciplines: string[]
  registration_body: string | null
  years_of_experience: number | null
  district_en: string | null
  district_bn: string | null
  languages: string[]
  availability: Availability
  fee_bdt: number | null
  verified_at: string | null
  logo_url: string | null
}

export interface PublicPractitioner extends PublicPractitionerItem {
  bio_en: string | null
  bio_bn: string | null
  consultation_hours: string | null
  follow_up_fee_bdt: number | null
  address_line_1: string | null
  address_line_2: string | null
  landmark: string | null
  upazila_en: string | null
  upazila_bn: string | null
  division_en: string | null
  division_bn: string | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  whatsapp: string | null
  accepts_requests: boolean
  degrees: PublicDegree[]
}

/** `launched` is false until enough profiles exist; the site then shows a teaser instead. */
export interface PublicPractitionerList {
  launched: boolean
  total: number
  items: PublicPractitionerItem[]
}

export interface ContactRequestInput {
  patient_name: string
  patient_phone: string
  message?: string
  preferred_time?: string
  consent: boolean
  /** Honeypot — leave empty; hidden from people */
  website?: string
}
