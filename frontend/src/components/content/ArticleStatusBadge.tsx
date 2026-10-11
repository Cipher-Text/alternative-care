'use client'

import { useTranslations } from 'next-intl'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ArticleStatus } from '@/types/article'

const STATUS_STYLES: Record<ArticleStatus, string> = {
  draft: 'border-transparent bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
  in_review: 'border-transparent bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200',
  published: 'border-transparent bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-200',
}

export function ArticleStatusBadge({ status }: { status: ArticleStatus }) {
  const t = useTranslations('contentAdminUi')
  return <Badge className={cn('font-medium', STATUS_STYLES[status])}>{t(`status.${status}`)}</Badge>
}

export function OverdueBadge() {
  const t = useTranslations('contentAdminUi')
  return (
    <Badge className="border-transparent bg-red-100 font-medium text-red-900 dark:bg-red-900/40 dark:text-red-200">
      {t('reviewOverdue')}
    </Badge>
  )
}
