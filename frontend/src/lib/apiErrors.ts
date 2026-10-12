import type { CreditChannel, CreditsExhaustedDetail } from '@/types/credits'

type ApiError = { response?: { status?: number; data?: { detail?: unknown } } }

/** The raw `detail` of an API error response (string, object, array or undefined). */
export function rawDetail(error: unknown): unknown {
  return (error as ApiError)?.response?.data?.detail
}

/**
 * A human-readable message from an API error. `detail` can be a string (our own errors), an object
 * with a `message` (structured errors such as credits_exhausted) or an array of validation items;
 * it is never stringified as "[object Object]".
 */
export function errorMessage(error: unknown, fallback: string): string {
  const detail = rawDetail(error)
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
      .filter(Boolean)
    if (msgs.length) return msgs.join('; ')
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    const m = (detail as { message: unknown }).message
    if (typeof m === 'string' && m.trim()) return m
  }
  return fallback
}

/** The structured "credits exhausted" 403, or null for any other error. */
export function creditsExhausted(error: unknown): CreditsExhaustedDetail | null {
  const detail = rawDetail(error)
  if (detail && typeof detail === 'object' && (detail as { code?: unknown }).code === 'credits_exhausted') {
    return detail as CreditsExhaustedDetail
  }
  return null
}

export function isCreditChannel(value: unknown): value is CreditChannel {
  return value === 'sms' || value === 'email'
}
