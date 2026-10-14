'use client'

import { useTranslations } from 'next-intl'
import { useFacebookSummary } from '@/lib/hooks/useMarketing'
import { BenefitCard } from '@/components/marketing/BenefitCard'
import { RequestForm } from '@/components/marketing/RequestForm'
import { RequestTracker } from '@/components/marketing/RequestTracker'
import { RequestHistory } from '@/components/marketing/RequestHistory'
import { useCan } from '@/lib/auth/permissions'

/** Doctor: ask to be featured on the AltCare Facebook page, approve the exact text, see the result. */
export default function MarketingPage() {
  const t = useTranslations('marketingUi')
  // Doctor-only on the backend; receptionists and platform staff get nothing here
  const { can } = useCan()
  const isDoctor = can('marketing.request')
  const summary = useFacebookSummary(isDoctor)

  if (!isDoctor) return null

  const data = summary.data
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>

      {summary.isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" aria-busy="true" />
      ) : summary.isError || !data ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <>
          <BenefitCard summary={data} />
          {data.in_plan && data.open_request && <RequestTracker request={data.open_request} />}
          {data.in_plan && data.can_request && <RequestForm />}
          {data.in_plan && <RequestHistory history={data.history} />}
        </>
      )}
    </div>
  )
}
