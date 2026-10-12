'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { AlertTriangle } from 'lucide-react'
import type { CreditChannel } from '@/types/credits'

/** Says that a send was blocked because the channel's credits are used up, and links to Messaging. */
export function CreditsExhaustedNotice({
  channel,
  onNavigate,
}: {
  channel: CreditChannel
  onNavigate?: () => void
}) {
  const t = useTranslations('billingUi')
  return (
    <div role="alert" className="flex items-start gap-3 text-sm">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
      <div className="space-y-1">
        <p className="font-semibold">{t('exhausted.title', { channel: t(`channel.${channel}`) })}</p>
        <p>{t('exhausted.text')}</p>
        <Link
          href="/settings/messaging"
          onClick={onNavigate}
          className="font-medium text-emerald-700 underline underline-offset-2"
        >
          {t('exhausted.link')}
        </Link>
      </div>
    </div>
  )
}
