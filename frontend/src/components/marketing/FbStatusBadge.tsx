'use client'

import { useTranslations } from 'next-intl'
import { Badge } from '@/components/ui/badge'
import type { FbStatus } from '@/types/marketing'

const STYLE: Record<FbStatus, string> = {
  requested: 'border-transparent bg-amber-100 text-amber-900 dark:bg-amber-900 dark:text-amber-100',
  drafted: 'border-transparent bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100',
  approved: 'border-transparent bg-indigo-100 text-indigo-900 dark:bg-indigo-900 dark:text-indigo-100',
  posted: 'border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100',
  rejected: 'border-transparent bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
  cancelled: 'border-transparent bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100',
}

export function FbStatusBadge({ status }: { status: FbStatus }) {
  const t = useTranslations('marketingUi.status')
  return <Badge className={STYLE[status] ?? ''}>{t(status)}</Badge>
}
