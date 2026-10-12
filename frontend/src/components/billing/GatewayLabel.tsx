'use client'

import { useTranslations } from 'next-intl'
import { Badge } from '@/components/ui/badge'

/** Payment method name. The fake gateway is labelled as a test with a clear TEST badge. */
export function GatewayLabel({ gateway }: { gateway: string }) {
  const t = useTranslations('billingUi.gateway')
  if (gateway === 'fake') {
    return (
      <span className="inline-flex items-center gap-2">
        {t('fake')}
        <Badge className="border-transparent bg-amber-500 text-black">{t('testBadge')}</Badge>
      </span>
    )
  }
  return <span>{gateway}</span>
}

/** Plain-text name (table cells). */
export function useGatewayName() {
  const t = useTranslations('billingUi.gateway')
  return (gateway: string) => (gateway === 'fake' ? t('fake') : gateway)
}
