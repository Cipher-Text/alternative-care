/** The part of the clinic profile the app reads (GET /tenant/profile returns more). */
export interface ClinicProfile {
  id: string
  clinic_name: string | null
  logo_url: string | null
  /** The systems the clinic practises, e.g. ['homeopathy', 'unani'] */
  specializations: string[]
  /** The usual fees, in paisa (100 paisa = 1 taka); null when not set */
  consultation_fee?: number | null
  follow_up_fee?: number | null
}
