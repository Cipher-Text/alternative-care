/** Small formatting helpers shared by the public practitioner pages. */

export const DIRECTORY_DISCIPLINES = ['homeopathy', 'ayurveda', 'unani', 'herbal'] as const
export type DirectoryDiscipline = (typeof DIRECTORY_DISCIPLINES)[number]

export function isDirectoryDiscipline(value: string): value is DirectoryDiscipline {
  return (DIRECTORY_DISCIPLINES as readonly string[]).includes(value)
}

/** "৳500": ASCII digits in both languages, as the Bengali UI style guide asks. */
export function formatFee(amount: number): string {
  return `৳${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(amount)}`
}

/** Digits only, with Bangladesh country code, for a wa.me link. Null when there is nothing usable. */
export function whatsappDigits(raw: string): string | null {
  let digits = raw.replace(/\D/g, '')
  if (digits.startsWith('00')) digits = digits.slice(2)
  else if (digits.startsWith('0')) digits = `88${digits}`
  return digits.length >= 8 ? digits : null
}

export function telHref(raw: string): string {
  return `tel:${raw.replace(/[^\d+]/g, '')}`
}
