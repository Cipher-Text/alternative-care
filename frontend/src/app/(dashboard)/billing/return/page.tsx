'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { useOrder } from '@/lib/hooks/useCheckout'
import { useDateFormat } from '@/lib/i18n/date'
import { formatMoney } from '@/lib/billingFormat'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { Order } from '@/types/checkout'
import { useCan } from '@/lib/auth/permissions'

const POLL_MS = 2000
const GIVE_UP_MS = 30000

function Fulfilment({ order }: { order: Order }) {
  const t = useTranslations('billingUi.return')
  const tc = useTranslations('billingUi.channel')
  const { fmt } = useDateFormat()
  const f = order.fulfilment
  if (!f) return null

  if (order.kind === 'subscription') {
    const rawPlan = typeof f.plan === 'string' ? f.plan : order.plan_key
    const plan = rawPlan ? rawPlan.charAt(0).toUpperCase() + rawPlan.slice(1) : null
    const until = typeof f.plan_expires_at === 'string' ? f.plan_expires_at : null
    if (!plan) return null
    return (
      <p className="font-medium">
        {until ? t('planActiveUntil', { plan, date: fmt(until, 'MMM d, yyyy') }) : t('planActive', { plan })}
      </p>
    )
  }

  const channel = f.channel === 'sms' || f.channel === 'email' ? f.channel : order.channel
  const added = typeof f.added === 'number' ? f.added : order.quantity
  const balance = typeof f.balance === 'number' ? f.balance : null
  if (!channel || added === null) return null
  return (
    <p className="font-medium">
      {t(channel === 'sms' ? 'creditsAddedSms' : 'creditsAddedEmail', { count: added })}
      {balance !== null && <> {t('balance', { balance, channel: tc(channel) })}</>}
    </p>
  )
}

function Return() {
  const t = useTranslations('billingUi.return')
  const search = useSearchParams()
  const id = search.get('order')
  const { can } = useCan()
  const isDoctor = can('billing.manage')
  const [timedOut, setTimedOut] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setTimedOut(true), GIVE_UP_MS)
    return () => clearTimeout(timer)
  }, [id])

  // The URL says nothing about the payment: ask the server, which re-checks the gateway, until it settles
  const order = useOrder(id, {
    enabled: isDoctor,
    refetchInterval: (data) => (timedOut || (data && data.status !== 'pending') ? false : POLL_MS),
  })
  const o = order.data

  if (!isDoctor) return null

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <Card>
        <CardContent className="space-y-4 p-6">
          {!id ? (
            <p role="alert" className="text-sm text-red-600">{t('missingOrder')}</p>
          ) : order.error ? (
            <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
          ) : !o || (o.status === 'pending' && !timedOut) ? (
            <div role="status" className="flex items-center gap-3">
              <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
              <p>{t('checking')}</p>
            </div>
          ) : o.status === 'pending' ? (
            <div role="status" className="space-y-2">
              <p className="font-semibold">{t('stillProcessing')}</p>
              <p className="text-sm text-muted-foreground">{t('stillProcessingText')}</p>
            </div>
          ) : o.status === 'paid' ? (
            <div role="status" className="space-y-2">
              <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="h-7 w-7" aria-hidden="true" />
                <p className="text-xl font-bold">{t('successTitle')}</p>
              </div>
              <Fulfilment order={o} />
              <p className="text-sm text-muted-foreground">{o.description} · {formatMoney(o.amount, o.currency)}</p>
            </div>
          ) : (
            <div role="status" className="space-y-2">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                <XCircle className="h-7 w-7" aria-hidden="true" />
                <p className="text-xl font-bold">{t(`title_${o.status}`)}</p>
              </div>
              <p className="text-sm text-muted-foreground">{t('notCharged')}</p>
            </div>
          )}

          {o && (
            <p className="text-sm">
              {t('receiptNo')}: <span className="font-mono font-semibold">{o.receipt_no}</span>
            </p>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            {o && (
              <Button asChild variant="outline" className="h-10">
                <Link href={`/billing/orders/${o.id}`}>{t('viewReceipt')}</Link>
              </Button>
            )}
            {o && o.status !== 'paid' && o.status !== 'pending' && (
              <Button asChild className="h-10">
                <Link href="/billing">{t('tryAgain')}</Link>
              </Button>
            )}
            <Button asChild variant="ghost" className="h-10">
              <Link href="/billing">{t('backToBilling')}</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function BillingReturnPage() {
  return (
    <Suspense fallback={null}>
      <Return />
    </Suspense>
  )
}
