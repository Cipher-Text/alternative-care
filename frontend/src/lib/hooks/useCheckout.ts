import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { adminBillingApi, checkoutApi } from '@/lib/api/checkout'
import { errorMessage } from '@/lib/apiErrors'
import { billingKeys } from '@/lib/hooks/useBilling'
import type { CheckoutRequest, ManualPlanGrantInput, Order, CreditPackInput, CreditPackUpdate, OrderStatus } from '@/types/checkout'

export const checkoutKeys = {
  subscription: ['subscription'] as const,
  packs: ['billing', 'packs'] as const,
  orders: (params: { limit: number; offset: number }) => ['billing', 'orders', params] as const,
  order: (id: string) => ['billing', 'order', id] as const,
  adminPacks: ['admin', 'billing', 'packs'] as const,
  adminOrders: (params: { status?: OrderStatus; limit: number; offset: number }) =>
    ['admin', 'billing', 'orders', params] as const,
}

export function useSubscription(enabled = true) {
  return useQuery(checkoutKeys.subscription, () => checkoutApi.subscription(), { enabled, staleTime: 15000 })
}

/** Silent: callers that only decide whether to show a link (messaging page) get no retries. */
export function usePacks(enabled = true) {
  return useQuery(checkoutKeys.packs, () => checkoutApi.packs(), { enabled, staleTime: 60000, retry: false })
}

export function useOrders(params: { limit: number; offset: number }, enabled = true) {
  return useQuery(checkoutKeys.orders(params), () => checkoutApi.orders(params), {
    enabled,
    staleTime: 15000,
    keepPreviousData: true,
  })
}

/** One order. `refetchInterval` (ms) is used by the return page to poll while it is pending. */
export function useOrder(id: string | null, options?: { refetchInterval?: number | false | ((data: Order | undefined) => number | false); enabled?: boolean }) {
  return useQuery(checkoutKeys.order(id ?? ''), () => checkoutApi.order(id as string), {
    enabled: Boolean(id) && (options?.enabled ?? true),
    refetchInterval: options?.refetchInterval ?? false,
    refetchOnWindowFocus: false,
  })
}

/** After a purchase changes anything: plan, balances (credit summary), packs and order lists. */
function useInvalidateBilling() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries(checkoutKeys.subscription)
    queryClient.invalidateQueries(billingKeys.credits)
    queryClient.invalidateQueries(['billing'])
  }
}

export function useStartCheckout() {
  return useMutation((data: CheckoutRequest) => checkoutApi.start(data))
}

export function useCompleteFake() {
  const invalidate = useInvalidateBilling()
  return useMutation(
    ({ id, outcome }: { id: string; outcome: 'success' | 'failed' | 'cancelled' }) =>
      checkoutApi.completeFake(id, outcome),
    { onSettled: invalidate }
  )
}

export function useAdminPacks(enabled = true) {
  return useQuery(checkoutKeys.adminPacks, () => adminBillingApi.packs(), { enabled })
}

export function useAdminOrders(params: { status?: OrderStatus; limit: number; offset: number }, enabled = true) {
  return useQuery(checkoutKeys.adminOrders(params), () => adminBillingApi.orders(params), {
    enabled,
    keepPreviousData: true,
  })
}

export function useCreatePack() {
  const t = useTranslations('billingUi.adminBilling')
  const queryClient = useQueryClient()
  return useMutation((data: CreditPackInput) => adminBillingApi.createPack(data), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin', 'billing', 'packs'])
      queryClient.invalidateQueries(checkoutKeys.packs)
      toast.success(t('packs.created'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('packs.saveFailed')))
    },
  })
}

export function useUpdatePack() {
  const t = useTranslations('billingUi.adminBilling')
  const queryClient = useQueryClient()
  return useMutation(({ id, data }: { id: number; data: CreditPackUpdate }) => adminBillingApi.updatePack(id, data), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin', 'billing', 'packs'])
      queryClient.invalidateQueries(checkoutKeys.packs)
      toast.success(t('packs.updated'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('packs.saveFailed')))
    },
  })
}

/** Admin: set a clinic's plan after a manual payment. Refreshes the clinic and its billing views. */
export function useGrantPlan(tenantId: string) {
  const t = useTranslations('billingUi.admin.plan')
  const queryClient = useQueryClient()
  return useMutation((data: ManualPlanGrantInput) => adminBillingApi.grantPlan(tenantId, data), {
    onSuccess: () => {
      queryClient.invalidateQueries(['admin'])
      queryClient.invalidateQueries(['billing'])
      queryClient.invalidateQueries(checkoutKeys.subscription)
      toast.success(t('done'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('failed')))
    },
  })
}
