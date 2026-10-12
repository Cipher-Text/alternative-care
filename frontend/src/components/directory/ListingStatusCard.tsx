'use client'

import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { CheckCircle2, Circle, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Listing, ListingBlocker } from '@/types/directory'

const GATES: ListingBlocker[] = [
  'not_listed',
  'not_verified',
  'not_approved',
  'not_in_plan',
  'no_profile_text',
]

/** Checklist of the five conditions for appearing publicly, with how to fix each one that is missing. */
export function ListingStatusCard({ listing }: { listing: Listing }) {
  const t = useTranslations('directoryAdminUi')
  const eligibility = listing.eligibility
  const isPublic = !!eligibility?.public
  // If the server sent no eligibility, assume nothing is done rather than claiming success
  const blockers = eligibility?.blockers ?? GATES

  return (
    <Card
      className={isPublic ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950/30' : undefined}
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-wrap items-center gap-2 text-lg">
          {isPublic ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          ) : (
            <Circle className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          )}
          {isPublic ? t('status.liveTitle') : t('status.notLiveTitle')}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {isPublic ? t('status.liveText') : t('status.notLiveText')}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {isPublic && listing.slug && (
          <Button asChild variant="outline" className="h-10">
            <Link href={`/practitioners/${listing.slug}`} target="_blank" rel="noopener">
              <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
              {t('status.viewProfile')}
            </Link>
          </Button>
        )}
        <ul className="space-y-3">
          {GATES.map((gate) => {
            const done = !blockers.includes(gate)
            return (
              <li key={gate} className="flex gap-3">
                {done ? (
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" />
                ) : (
                  <Circle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
                )}
                <div className="min-w-0 text-sm">
                  <p className="font-medium">
                    {t(`status.gate.${gate}.label`)}
                    <span className="sr-only"> - {done ? t('status.done') : t('status.todo')}</span>
                  </p>
                  {!done && (
                    <p className="text-muted-foreground">
                      {t(`status.gate.${gate}.fix`)}{' '}
                      {gate === 'not_in_plan' && (
                        <Link href="/pricing" className="font-medium text-primary underline">
                          {t('status.gate.not_in_plan.link')}
                        </Link>
                      )}
                    </p>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
        <p className="text-xs text-muted-foreground">{t('status.paymentNote')}</p>
      </CardContent>
    </Card>
  )
}
