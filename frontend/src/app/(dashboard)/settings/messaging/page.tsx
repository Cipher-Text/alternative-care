'use client'

import { useTranslations } from 'next-intl'
import { AlertTriangle, Loader2, Mail, MessageSquare } from 'lucide-react'
import Link from 'next/link'
import { useAuthStore } from '@/store/authStore'
import { useCredits, useCreditLedger } from '@/lib/hooks/useBilling'
import { usePacks, useSubscription } from '@/lib/hooks/useCheckout'
import { useDateFormat } from '@/lib/i18n/date'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { ChannelBalance, CreditChannel } from '@/types/credits'

const PAGE_SIZE = 20

function ChannelCard({ balance, available }: { balance: ChannelBalance; available: boolean }) {
  const t = useTranslations('billingUi.messaging')
  const tc = useTranslations('billingUi.channel')
  const Icon = balance.channel === 'sms' ? MessageSquare : Mail
  const unlimited = balance.allowance_limit === null
  const pct = unlimited
    ? 0
    : balance.allowance_limit === 0
      ? 100
      : Math.min(100, Math.round((balance.allowance_used / (balance.allowance_limit as number)) * 100))
  const exhausted = !unlimited && (balance.allowance_remaining ?? 0) <= 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {tc(balance.channel)}
        </CardTitle>
        <CardDescription className="capitalize">{t('plan', { plan: balance.plan })}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {!available && (
          <div role="status" className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-semibold">{t('unavailableTitle')}</p>
              <p>{t('unavailableText', { channel: tc(balance.channel) })}</p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-sm font-medium">{t('allowance')}</p>
            {unlimited && <Badge variant="outline">{t('unlimited')}</Badge>}
          </div>
          {!unlimited && (
            <div
              role="progressbar"
              aria-label={t('allowance')}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={pct}
              className="h-2.5 w-full overflow-hidden rounded-full bg-muted"
            >
              <div
                className={`h-full rounded-full ${exhausted ? 'bg-amber-500' : 'bg-emerald-600'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          )}
          <p className="text-sm text-muted-foreground">
            {unlimited
              ? t('usedUnlimited', { used: balance.allowance_used })
              : t('usedOf', { used: balance.allowance_used, limit: balance.allowance_limit as number })}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {!unlimited && (
            <div>
              <p className="text-sm text-muted-foreground">{t('remaining')}</p>
              <p className="text-2xl font-bold">{balance.allowance_remaining ?? 0}</p>
            </div>
          )}
          <div>
            <p className="text-sm text-muted-foreground">{t('purchased')}</p>
            <p className="text-2xl font-bold">{balance.purchased}</p>
            <p className="text-xs text-muted-foreground">{t('purchasedHint')}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function MessagingPage() {
  const t = useTranslations('billingUi.messaging')
  const tc = useTranslations('billingUi.channel')
  const { fmt } = useDateFormat()
  const credits = useCredits()
  // Online purchase is doctors-only, and only offered once packs exist and a payment method is on
  const isDoctor = useAuthStore((s) => s.user?.role === 'doctor')
  const packs = usePacks(isDoctor)
  const subscription = useSubscription(isDoctor)
  const canBuyOnline = isDoctor && (packs.data?.some((p) => p.is_active) ?? false) && (subscription.data?.gateways.length ?? 0) > 0
  const pager = usePager(PAGE_SIZE)
  const ledger = useCreditLedger({ limit: PAGE_SIZE + 1, offset: pager.offset })
  const { items, hasNext } = serverPage(ledger.data, PAGE_SIZE)

  const availability: Record<CreditChannel, boolean> = {
    sms: credits.data?.sms_available ?? true,
    email: credits.data?.email_available ?? true,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
        <p className="mt-1 text-sm text-muted-foreground">{t('order')}</p>
      </div>

      {credits.isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" aria-hidden="true" />
        </div>
      ) : credits.error || !credits.data ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {credits.data.channels.map((b) => (
            <ChannelCard key={b.channel} balance={b} available={availability[b.channel]} />
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('buyTitle')}</CardTitle>
          <CardDescription>{canBuyOnline ? t('buyOnline') : t('buySoon')}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          {canBuyOnline ? (
            <Button asChild className="h-10">
              <Link href="/billing#packs">{t('buyButton')}</Link>
            </Button>
          ) : (
            <>
              <Button disabled className="h-10">{t('buyButton')}</Button>
              <p className="text-sm text-muted-foreground">{t('buyContact')}</p>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('historyTitle')}</CardTitle>
        </CardHeader>
        <CardContent>
          {ledger.isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
            </div>
          ) : ledger.error ? (
            <p role="alert" className="text-sm text-red-600">{t('historyFailed')}</p>
          ) : items.length === 0 && pager.page === 1 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">{t('historyEmpty')}</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('col.date')}</TableHead>
                      <TableHead>{t('col.channel')}</TableHead>
                      <TableHead>{t('col.type')}</TableHead>
                      <TableHead className="text-right">{t('col.quantity')}</TableHead>
                      <TableHead className="text-right">{t('col.balance')}</TableHead>
                      <TableHead>{t('col.note')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell className="whitespace-nowrap">{fmt(row.created_at, 'MMM d, yyyy h:mm a')}</TableCell>
                        <TableCell>{tc(row.channel)}</TableCell>
                        <TableCell>{t(`kind.${row.kind}`)}</TableCell>
                        <TableCell className={`text-right font-medium tabular-nums ${row.quantity > 0 ? 'text-emerald-700' : ''}`}>
                          {row.quantity > 0 ? `+${row.quantity}` : row.quantity}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{row.balance_after}</TableCell>
                        <TableCell className="max-w-xs break-words text-muted-foreground">{row.note || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Pager
                page={pager.page}
                pageSize={PAGE_SIZE}
                count={items.length}
                hasNext={hasNext}
                onPageChange={pager.setPage}
                isLoading={ledger.isFetching}
                noun="entries"
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
