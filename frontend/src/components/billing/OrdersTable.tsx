'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { useOrders } from '@/lib/hooks/useCheckout'
import { useDateFormat } from '@/lib/i18n/date'
import { formatMoney } from '@/lib/billingFormat'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { OrderStatusBadge } from '@/components/billing/OrderStatusBadge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const PAGE_SIZE = 10

export function OrdersTable() {
  const t = useTranslations('billingUi.orders')
  const router = useRouter()
  const { fmt } = useDateFormat()
  const pager = usePager(PAGE_SIZE)
  const orders = useOrders({ limit: PAGE_SIZE + 1, offset: pager.offset })
  const { items, hasNext } = serverPage(orders.data, PAGE_SIZE)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('title')}</CardTitle>
      </CardHeader>
      <CardContent>
        {orders.isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
          </div>
        ) : orders.error ? (
          <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
        ) : items.length === 0 && pager.page === 1 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{t('empty')}</p>
        ) : (
          <>
            <p className="mb-2 text-xs text-muted-foreground">{t('clickHint')}</p>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('col.receipt')}</TableHead>
                    <TableHead>{t('col.date')}</TableHead>
                    <TableHead>{t('col.description')}</TableHead>
                    <TableHead className="text-right">{t('col.amount')}</TableHead>
                    <TableHead>{t('col.status')}</TableHead>
                    <TableHead>{t('col.payer')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((o) => (
                    <TableRow key={o.id} className="cursor-pointer" onClick={() => router.push(`/billing/orders/${o.id}`)}>
                      <TableCell className="whitespace-nowrap font-medium">
                        <Link href={`/billing/orders/${o.id}`} className="text-emerald-700 underline-offset-2 hover:underline dark:text-emerald-400" onClick={(e) => e.stopPropagation()}>
                          {o.receipt_no}
                        </Link>
                      </TableCell>
                      <TableCell className="whitespace-nowrap">{fmt(o.created_at, 'MMM d, yyyy h:mm a')}</TableCell>
                      <TableCell className="min-w-48">{o.description}</TableCell>
                      <TableCell className="whitespace-nowrap text-right tabular-nums">{formatMoney(o.amount, o.currency)}</TableCell>
                      <TableCell><OrderStatusBadge status={o.status} /></TableCell>
                      <TableCell>{o.payer_name}</TableCell>
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
              isLoading={orders.isFetching}
              noun="orders"
            />
          </>
        )}
      </CardContent>
    </Card>
  )
}
