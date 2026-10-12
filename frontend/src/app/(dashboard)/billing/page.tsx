'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { Info, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { usePacks, useSubscription } from '@/lib/hooks/useCheckout'
import { formatMoney, localName, planName } from '@/lib/billingFormat'
import { CheckoutConfirmDialog } from '@/components/billing/CheckoutConfirmDialog'
import type { Purchase } from '@/components/billing/CheckoutConfirmDialog'
import { CurrentPlanCard } from '@/components/billing/CurrentPlanCard'
import { OrdersTable } from '@/components/billing/OrdersTable'
import { PlanCard } from '@/components/billing/PlanCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { BillingPeriod, CreditPack, PlanOption } from '@/types/checkout'

/** The clinic's plan, credit packs and receipts. Doctors only: the clinic is the payer. */
export default function BillingPage() {
  const t = useTranslations('billingUi.page')
  const ttest = useTranslations('billingUi.testMode')
  const tp = useTranslations('billingUi.plans')
  const tk = useTranslations('billingUi.packs')
  const tc = useTranslations('billingUi.channel')
  const tf = useTranslations('billingUi.confirm')
  const locale = useLocale()
  const isDoctor = useAuthStore((s) => s.user?.role === 'doctor')
  const sub = useSubscription(isDoctor)
  const packs = usePacks(isDoctor)
  const [purchase, setPurchase] = useState<Purchase | null>(null)

  if (!isDoctor) return null

  const currentPlan = sub.data?.plan
  const gateways = sub.data?.gateways ?? []
  const canPay = gateways.length > 0

  const buyPlan = (option: PlanOption, period: BillingPeriod) => {
    const price = period === 'monthly' ? option.price_monthly : option.price_yearly
    if (price === null) return
    setPurchase({
      summary: tf('planSummary', { plan: planName(option, locale), period: tp(period === 'monthly' ? 'oneMonth' : 'oneYear') }),
      amount: price,
      currency: option.currency,
      build: (gateway) => ({ kind: 'subscription', gateway, plan_key: option.plan_key, period }),
    })
  }

  const buyPack = (pack: CreditPack) => {
    setPurchase({
      summary: tf('packSummary', {
        name: localName(pack.name_en, pack.name_bn, locale),
        quantity: pack.quantity,
        channel: tc(pack.channel),
      }),
      amount: pack.price,
      currency: pack.currency,
      build: (gateway) => ({ kind: 'credit_pack', gateway, pack_id: pack.id }),
    })
  }

  const activePacks = (packs.data ?? []).filter((p) => p.is_active)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>

      {sub.isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" aria-hidden="true" />
        </div>
      ) : sub.error || !sub.data ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <>
          {!canPay && (
            <div role="status" className="flex items-start gap-2 rounded-lg border bg-muted/40 p-3 text-sm">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold">{t('noGatewayTitle')}</p>
                <p className="text-muted-foreground">{t('noGatewayText')}</p>
              </div>
            </div>
          )}

          {canPay && sub.data.test_mode && (
            <div role="status" className="flex items-start gap-2 rounded-lg border border-amber-500/60 bg-amber-50 p-3 text-sm dark:bg-amber-950/30">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
              <div>
                <p className="font-semibold">{ttest('title')}</p>
                <p className="text-muted-foreground">{ttest('body')}</p>
              </div>
            </div>
          )}

          <CurrentPlanCard sub={sub.data} />

          <section aria-labelledby="plans-heading" className="space-y-3">
            <h2 id="plans-heading" className="text-xl font-semibold">{tp('title')}</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {sub.data.options.map((o) => (
                <PlanCard key={o.plan_key} option={o} isCurrent={o.plan_key === currentPlan} canPay={canPay} onBuy={buyPlan} />
              ))}
            </div>
          </section>

          <section id="packs" aria-labelledby="packs-heading" className="scroll-mt-20 space-y-3">
            <div>
              <h2 id="packs-heading" className="text-xl font-semibold">{tk('title')}</h2>
              <p className="text-sm text-muted-foreground">
                {tk('note')}{' '}
                <Link href="/settings/messaging" className="text-emerald-700 underline dark:text-emerald-400">{tk('noteLink')}</Link>
              </p>
            </div>
            {packs.isLoading ? (
              <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
            ) : packs.error ? (
              <p role="alert" className="text-sm text-red-600">{tk('loadFailed')}</p>
            ) : activePacks.length === 0 ? (
              <p className="text-sm text-muted-foreground">{tk('empty')}</p>
            ) : (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {(['sms', 'email'] as const).map((channel) => {
                  const list = activePacks.filter((p) => p.channel === channel).sort((a, b) => a.sort_order - b.sort_order)
                  if (list.length === 0) return null
                  return (
                    <Card key={channel}>
                      <CardHeader>
                        <CardTitle>{tc(channel)}</CardTitle>
                        <CardDescription>{tk('channelHint', { channel: tc(channel) })}</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {list.map((p) => (
                          <div key={p.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3">
                            <div>
                              <p className="font-medium">{localName(p.name_en, p.name_bn, locale)}</p>
                              <p className="text-sm text-muted-foreground">
                                {tk('quantity', { quantity: p.quantity })} · {formatMoney(p.price, p.currency)}
                              </p>
                            </div>
                            {canPay && (
                              <Button className="h-10" onClick={() => buyPack(p)}>
                                {tk('buy')}
                              </Button>
                            )}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}
          </section>
        </>
      )}

      <OrdersTable />

      <CheckoutConfirmDialog purchase={purchase} gateways={gateways} onClose={() => setPurchase(null)} />
    </div>
  )
}
