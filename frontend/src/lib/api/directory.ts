import { apiClient } from './client'
import type {
  ContactRequest,
  DirectoryStats,
  Listing,
  ListingInput,
  RequestStatus,
} from '@/types/directory'

/** Doctor-only: own listing, month-to-date contact numbers, and contact requests. */
export const directoryApi = {
  getListing: async (): Promise<Listing> => (await apiClient.get('/directory/listing')).data,
  saveListing: async (data: ListingInput): Promise<Listing> =>
    (await apiClient.put('/directory/listing', data)).data,
  stats: async (): Promise<DirectoryStats> => (await apiClient.get('/directory/stats')).data,
  requests: async (params?: { status?: RequestStatus; limit?: number; offset?: number }): Promise<ContactRequest[]> =>
    (await apiClient.get('/directory/requests', { params })).data,
  updateRequest: async (id: string, status: RequestStatus): Promise<ContactRequest> =>
    (await apiClient.patch(`/directory/requests/${id}`, { status })).data,
}

/** Admin-only: record that a tenant's credentials were checked (free; required to appear publicly). */
export const verifyTenant = async (
  tenantId: string,
  data: { verified: boolean; note?: string }
): Promise<{ tenant_id: string; is_verified: boolean; verified_at: string | null; verification_note: string | null }> =>
  (await apiClient.post(`/admin/tenants/${tenantId}/verification`, data)).data
