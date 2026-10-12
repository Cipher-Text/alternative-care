'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { AlertCircle, ExternalLink, Megaphone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDateFormat } from '@/lib/i18n/date'
import type { FacebookSummary } from '@/types/marketing'

/** What the benefit is, this quarter's usage, why a new request may not be possible, and the live profile link. */
export function BenefitCard({ summary }: { summary: FacebookSummary }) {
  const t = useTranslations('marketingUi')
  const { fmt } = useDateFormat()
  const dates = (d: string) => fmt(d, 'MMM d, yyyy')

  if (!summary.in_plan) {
    return (
      <Card className="border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/30">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Megaphone className="h-5 w-5 text-amber-600" aria-hidden="true" />
            {t('upsell.title')}
          </CardTitle>
          <p className="text-sm text-muted-foreground">{t('what')}</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">{t('upsell.text')}</p>
          <Button asChild className="h-10">
            <Link href="/billing">{t('upsell.cta')}</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  const blockers = summary.blockers.filter((b) => b !== 'not_in_plan')

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Megaphone className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('benefit.title')}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{t('what')}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        <div>
          <p className="text-2xl font-semibold tabular-nums">
            {summary.limit === null
              ? t('benefit.usedUnlimited', { used: summary.used })
              : t('benefit.usedOf', { used: summary.used, limit: summary.limit })}
          </p>
          <p className="text-sm text-muted-foreground">
            {t('benefit.period', { start: dates(summary.period_start), end: dates(summary.period_end) })}
          </p>
          {summary.remaining !== null && (
            <p className="mt-1 text-sm">{t('benefit.remaining', { remaining: summary.remaining })}</p>
          )}
        </div>

        {summary.profile_path && (
          <div className="rounded-lg border bg-muted/40 p-3 text-sm">
            <p className="mb-2">{t('profile.live')}</p>
            <Button asChild variant="outline" className="h-10">
              <Link href={summary.profile_path} target="_blank" rel="noopener">
                <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
                {t('profile.view')}
              </Link>
            </Button>
          </div>
        )}

        {blockers.length > 0 && (
          <ul className="space-y-3" aria-label={t('blockers.heading')}>
            {blockers.map((b) => (
              <li key={b} className="flex gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
                <div className="text-sm">
                  <p className="font-medium">{t(`blockers.${b}.title`)}</p>
                  <p className="text-muted-foreground">
                    {b === 'quota_used'
                      ? t('blockers.quota_used.fix', { date: dates(summary.period_end) })
                      : t(`blockers.${b}.fix`)}
                  </p>
                  {b === 'no_public_profile' && (
                    <Button asChild variant="outline" size="sm" className="mt-2 h-10 sm:h-8">
                      <Link href="/directory">{t('blockers.no_public_profile.cta')}</Link>
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
