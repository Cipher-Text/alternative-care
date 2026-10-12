'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Phone } from 'lucide-react'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { localDate } from '@/components/patient-portal/portalUtils'
import { useAppointmentRequests } from '@/lib/hooks/useAppointmentRequests'
import { useDateFormat } from '@/lib/i18n/date'
import type { ClinicRequest, RequestStatus } from '@/types/appointmentRequest'
import { ConfirmRequestDialog } from './ConfirmRequestDialog'
import { DeclineRequestDialog } from './DeclineRequestDialog'

const TABS: RequestStatus[] = ['requested', 'confirmed', 'declined', 'cancelled']

/** Patients' appointment requests. Personal data: one page at a time, no export. */
export function RequestsList() {
  const t = useTranslations('appointmentRequestsUi')
  const { fmt } = useDateFormat()
  const [status, setStatus] = useState<RequestStatus>('requested')
  const pager = usePager(undefined, status)
  const [confirming, setConfirming] = useState<ClinicRequest | null>(null)
  const [declining, setDeclining] = useState<ClinicRequest | null>(null)

  const { data, isLoading, isError, refetch } = useAppointmentRequests({
    status,
    limit: pager.pageSize + 1, // one extra row tells us whether a next page exists
    offset: pager.offset,
  })
  const { items, hasNext } = serverPage(data, pager.pageSize)

  const genderLabel = (g: string | null) => (g === 'male' || g === 'female' || g === 'other' ? t(`gender.${g}`) : null)

  return (
    <div className="space-y-4">
      <Tabs value={status} onValueChange={(v) => setStatus(v as RequestStatus)}>
        <TabsList className="h-auto flex-wrap">
          {TABS.map((s) => <TabsTrigger key={s} value={s} className="min-h-9">{t(`tabs.${s}`)}</TabsTrigger>)}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-2" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-28 animate-pulse rounded-lg bg-muted" />)}
        </div>
      ) : isError ? (
        <div role="alert" className="space-y-2 text-sm text-red-600">
          <p>{t('loadFailed')}</p>
          <Button size="sm" variant="outline" onClick={() => void refetch()}>{t('retry')}</Button>
        </div>
      ) : items.length === 0 ? (
        <Card><CardContent className="py-10 text-center text-muted-foreground">{t(`empty.${status}`)}</CardContent></Card>
      ) : (
        <ul className="space-y-3">
          {items.map((r) => {
            const who = r.requester
            const gender = genderLabel(who.gender)
            return (
              <li key={r.id}>
                <Card>
                  <CardContent className="space-y-3 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-lg font-semibold">
                          {who.display_name}
                          {who.is_dependent && <Badge variant="outline" className="ml-2 align-middle">{t('dependent')}</Badge>}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {[who.age_years != null ? t('age', { count: who.age_years }) : null, gender].filter(Boolean).join(' · ')}
                        </p>
                        <a href={`tel:${who.phone}`} aria-label={t('callPatient', { name: who.display_name })} className="mt-1 inline-flex items-center gap-1.5 text-sm text-primary underline">
                          <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                          {who.phone}
                        </a>
                      </div>
                      <p className="text-sm text-muted-foreground">{t('received', { date: fmt(r.created_at, 'MMM d, yyyy h:mm a') })}</p>
                    </div>

                    <div className="space-y-1 text-sm">
                      <p>
                        <span className="font-medium">{t('preferred')}</span>{' '}
                        {fmt(localDate(r.preferred_date), 'EEE, MMM d, yyyy')} · {t(`windows.${r.preferred_window}`)}
                      </p>
                      {r.doctor_name && <p><span className="font-medium">{t('askedFor')}</span> {r.doctor_name}</p>}
                      {r.reason && (
                        <blockquote className="whitespace-pre-wrap break-words border-l-2 border-muted-foreground/30 pl-3 italic text-muted-foreground">
                          {r.reason}
                        </blockquote>
                      )}
                    </div>

                    <p className="text-sm text-muted-foreground">
                      {r.existing_patient_id ? (
                        <>
                          {t('existingRecord')}{' '}
                          <Link href={`/patients/${r.existing_patient_id}`} className="text-primary underline">{t('openRecord')}</Link>
                        </>
                      ) : r.status === 'requested' ? (
                        t('newRecord')
                      ) : null}
                    </p>

                    {r.status === 'confirmed' && r.appointment && (
                      <p className="rounded-md bg-emerald-50 p-3 text-sm font-medium text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
                        {t('bookedFor', {
                          date: fmt(localDate(r.appointment.date), 'EEE, MMM d, yyyy'),
                          time: fmt(localDate(r.appointment.date, r.appointment.time), 'h:mm a'),
                          minutes: r.appointment.duration_minutes,
                        })}
                        {r.patient_id && (
                          <>{' '}<Link href={`/patients/${r.patient_id}`} className="underline">{t('openRecord')}</Link></>
                        )}
                      </p>
                    )}
                    {r.status === 'declined' && r.decline_reason && (
                      <p className="text-sm">{t('declineReason', { reason: r.decline_reason })}</p>
                    )}
                    {r.status === 'cancelled' && r.cancelled_by && (
                      <p className="text-sm text-muted-foreground">{r.cancelled_by === 'patient' ? t('cancelledByPatient') : t('cancelledByClinic')}</p>
                    )}

                    {r.status === 'requested' && (
                      <div className="flex flex-wrap gap-2">
                        <Button size="sm" className="h-9" onClick={() => setConfirming(r)}>{t('confirmAction')}</Button>
                        <Button size="sm" variant="outline" className="h-9" onClick={() => setDeclining(r)}>{t('declineAction')}</Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </li>
            )
          })}
        </ul>
      )}

      <Pager page={pager.page} pageSize={pager.pageSize} count={items.length} hasNext={hasNext} onPageChange={pager.setPage} isLoading={isLoading} noun="requests" />

      <ConfirmRequestDialog request={confirming} onClose={() => setConfirming(null)} />
      <DeclineRequestDialog request={declining} onClose={() => setDeclining(null)} />
    </div>
  )
}
