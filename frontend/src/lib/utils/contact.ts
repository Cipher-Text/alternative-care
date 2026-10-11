/**
 * Contact and navigation links for the pharmacy directory (pure functions, no imports, so they can
 * be unit-tested directly — see tests/unit/contact.test.js).
 */

/** Digits only, e.g. "+880 1711-000000" -> "8801711000000". */
function digits(value: string): string {
  return value.replace(/\D/g, '')
}

/**
 * A number for `wa.me`, which needs the full international form without "+".
 * Bangladeshi local numbers (01XXXXXXXXX) become 8801XXXXXXXXX; numbers already in international
 * form (+880… / 00880… / 880…) are kept. Anything that cannot be a phone number returns null so the
 * UI hides the button instead of linking to a dead chat.
 */
export function whatsappNumber(raw: string | null | undefined): string | null {
  if (!raw) return null
  let n = digits(raw)
  if (n.startsWith('00')) n = n.slice(2) // 00880… -> 880…
  else if (n.startsWith('0')) n = '880' + n.slice(1) // 01711… -> 880 1711…
  // Whatever it started as, an international number is 8–15 digits (E.164)
  if (n.length < 8 || n.length > 15) return null
  return n
}

export function whatsappLink(raw: string | null | undefined, message?: string): string | null {
  const n = whatsappNumber(raw)
  if (!n) return null
  return message ? `https://wa.me/${n}?text=${encodeURIComponent(message)}` : `https://wa.me/${n}`
}

/** `tel:` link that keeps a leading + and drops spaces/dashes that some dialers reject. */
export function telLink(raw: string | null | undefined): string | null {
  if (!raw) return null
  const cleaned = raw.trim().replace(/[^\d+]/g, '')
  return digits(cleaned).length >= 5 ? `tel:${cleaned}` : null
}

/**
 * Google Maps directions (opens the Maps app on phones). Uses the pin when there is one, otherwise
 * falls back to the address text; returns null when there is nothing to navigate to.
 */
export function directionsLink(place: {
  latitude: number | null
  longitude: number | null
  address?: string | null
  name?: string | null
}): string | null {
  if (place.latitude !== null && place.longitude !== null) {
    return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`
  }
  const text = [place.name, place.address].filter(Boolean).join(', ').trim()
  return text ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(text)}` : null
}

/** "850 m" under a kilometre, "1.7 km" under 10, "23 km" above. */
export function formatDistance(km: number | null | undefined): string | null {
  if (km === null || km === undefined || !Number.isFinite(km) || km < 0) return null
  if (km < 1) return `${Math.max(10, Math.round((km * 1000) / 10) * 10)} m`
  if (km < 10) return `${km.toFixed(1)} km`
  return `${Math.round(km)} km`
}
