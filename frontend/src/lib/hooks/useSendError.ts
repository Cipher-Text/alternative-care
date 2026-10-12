import { useCallback } from 'react'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { createElement } from 'react'
import { CreditsExhaustedNotice } from '@/components/billing/CreditsExhaustedNotice'
import { creditsExhausted, errorMessage, isCreditChannel } from '@/lib/apiErrors'

/**
 * Toast for a failed SMS/email send: the "no credits left" notice with a link to Messaging when
 * that is the cause, otherwise the server's message (never "[object Object]").
 */
export function useSendErrorToast() {
  const t = useTranslations('billingUi')
  return useCallback(
    (error: unknown, fallback?: string) => {
      const exhausted = creditsExhausted(error)
      if (exhausted && isCreditChannel(exhausted.channel)) {
        toast.custom(
          (item) =>
            createElement(
              'div',
              { className: 'max-w-sm rounded-lg border bg-white p-4 text-slate-900 shadow-lg dark:bg-slate-900 dark:text-slate-100' },
              createElement(CreditsExhaustedNotice, {
                channel: exhausted.channel,
                onNavigate: () => toast.dismiss(item.id),
              })
            ),
          { duration: 10000 }
        )
        return
      }
      toast.error(errorMessage(error, fallback ?? t('exhausted.sendFailed')))
    },
    [t]
  )
}
