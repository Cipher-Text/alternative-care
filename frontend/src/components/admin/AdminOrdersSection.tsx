'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { useAdminOrders } from '@/lib/hooks/useCheckout'
import { useDateFormat } from '@/lib/i18n/date'
import { formatMoney } from '@/lib/billingFormat'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { OrderStatusBadge } from '@/components/billing/OrderStatusBadge'
import { useGatewayName } from '@/components/billing/GatewayLabel'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { OrderStatus } from '@/types/checkout'

const PAGE_SIZE = 20
const FILTERS = ['all', 'pending', 'paid', 'failed', 'cancelled', 'expired'] as const
type Filter = (typeof FILTERS)[number]

export function AdminOrdersSection() {
  const t = useTranslations('billingUi.adminBilling.orders')
  const ts = useTranslations('billingUi.status')
  const { fmt } = useDateFormat()
  const gatewayName = useGatewayName()
  const [filter, setFilter] = useState<Filter>('all')
  const pager = usePager(PAGE_SIZE, filter)
  const status: OrderStatus | undefined = filter === 'all' ? undefined : filter
  const orders = useAdminOrders({ status, limit: PAGE_SIZE + 1, offset: pager.offset })
  const { items, hasNext } = serverPage(orders.data, PAGE_SIZE)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('title')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
          <TabsList className="flex h-auto flex-wrap justify-start">
            {FILTERS.map((f) => (
              <TabsTrigger key={f} value={f}>{f === 'all' ? t('all') : ts(f)}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

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
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('col.clinic')}</TableHead>
                    <TableHead>{t('col.receipt')}</TableHead>
                    <TableHead>{t('col.description')}</TableHead>
                    <TableHead className="text-right">{t('col.amount')}</TableHead>
                    <TableHead>{t('col.status')}</TableHead>
                    <TableHead>{t('col.gateway')}</TableHead>
                    <TableHead>{t('col.payer')}</TableHead>
                    <TableHead>{t('col.date')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((o) => (
                    <TableRow key={o.id}>
                      <TableCell className="font-medium">{o.tenant_name}</TableCell>
                      <TableCell className="whitespace-nowrap">{o.receipt_no}</TableCell>
                      <TableCell className="min-w-48">{o.description}</TableCell>
                      <TableCell className="whitespace-nowrap text-right tabular-nums">{formatMoney(o.amount, o.currency)}</TableCell>
                      <TableCell><OrderStatusBadge status={o.status} /></TableCell>
                      <TableCell>{gatewayName(o.gateway)}</TableCell>
                      <TableCell>
                        {o.payer_name}
                        {o.payer_phone && <span className="block text-xs text-muted-foreground">{o.payer_phone}</span>}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">{fmt(o.created_at, 'MMM d, yyyy h:mm a')}</TableCell>
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
