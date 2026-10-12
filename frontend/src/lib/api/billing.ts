import { apiClient } from './client'
import type {
  CreditAdjustmentInput,
  CreditChannel,
  CreditSummary,
  LedgerEntry,
  MessagingStatus,
} from '@/types/credits'

/** Clinic-facing: SMS/email balances (plan allowance + purchased credits) and history. */
export const billingApi = {
  credits: async (): Promise<CreditSummary> => (await apiClient.get('/billing/credits')).data,
  ledger: async (params?: { limit?: number; offset?: number }): Promise<LedgerEntry[]> =>
    (await apiClient.get('/billing/credits/ledger', { params })).data,
}

/** Admin-only. */
export const adminMessagingApi = {
  status: async (): Promise<MessagingStatus> => (await apiClient.get('/admin/messaging/status')).data,
  adjustCredits: async (
    tenantId: string,
    data: CreditAdjustmentInput
  ): Promise<{ channel: CreditChannel; purchased: number }> =>
    (await apiClient.post(`/admin/tenants/${tenantId}/credits`, data)).data,
}
