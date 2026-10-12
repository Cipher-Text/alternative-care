/** AltCare's public contact channels, from the deployment's environment. A channel that is not set
 * is simply not shown. The contact form always works, whatever is configured here. */

export interface ContactInfo {
  email: string | null
  /** Digits only, with country code, as wa.me expects (e.g. 8801700000000) */
  whatsapp: string | null
  /** Full https URL of the AltCare Facebook page */
  facebook: string | null
}

function clean(value: string | undefined): string | null {
  const v = (value ?? '').trim()
  return v ? v : null
}

export function getContactInfo(): ContactInfo {
  const digits = (process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? '').replace(/[^0-9]/g, '')
  const facebook = clean(process.env.NEXT_PUBLIC_FACEBOOK_URL)
  return {
    email: clean(process.env.NEXT_PUBLIC_CONTACT_EMAIL),
    whatsapp: digits.length >= 8 ? digits : null,
    facebook: facebook && facebook.startsWith('https://') ? facebook : null,
  }
}
