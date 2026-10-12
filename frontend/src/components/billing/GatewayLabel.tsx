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
  return <span>{gatewayText(gateway, t)}</span>
}

/** Known providers get a plain name; an unknown one shows as is. */
function gatewayText(gateway: string, t: (key: string) => string): string {
  if (gateway === 'sslcommerz') return t('sslcommerz')
  if (gateway === 'bkash') return t('bkash')
  if (gateway === 'fake') return t('fake')
  if (gateway === 'manual') return t('manual')
  return gateway
}

/** Plain-text name (table cells). */
export function useGatewayName() {
  const t = useTranslations('billingUi.gateway')
  return (gateway: string) => gatewayText(gateway, t)
}
