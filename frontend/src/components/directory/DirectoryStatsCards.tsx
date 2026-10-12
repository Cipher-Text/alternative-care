'use client'

import { useTranslations } from 'next-intl'
import { Card, CardContent } from '@/components/ui/card'
import type { DirectoryStats } from '@/types/directory'

/** This month's contact numbers. Zeros are shown on purpose: they are information, not an empty state. */
export function DirectoryStatsCards({ stats }: { stats: DirectoryStats }) {
  const t = useTranslations('directoryAdminUi')
  const items = [
    { key: 'requests', value: stats.requests },
    { key: 'calls', value: stats.calls },
    { key: 'whatsapp', value: stats.whatsapp },
    { key: 'open', value: stats.open_requests },
  ] as const

  return (
    <section aria-labelledby="dir-stats-title" className="space-y-3">
      <h2 id="dir-stats-title" className="text-lg font-semibold text-gray-900 dark:text-white">
        {t('stats.title')}
      </h2>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {items.map((item) => (
          <Card key={item.key}>
            <CardContent className="p-4">
              <p className="text-3xl font-bold tabular-nums">{item.value}</p>
              <p className="mt-1 text-sm text-muted-foreground">{t(`stats.${item.key}`)}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">{t('stats.hint')}</p>
    </section>
  )
}
