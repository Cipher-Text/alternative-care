/** The part of the clinic profile the app reads (GET /tenant/profile returns more). */
export interface ClinicProfile {
  id: string
  clinic_name: string | null
  logo_url: string | null
}
