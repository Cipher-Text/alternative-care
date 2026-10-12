import { useQuery, useMutation, useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { adminMarketingApi, marketingApi } from '@/lib/api/marketing'
import { errorMessage } from '@/lib/apiErrors'
import type { AdminFacebookRequest, FbStatus } from '@/types/marketing'

const SUMMARY_KEY = ['marketing', 'facebook']
const QUEUE_KEY = ['marketing', 'admin-queue']

export function useFacebookSummary(enabled = true) {
  return useQuery(SUMMARY_KEY, () => marketingApi.summary(), { enabled, staleTime: 15000 })
}

/** Every doctor action changes the summary (open request, quota, history), so they all refresh it. */
function useSummaryMutation<V>(fn: (v: V) => Promise<unknown>, successKey: string) {
  const t = useTranslations('marketingUi')
  const queryClient = useQueryClient()
  return useMutation(fn, {
    onSuccess: () => {
      queryClient.invalidateQueries(SUMMARY_KEY)
      toast.success(t(successKey))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('toast.failed')))
      // A refusal usually means the state moved on (e.g. staff acted meanwhile): show the current truth
      queryClient.invalidateQueries(SUMMARY_KEY)
    },
  })
}

export function useCreateFacebookRequest() {
  return useSummaryMutation((note?: string) => marketingApi.request(note), 'toast.requested')
}
export function useCancelFacebookRequest() {
  return useSummaryMutation((id: string) => marketingApi.cancel(id), 'toast.cancelled')
}
export function useApproveFacebookRequest() {
  return useSummaryMutation((id: string) => marketingApi.approve(id), 'toast.approved')
}
export function useRequestFacebookChanges() {
  return useSummaryMutation(
    ({ id, comment }: { id: string; comment: string }) => marketingApi.requestChanges(id, comment),
    'toast.changesSent'
  )
}

/**
 * Staff queue for one tab. The API filters by a single status, so a tab with several statuses
 * (Closed = rejected + cancelled) fetches each from the start, merges newest first and slices.
 */
export function useAdminFacebookQueue(statuses: FbStatus[], offset: number, limit: number, enabled = true) {
  return useQuery<AdminFacebookRequest[]>(
    [...QUEUE_KEY, statuses, offset, limit],
    async () => {
      const take = statuses.length === 1 ? limit : offset + limit
      const skip = statuses.length === 1 ? offset : 0
      const lists = await Promise.all(
        statuses.map((status) => adminMarketingApi.list({ status, limit: take, offset: skip }))
      )
      if (statuses.length === 1) return lists[0]
      return lists
        .flat()
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(offset, offset + limit)
    },
    { enabled, staleTime: 10000, keepPreviousData: true }
  )
}

function useQueueMutation<V>(fn: (v: V) => Promise<unknown>, successKey: string) {
  const t = useTranslations('marketingUi')
  const queryClient = useQueryClient()
  return useMutation(fn, {
    onSuccess: () => {
      queryClient.invalidateQueries(QUEUE_KEY)
      toast.success(t(successKey))
    },
    onError: (error) => {
      toast.error(errorMessage(error, t('toast.failed')))
      queryClient.invalidateQueries(QUEUE_KEY)
    },
  })
}

export function useDraftFacebookPost() {
  return useQueueMutation(
    ({ id, text }: { id: string; text: string }) => adminMarketingApi.draft(id, text),
    'toast.drafted'
  )
}
export function useRejectFacebookRequest() {
  return useQueueMutation(
    ({ id, reason }: { id: string; reason: string }) => adminMarketingApi.reject(id, reason),
    'toast.rejected'
  )
}
export function useMarkFacebookPosted() {
  return useQueueMutation(
    ({ id, url }: { id: string; url: string }) => adminMarketingApi.markPosted(id, url),
    'toast.posted'
  )
}
