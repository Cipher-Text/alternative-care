'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { formatMoney, planName, yearlySaving } from '@/lib/billingFormat'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { BillingPeriod, PlanOption } from '@/types/checkout'

export function PlanCard({
  option,
  isCurrent,
  canPay,
  onBuy,
}: {
  option: PlanOption
  isCurrent: boolean
  /** At least one payment method is available */
  canPay: boolean
  onBuy: (option: PlanOption, period: BillingPeriod) => void
}) {
  const t = useTranslations('billingUi.plans')
  const locale = useLocale()
  const periods = (['monthly', 'yearly'] as const).filter((p) =>
    (p === 'monthly' ? option.price_monthly : option.price_yearly) !== null
  )
  const [chosen, setChosen] = useState<BillingPeriod>('monthly')
  const period: BillingPeriod = periods.includes(chosen) ? chosen : (periods[0] ?? 'monthly')
  const saving = yearlySaving(option)
  const payable = option.action === 'subscribe' || option.action === 'renew' || option.action === 'upgrade'

  return (
    <Card className={isCurrent ? 'border-emerald-500' : undefined}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-2">
          {planName(option, locale)}
          {isCurrent && <Badge variant="outline">{t('yourPlan')}</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {periods.length > 0 ? (
          <div role="radiogroup" aria-label={t('period')} className="grid grid-cols-2 gap-2">
            {periods.map((p) => {
              const price = p === 'monthly' ? option.price_monthly : option.price_yearly
              const selected = p === period
              return (
                <button
                  key={p}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setChosen(p)}
                  className={`rounded-lg border p-3 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                    selected ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950' : 'hover:border-emerald-300'
                  }`}
                >
                  <span className="block text-xs text-muted-foreground">{t(p)}</span>
                  <span className="block text-lg font-bold">{formatMoney(price, option.currency)}</span>
                  <span className="block text-xs text-muted-foreground">{t(p === 'monthly' ? 'perMonth' : 'perYear')}</span>
                </button>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t('noPrice')}</p>
        )}
        {saving && periods.includes('yearly') && (
          <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
            {t('saving', { amount: formatMoney(saving.amount, option.currency), percent: saving.percent })}
          </p>
        )}

        {option.action === 'current' && <p className="text-sm text-muted-foreground">{t('action.current')}</p>}
        {option.action === 'unavailable' && <p className="text-sm text-muted-foreground">{t('action.unavailable')}</p>}
        {option.action === 'blocked' && (
          <div className="space-y-2">
            <Button disabled className="h-10 w-full">{t('action.blocked')}</Button>
            {option.reason && <p className="text-sm text-muted-foreground">{option.reason}</p>}
          </div>
        )}
        {payable && canPay && periods.length > 0 && (
          <Button className="h-10 w-full" onClick={() => onBuy(option, period)}>
            {t(`action.${option.action as 'subscribe' | 'renew' | 'upgrade'}`)}
          </Button>
        )}
        {payable && option.reason && <p className="text-sm text-muted-foreground">{option.reason}</p>}
      </CardContent>
    </Card>
  )
}
