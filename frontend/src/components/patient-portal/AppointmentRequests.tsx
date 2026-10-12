'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { identityError } from '@/components/identity/identityUtils'
import { useDateFormat } from '@/lib/i18n/date'
import { useCancelPortalRequest, usePortalMe, usePortalRequests } from '@/lib/hooks/usePatientPortal'
import type { PatientRequest, RequestStatus } from '@/types/appointmentRequest'
import { AddProfileForm } from './AddProfileForm'
import { isUnauthorized, localDate, portalButtonOutline, portalErrorBox } from './portalUtils'

const card = 'rounded-lg border border-gray-200 p-4 dark:border-slate-800'
const STATUS_STYLE: Record<RequestStatus, string> = {
  requested: 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
  confirmed: 'bg-emerald-600 text-white',
  declined: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
  cancelled: 'bg-gray-100 text-gray-900 dark:bg-slate-800 dark:text-gray-200',
}

type SignedOut = (expired: boolean) => void

/** "My appointment requests": what the patient asked for, and what the clinics answered. */
export function MyRequests({ onSignedOut }: { onSignedOut: SignedOut }) {
  const t = useTranslations('patientPortalUi.myRequests')
  const { fmt } = useDateFormat()
  const requests = usePortalRequests(true)
  const cancel = useCancelPortalRequest()
  const [target, setTarget] = useState<PatientRequest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [now] = useState(() => Date.now())

  useEffect(() => {
    if (requests.error && isUnauthorized(requests.error)) onSignedOut(true)
  }, [requests.error, onSignedOut])

  const canCancel = (r: PatientRequest) =>
    r.status === 'requested' ||
    (r.status === 'confirmed' && r.appointment !== null && localDate(r.appointment.date, r.appointment.time).getTime() > now)

  async function doCancel() {
    if (!target) return
    try {
      await cancel.mutateAsync(target.id)
      setTarget(null)
      setError(null)
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      const { code } = identityError(err)
      setError(code === 'not_cancellable' ? t('errors.notCancellable') : t('errors.generic'))
    }
  }

  const items = requests.data ?? []

  return (
    <section className="space-y-3" aria-labelledby="my-requests-title">
      <h2 id="my-requests-title" className="text-xl font-semibold text-gray-900 dark:text-white">{t('title')}</h2>

      {requests.isLoading && <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label={t('loading')} />}
      {requests.isError && !isUnauthorized(requests.error) && (
        <div role="alert" className={portalErrorBox}>
          <p>{t('loadFailed')}</p>
          <button type="button" className={`${portalButtonOutline} mt-2`} onClick={() => void requests.refetch()}>{t('retry')}</button>
        </div>
      )}
      {requests.data && items.length === 0 && (
        <p className="rounded-lg border border-dashed border-gray-300 p-4 text-base text-gray-600 dark:border-slate-700 dark:text-gray-400">{t('empty')}</p>
      )}

      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id} className={`${card} space-y-1`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-base font-semibold">{r.clinic_name}{r.doctor_name ? ` · ${r.doctor_name}` : ''}</p>
              <span className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${STATUS_STYLE[r.status]}`}>{t(`status.${r.status}`)}</span>
            </div>
            <p className="text-base text-gray-700 dark:text-gray-300">{t('person', { name: r.profile_name })}</p>
            {r.status === 'confirmed' && r.appointment ? (
              <p className="text-base font-semibold text-emerald-800 dark:text-emerald-300">
                {t('bookedFor', {
                  date: fmt(localDate(r.appointment.date), 'EEE, MMM d, yyyy'),
                  time: fmt(localDate(r.appointment.date, r.appointment.time), 'h:mm a'),
                })}
              </p>
            ) : (
              <p className="text-base text-gray-700 dark:text-gray-300">
                {t('preferred', { date: fmt(localDate(r.preferred_date), 'EEE, MMM d, yyyy'), window: t(`windows.${r.preferred_window}`) })}
              </p>
            )}
            {r.status === 'declined' && r.decline_reason && (
              <p className="text-base text-red-800 dark:text-red-300">{t('declineReason', { reason: r.decline_reason })}</p>
            )}
            {r.status === 'cancelled' && r.cancelled_by && (
              <p className="text-sm text-gray-600 dark:text-gray-400">{r.cancelled_by === 'patient' ? t('cancelledByYou') : t('cancelledByClinic')}</p>
            )}
            {canCancel(r) && (
              <button type="button" className={`${portalButtonOutline} mt-2 py-2`} onClick={() => { setError(null); setTarget(r) }}>
                {r.status === 'requested' ? t('cancelRequest') : t('cancelAppointment')}
              </button>
            )}
          </li>
        ))}
      </ul>

      <Dialog open={!!target} onOpenChange={(o) => { if (!o && !cancel.isLoading) setTarget(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{target?.status === 'confirmed' ? t('cancelAppointmentTitle') : t('cancelRequestTitle')}</DialogTitle>
            <DialogDescription>{t('cancelBody', { clinic: target?.clinic_name ?? '' })}</DialogDescription>
          </DialogHeader>
          {error && <p role="alert" className={portalErrorBox}>{error}</p>}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setTarget(null)} disabled={cancel.isLoading}>{t('keep')}</Button>
            <Button variant="destructive" onClick={doCancel} disabled={cancel.isLoading}>
              {cancel.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('confirmCancel')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  )
}

/** Add yourself (when there is no own profile yet) or a child, and a way into the practitioner directory. */
export function AddPersonCard({ onSignedOut }: { onSignedOut: SignedOut }) {
  const t = useTranslations('patientPortalUi.addPerson')
  const me = usePortalMe(true)
  const [open, setOpen] = useState(false)
  const hasSelf = (me.data?.profiles ?? []).some((p) => p.relationship === 'self')

  return (
    <section className={`${card} space-y-3`}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('title')}</h2>
      <p className="text-base text-gray-600 dark:text-gray-400">{t('body')}</p>
      {open ? (
        <AddProfileForm hasSelf={hasSelf} idPrefix="dash-add" onAdded={() => setOpen(false)} onCancel={() => setOpen(false)} onSignedOut={onSignedOut} />
      ) : (
        <div className="flex flex-wrap gap-2">
          <button type="button" className={portalButtonOutline} onClick={() => setOpen(true)}>{hasSelf ? t('addChild') : t('addPerson')}</button>
          <Link href="/practitioners" className={portalButtonOutline}>{t('findPractitioner')}</Link>
        </div>
      )}
    </section>
  )
}
