'use client'

import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useDateFormat } from '@/lib/i18n/date'
import { usePatientSharing } from '@/lib/hooks/useSharing'
import type { ShareSummary } from '@/types/sharing'
import { useCan } from '@/lib/auth/permissions'

/**
 * "Sharing between clinics" for a linked patient: clinic names, dates and read counts only.
 * The shared records themselves are loaded only on the shared-records page, because loading them is logged.
 */
export function SharingBlock({ patientId }: { patientId: string }) {
  const t = useTranslations('sharingUi')
  const { fmt } = useDateFormat()
  const router = useRouter()
  const { can } = useCan()
  const canRevoke = can('identity.revoke')
  const { data, isLoading, isError, refetch } = usePatientSharing(patientId)

  const date = (d: string) => fmt(d, 'MMM d, yyyy')
  const when = (d: string) => fmt(d, 'MMM d, yyyy, h:mm a')
  const chip = (s: ShareSummary) => (
    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-slate-800">{t(`status.${s.status}`)}</span>
  )
  const empty = !!data && data.incoming.length === 0 && data.outgoing.length === 0

  return (
    <div className="space-y-3 border-t pt-4">
      <h3 className="text-sm font-semibold">{t('clinic.title')}</h3>
      {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" aria-label={t('clinic.loading')} />}
      {isError && (
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span>{t('clinic.loadFailed')}</span>
          <Button size="sm" variant="outline" onClick={() => refetch()}>{t('clinic.retry')}</Button>
        </div>
      )}
      {empty && <p className="text-sm text-muted-foreground">{t('clinic.none')}</p>}

      {data && data.incoming.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('clinic.incomingHeading')}</p>
          <ul className="space-y-2">
            {data.incoming.map((s) => (
              <li key={s.share_id} className="space-y-1 rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{t('clinic.incoming', { clinic: s.clinic_name, date: date(s.expires_at) })}</span>
                  {chip(s)}
                </div>
                <p className="text-muted-foreground">
                  {s.access_count > 0 && s.last_accessed_at
                    ? t('clinic.incomingReads', { count: s.access_count, date: when(s.last_accessed_at) })
                    : t('clinic.incomingNotOpened')}
                </p>
                {canRevoke && s.status === 'active' && (
                  <Button size="sm" onClick={() => router.push(`/patients/${patientId}/shared-records`)}>
                    {t('clinic.open')}
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data && data.outgoing.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('clinic.outgoingHeading')}</p>
          <ul className="space-y-2">
            {data.outgoing.map((s) => (
              <li key={s.share_id} className="space-y-1 rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{t('clinic.outgoing', { clinic: s.clinic_name, date: date(s.expires_at) })}</span>
                  {chip(s)}
                </div>
                <p className="text-muted-foreground">
                  {s.access_count > 0 && s.last_accessed_at
                    ? t('clinic.outgoingReads', { count: s.access_count, date: when(s.last_accessed_at) })
                    : t('clinic.outgoingNotOpened')}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
