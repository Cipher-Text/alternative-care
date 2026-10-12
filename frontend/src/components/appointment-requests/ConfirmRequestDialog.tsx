'use client'

import Link from 'next/link'
import { useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { identityError } from '@/components/identity/identityUtils'
import { isoDateFromToday, localDate } from '@/components/patient-portal/portalUtils'
import { useConfirmAppointmentRequest, useRefreshAppointmentRequests } from '@/lib/hooks/useAppointmentRequests'
import { useDateFormat } from '@/lib/i18n/date'
import { useAuthStore } from '@/store/authStore'
import type { ClinicRequest } from '@/types/appointmentRequest'

const DURATIONS = [15, 30, 45, 60, 90, 120, 180, 240]
const selectClass = 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm'

interface Props {
  request: ClinicRequest | null
  onClose: () => void
}

/** Confirm a request with an exact date and time: this books the appointment. */
export function ConfirmRequestDialog({ request, onClose }: Props) {
  // The form is keyed by the request, so each opening starts from that request's own defaults
  return (
    <Dialog open={!!request} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent>{request && <ConfirmForm key={request.id} request={request} onClose={onClose} />}</DialogContent>
    </Dialog>
  )
}

function ConfirmForm({ request, onClose }: { request: ClinicRequest; onClose: () => void }) {
  const t = useTranslations('appointmentRequestsUi.confirm')
  const { fmt } = useDateFormat()
  const user = useAuthStore((s) => s.user)
  const confirm = useConfirmAppointmentRequest()
  const refresh = useRefreshAppointmentRequests()

  // The clinic's doctors we know of: the practitioner they asked for, and the signed-in doctor
  const doctors: { id: string; name: string }[] = []
  if (request.doctor_id) doctors.push({ id: request.doctor_id, name: request.doctor_name ?? request.doctor_id })
  if (user?.role === 'doctor' && !doctors.some((d) => d.id === user.id)) doctors.push({ id: user.id, name: user.full_name })

  const [date, setDate] = useState(request.preferred_date)
  const [time, setTime] = useState('')
  const [duration, setDuration] = useState(30)
  const [doctorId, setDoctorId] = useState(doctors[0]?.id ?? '')
  const [notify, setNotify] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [limitReached, setLimitReached] = useState(false)

  const today = isoDateFromToday(0)
  const doctorName = doctors.find((d) => d.id === doctorId)?.name

  function message(err: unknown): string {
    const { code, status } = identityError(err)
    switch (code) {
      case 'slot_taken': return t('errors.slotTaken')
      case 'date_in_past': return t('errors.dateInPast')
      case 'doctor_not_found': return t('errors.doctorNotFound')
      case 'plan_limit_reached': return t('errors.planLimit')
    }
    if (status === 404) return t('errors.notFound')
    return t('errors.generic')
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setLimitReached(false)
    if (!date || !time) return setError(t('errors.required'))
    if (date < today) return setError(t('errors.dateInPast'))
    setError(null)
    try {
      await confirm.mutateAsync({
        id: request.id,
        data: {
          appointment_date: date,
          appointment_time: time,
          duration_minutes: duration,
          doctor_id: doctorId || null,
          notify_sms: notify,
        },
      })
      toast.success(t('done'))
      onClose()
    } catch (err) {
      const { code } = identityError(err)
      if (code === 'not_open') {
        toast.error(t('errors.notOpen'))
        refresh()
        return onClose()
      }
      setLimitReached(code === 'plan_limit_reached')
      setError(message(err))
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{t('title')}</DialogTitle>
        <DialogDescription>{t('description', { name: request.requester.display_name })}</DialogDescription>
      </DialogHeader>
      <form onSubmit={submit} noValidate className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="cf-date">{t('date')}</Label>
            <Input id="cf-date" type="date" min={today} value={date} onChange={(e) => setDate(e.target.value)} disabled={confirm.isLoading} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cf-time">{t('time')}</Label>
            <Input id="cf-time" type="time" step={300} value={time} onChange={(e) => setTime(e.target.value)} disabled={confirm.isLoading} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cf-duration">{t('duration')}</Label>
            <select id="cf-duration" className={selectClass} value={duration} onChange={(e) => setDuration(Number(e.target.value))} disabled={confirm.isLoading}>
              {DURATIONS.map((d) => <option key={d} value={d}>{t('minutes', { count: d })}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cf-doctor">{t('doctor')}</Label>
            {doctors.length > 0 ? (
              <select id="cf-doctor" className={selectClass} value={doctorId} onChange={(e) => setDoctorId(e.target.value)} disabled={confirm.isLoading}>
                {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            ) : (
              <p className="text-sm text-muted-foreground">{t('noDoctorKnown')}</p>
            )}
          </div>
        </div>

        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1" checked={notify} onChange={(e) => setNotify(e.target.checked)} disabled={confirm.isLoading} />
          <span>
            {t('notify')}
            <span className="block text-muted-foreground">{t('notifyNote')}</span>
          </span>
        </label>

        {date && time && (
          <p className="rounded-md bg-muted p-3 text-sm" role="status">
            {t('summary', {
              name: request.requester.display_name,
              date: fmt(localDate(date), 'EEE, MMM d, yyyy'),
              time: fmt(localDate(date, time), 'h:mm a'),
              duration,
              doctor: doctorName ?? '-',
            })}
          </p>
        )}
        <p className="text-sm text-muted-foreground">
          {request.existing_patient_id ? t('existingRecord') : t('newRecord')}
        </p>

        {error && (
          <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
            {error}{' '}
            {limitReached && <Link href="/billing" className="font-medium underline">{t('seePlans')}</Link>}
          </p>
        )}

        <DialogFooter className="gap-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={confirm.isLoading}>{t('back')}</Button>
          <Button type="submit" disabled={confirm.isLoading}>
            {confirm.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('submit')}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
