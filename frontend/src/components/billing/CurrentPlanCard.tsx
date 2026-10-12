'use client'

import { useLocale, useTranslations } from 'next-intl'
import { AlertTriangle, CalendarClock } from 'lucide-react'
import { useDateFormat } from '@/lib/i18n/date'
import { planKeyName, planName } from '@/lib/billingFormat'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { SubscriptionInfo } from '@/types/checkout'

export function CurrentPlanCard({ sub }: { sub: SubscriptionInfo }) {
  const t = useTranslations('billingUi.current')
  const locale = useLocale()
  const { fmt } = useDateFormat()

  const current = sub.options.find((o) => o.plan_key === sub.plan)
  const name = current ? planName(current, locale) : planKeyName(sub.plan, locale)
  const noExpiry = sub.plan_expires_at === null
  const soon = !sub.expired && sub.days_left !== null && sub.days_left <= 7

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-3">
          <CalendarClock className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-2xl font-bold">{name}</p>
          {sub.expired ? (
            <Badge variant="destructive">{t('statusExpired')}</Badge>
          ) : noExpiry ? (
            <Badge variant="outline">{t('statusNoExpiry')}</Badge>
          ) : (
            <Badge className="border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100">
              {t('statusActive')}
            </Badge>
          )}
        </div>

        {!noExpiry && sub.plan_expires_at && (
          <p className="text-sm text-muted-foreground">
            {sub.expired ? t('expiredOn', { date: fmt(sub.plan_expires_at, 'MMM d, yyyy') }) : t('expiresOn', { date: fmt(sub.plan_expires_at, 'MMM d, yyyy') })}
            {!sub.expired && sub.days_left !== null && (
              <span className="ml-1 font-medium text-foreground">
                {sub.days_left === 0 ? `(${t('expiresToday')})` : `(${t('daysLeft', { days: sub.days_left })})`}
              </span>
            )}
          </p>
        )}
        {noExpiry && <p className="text-sm text-muted-foreground">{t('noExpiryText')}</p>}

        {(sub.expired || soon) && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-semibold">{sub.expired ? t('expiredTitle') : t('soonTitle')}</p>
              <p>{sub.expired ? t('expiredText') : t('soonText')}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
