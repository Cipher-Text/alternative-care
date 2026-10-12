import { apiClient } from './client'
import type { ContactMessage, ContactMessageInput } from '@/types/contact'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

/** Browser-side, no login. Throws an Error with the API's message; `status` is set (429 = too many). */
export async function sendContactMessage(data: ContactMessageInput): Promise<void> {
  const res = await fetch(`${API_URL}/public/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = body.detail
    const text =
      typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join(' ') : ''
    const err = new Error(text || `request failed: ${res.status}`)
    ;(err as Error & { status?: number }).status = res.status
    throw err
  }
}

/** Admin-only inbox. */
export const adminContactApi = {
  list: async (params?: { status?: 'new' | 'handled'; limit?: number; offset?: number }): Promise<ContactMessage[]> =>
    (await apiClient.get('/admin/contact', { params })).data,
  setStatus: async (id: string, status: 'new' | 'handled'): Promise<ContactMessage> =>
    (await apiClient.patch(`/admin/contact/${id}`, { status })).data,
}
