import { apiClient } from './client'
import type {
  AdminOrder,
  CheckoutRequest,
  CheckoutResponse,
  CreditPack,
  CreditPackInput,
  CreditPackUpdate,
  ManualPlanGrantInput,
  Order,
  OrderStatus,
  SubscriptionInfo,
} from '@/types/checkout'

/** Doctor-only: the clinic's subscription, packs, checkout and receipts. */
export const checkoutApi = {
  subscription: async (): Promise<SubscriptionInfo> => (await apiClient.get('/billing/subscription')).data,
  packs: async (): Promise<CreditPack[]> => (await apiClient.get('/billing/packs')).data,
  start: async (data: CheckoutRequest): Promise<CheckoutResponse> =>
    (await apiClient.post('/billing/checkout', data)).data,
  orders: async (params?: { limit?: number; offset?: number }): Promise<Order[]> =>
    (await apiClient.get('/billing/orders', { params })).data,
  /** Re-checks a pending order with the gateway, so it is the source of truth for the return page */
  order: async (id: string): Promise<Order> => (await apiClient.get(`/billing/orders/${id}`)).data,
  /** TEST gateway only: report the outcome the tester picked on the fake payment page */
  completeFake: async (id: string, outcome: 'success' | 'failed' | 'cancelled'): Promise<Order> =>
    (await apiClient.post(`/billing/fake-gateway/${id}/complete`, { outcome })).data,
}

/** Admin-only. */
export const adminBillingApi = {
  grantPlan: async (tenantId: string, data: ManualPlanGrantInput): Promise<AdminOrder> =>
    (await apiClient.post(`/admin/billing/tenants/${tenantId}/plan`, data)).data,
  packs: async (): Promise<CreditPack[]> => (await apiClient.get('/admin/billing/packs')).data,
  createPack: async (data: CreditPackInput): Promise<CreditPack> =>
    (await apiClient.post('/admin/billing/packs', data)).data,
  updatePack: async (id: number, data: CreditPackUpdate): Promise<CreditPack> =>
    (await apiClient.patch(`/admin/billing/packs/${id}`, data)).data,
  orders: async (params?: {
    status?: OrderStatus
    tenant_id?: string
    limit?: number
    offset?: number
  }): Promise<AdminOrder[]> => (await apiClient.get('/admin/billing/orders', { params })).data,
}
