import { useMutation, useQuery, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { adminMessagingApi, billingApi } from '@/lib/api/billing'
import { errorMessage } from '@/lib/apiErrors'
import type { CreditAdjustmentInput } from '@/types/credits'

export const billingKeys = {
  credits: ['billing', 'credits'] as const,
  ledger: (params: { limit: number; offset: number }) => ['billing', 'ledger', params] as const,
  messagingStatus: ['admin', 'messaging', 'status'] as const,
}

export function useCredits(enabled = true) {
  return useQuery(billingKeys.credits, () => billingApi.credits(), { enabled, staleTime: 15000 })
}

export function useCreditLedger(params: { limit: number; offset: number }) {
  return useQuery(billingKeys.ledger(params), () => billingApi.ledger(params), {
    staleTime: 15000,
    keepPreviousData: true,
  })
}

/** Silent callers (the admin dashboard card): no retries, no error UI. */
export function useMessagingStatus(enabled = true) {
  return useQuery(billingKeys.messagingStatus, () => adminMessagingApi.status(), {
    enabled,
    staleTime: 60000,
    retry: false,
  })
}

export function useAdjustCredits(tenantId: string) {
  const t = useTranslations('billingUi')
  const queryClient = useQueryClient()
  return useMutation((data: CreditAdjustmentInput) => adminMessagingApi.adjustCredits(tenantId, data), {
    onSuccess: () => {
      queryClient.invalidateQueries(['billing'])
      toast.success(t('admin.credits.done'))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('admin.credits.failed')))
    },
  })
}
