'use client'

import { useTranslations } from 'next-intl'
import { Badge } from '@/components/ui/badge'
import type { OrderStatus } from '@/types/checkout'

const STYLE: Record<OrderStatus, string> = {
  paid: 'border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100',
  pending: 'border-transparent bg-amber-100 text-amber-900 dark:bg-amber-900 dark:text-amber-100',
  failed: 'border-transparent bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
  cancelled: 'border-transparent bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100',
  expired: 'border-transparent bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100',
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const t = useTranslations('billingUi.status')
  return <Badge className={STYLE[status] ?? ''}>{t(status)}</Badge>
}
