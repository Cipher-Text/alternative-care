import { identityError } from '@/components/identity/identityUtils'

export const portalInput =
  'mt-1 block w-full rounded-md border border-gray-300 bg-background px-4 py-3 text-lg dark:border-slate-700'
export const portalButton =
  'w-full rounded-md bg-emerald-600 px-4 py-3 text-base font-semibold text-white hover:bg-emerald-700 disabled:opacity-60'
export const portalButtonOutline =
  'rounded-md border border-gray-300 px-4 py-3 text-base font-medium hover:bg-gray-50 disabled:opacity-60 dark:border-slate-700 dark:hover:bg-slate-800'
export const portalLabel = 'text-base font-medium text-gray-900 dark:text-white'
export const portalErrorBox =
  'rounded-md border border-red-200 bg-red-50 p-3 text-base text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200'

/** True when the portal session has ended (or was never valid). */
export function isUnauthorized(error: unknown): boolean {
  return identityError(error).status === 401
}

/** 1250 -> "1,250" (ASCII digits in both languages). */
export function formatAmount(amount: number): string {
  return amount.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

/** A YYYY-MM-DD date as a local date (new Date('YYYY-MM-DD') would be read as UTC). */
export function localDate(date: string, time?: string): Date {
  return new Date(`${date}T${time && /^\d{2}:\d{2}/.test(time) ? time.slice(0, 5) : '00:00'}:00`)
}

/** A local date as YYYY-MM-DD (toISOString would shift it to UTC). */
export function isoDate(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

/** Today plus `days`, as YYYY-MM-DD in the visitor's own time zone. */
export function isoDateFromToday(days = 0): string {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return isoDate(d)
}

/**
 * A `?next=` return path, or null. Only a same-origin relative path is accepted: it must start with a single "/",
 * so "//host", "/\host", "https://host", "javascript:..." and anything with control characters are rejected.
 */
export function safeNextPath(raw: string | null | undefined): string | null {
  if (!raw || raw.length > 300) return null
  if (!raw.startsWith('/') || raw.startsWith('//') || raw.startsWith('/\\')) return null
  if (/[\u0000-\u001f\u007f\\]/.test(raw)) return null
  try {
    const base = 'http://same-origin.invalid'
    const url = new URL(raw, base)
    if (url.origin !== base) return null
    return `${url.pathname}${url.search}${url.hash}`
  } catch {
    return null
  }
}
