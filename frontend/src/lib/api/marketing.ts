import { apiClient } from './client'
import type { AdminFacebookRequest, FacebookRequest, FacebookSummary, FbStatus } from '@/types/marketing'

/** Doctor-only: ask to be featured on the AltCare Facebook page, review the draft, approve it. */
export const marketingApi = {
  summary: async (): Promise<FacebookSummary> => (await apiClient.get('/marketing/facebook')).data,
  request: async (doctor_note?: string): Promise<FacebookRequest> =>
    (await apiClient.post('/marketing/facebook/requests', { doctor_note })).data,
  cancel: async (id: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/marketing/facebook/requests/${id}/cancel`)).data,
  /** Approves the exact drafted text; staff cannot mark it posted before this */
  approve: async (id: string, comment?: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/marketing/facebook/requests/${id}/approve`, { comment })).data,
  /** Sends the draft back to staff */
  requestChanges: async (id: string, comment: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/marketing/facebook/requests/${id}/changes`, { comment })).data,
}

/** Admin-only: the staff queue. */
export const adminMarketingApi = {
  list: async (params?: { status?: FbStatus; limit?: number; offset?: number }): Promise<AdminFacebookRequest[]> =>
    (await apiClient.get('/admin/marketing/facebook', { params })).data,
  draft: async (id: string, draft_text: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/admin/marketing/facebook/${id}/draft`, { draft_text })).data,
  reject: async (id: string, reason: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/admin/marketing/facebook/${id}/reject`, { reason })).data,
  /** Only allowed once the doctor approved (otherwise 409 not_approved) */
  markPosted: async (id: string, post_url: string): Promise<FacebookRequest> =>
    (await apiClient.post(`/admin/marketing/facebook/${id}/posted`, { post_url })).data,
}
