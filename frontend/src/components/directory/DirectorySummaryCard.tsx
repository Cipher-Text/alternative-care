'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { ArrowRight, BadgeCheck } from 'lucide-react'
import { useDirectoryStats } from '@/lib/hooks/useDirectory'
import { Card, CardContent } from '@/components/ui/card'
import { useCan } from '@/lib/auth/permissions'

/** Compact dashboard link to the directory. Doctors only; renders nothing if the stats fail to load. */
export function DirectorySummaryCard() {
  const t = useTranslations('directoryAdminUi')
  const { can } = useCan()
  const isDoctor = can('directory.manage')
  const { data } = useDirectoryStats(isDoctor)
  if (!isDoctor || !data) return null

  return (
    <Link href="/directory" aria-label={t('dashCard.open')} className="block">
      <Card className="transition-colors hover:bg-muted/50">
        <CardContent className="flex items-center gap-3 p-4">
          <BadgeCheck className="h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" />
          <p className="min-w-0 flex-1 text-sm">
            <span className="font-semibold">{t('dashCard.title')}</span>
            <span className="text-muted-foreground"> - {t('dashCard.summary', { requests: data.requests, open: data.open_requests })}</span>
          </p>
          <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        </CardContent>
      </Card>
    </Link>
  )
}
