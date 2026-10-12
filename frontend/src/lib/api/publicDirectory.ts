/** Server-side fetchers and helpers for the public practitioner directory. No auth, cached 5 min. */
import type {
  ContactRequestInput,
  PublicPractitioner,
  PublicPractitionerList,
} from '@/types/directory'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function fetchPractitioners(params: {
  discipline?: string
  district_id?: number
  q?: string
  limit?: number
  offset?: number
}): Promise<PublicPractitionerList> {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && qs.set(k, String(v)))
  try {
    const res = await fetch(`${API_URL}/public/practitioners?${qs}`, { next: { revalidate: 300 } })
    if (!res.ok) return { launched: false, total: 0, items: [] }
    return await res.json()
  } catch {
    return { launched: false, total: 0, items: [] }
  }
}

/** null on 404; throws on other errors so a backend outage is not cached as "not found". */
export async function fetchPractitioner(slug: string): Promise<PublicPractitioner | null> {
  const res = await fetch(`${API_URL}/public/practitioners/${encodeURIComponent(slug)}`, {
    next: { revalidate: 300 },
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`practitioner fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchPractitionerSlugs(): Promise<string[]> {
  try {
    const res = await fetch(`${API_URL}/public/practitioners/slugs`, { next: { revalidate: 300 } })
    return res.ok ? await res.json() : []
  } catch {
    return []
  }
}

/** Whether the directory has enough profiles to be shown (nav, sitemap). */
export async function isDirectoryLaunched(): Promise<boolean> {
  return (await fetchPractitioners({ limit: 1 })).launched
}

/** Browser-side: a patient asks the clinic to call back. Throws with the API's detail on failure. */
export async function submitContactRequest(slug: string, data: ContactRequestInput): Promise<void> {
  const res = await fetch(`${API_URL}/public/practitioners/${encodeURIComponent(slug)}/requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = new Error(typeof body.detail === 'string' ? body.detail : `request failed: ${res.status}`)
    ;(err as Error & { status?: number }).status = res.status
    throw err
  }
}

/** Browser-side, fire-and-forget: counts a call/WhatsApp tap. Never blocks the tap. */
export function recordContactEvent(slug: string, event_type: 'call' | 'whatsapp'): void {
  try {
    void fetch(`${API_URL}/public/practitioners/${encodeURIComponent(slug)}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type }),
      keepalive: true,
    })
  } catch {
    /* analytics must never break the page */
  }
}
