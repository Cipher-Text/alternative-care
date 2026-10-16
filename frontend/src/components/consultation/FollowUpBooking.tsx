'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { CalendarCheck, CalendarPlus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { appointmentsApi } from '@/lib/api/appointments'
import { errorMessage } from '@/lib/apiErrors'
import { useCan } from '@/lib/auth/permissions'
import { useAppointments } from '@/lib/hooks/useAppointments'
import { useAuthStore } from '@/store/authStore'
import { canBookFollowUp } from './visitDraft'

const OPEN = ['scheduled', 'confirmed', 'in_progress']

/**
 * The next appointment, booked from the consultation: the follow-up date the doctor set becomes an appointment with one click
 * (a time, and the diary's own clash check). Once an appointment exists on that date the patient also drops off the
 * dashboard's "follow-ups due" list.
 */
export function FollowUpBooking({
  patientId,
  visitDate,
  followUpDate,
  notes,
}: {
  patientId: string
  visitDate: string
  followUpDate: string | undefined
  notes: string | undefined
}) {
  const t = useTranslations('consultationUi.followUp')
  const locale = useLocale()
  const queryClient = useQueryClient()
  const { can } = useCan()
  const doctorId = useAuthStore((state) => state.user?.id)
  const [time, setTime] = useState('10:00')
  const [busy, setBusy] = useState(false)
  const { data: appointments } = useAppointments({ patient_id: patientId, limit: 50 })

  const valid = canBookFollowUp(followUpDate, visitDate)
  const booked = valid ? appointments?.find((a) => a.appointment_date === followUpDate && OPEN.includes(a.status)) : undefined
  const day = (iso: string) => new Intl.DateTimeFormat(locale, { dateStyle: 'full' }).format(new Date(`${iso}T00:00:00`))

  const book = async () => {
    if (!doctorId || !followUpDate) return
    setBusy(true)
    try {
      await appointmentsApi.create({
        patient_id: patientId,
        doctor_id: doctorId,
        appointment_date: followUpDate,
        appointment_time: `${time}:00`,
        duration_minutes: 30,
        reason: notes?.trim() ? `${t('reasonPrefix')}: ${notes.trim()}` : t('reasonPrefix'),
      })
      queryClient.invalidateQueries('appointments')
      queryClient.invalidateQueries(['dashboard'])
      toast.success(t('booked'))
    } catch (error) {
      // The diary refuses a time that clashes with another appointment; its message says which
      toast.error(errorMessage(error, t('failed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <CalendarPlus className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {!followUpDate && <p className="text-sm text-muted-foreground">{t('setDate')}</p>}
        {followUpDate && !valid && <p className="text-sm text-amber-600">{t('badDate')}</p>}
        {valid && booked && (
          <p className="flex flex-wrap items-center gap-2 text-sm">
            <CalendarCheck className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            {t('alreadyBooked', { date: day(booked.appointment_date), time: booked.appointment_time.slice(0, 5) })}
            <Link href={`/appointments/${booked.id}`} className="underline">{t('open')}</Link>
          </p>
        )}
        {valid && !booked && can('appointments.write') && (
          <div className="flex flex-wrap items-end gap-3">
            <p className="w-full text-sm">{t('forDate', { date: day(followUpDate as string) })}</p>
            <div className="space-y-1.5">
              <Label htmlFor="fu-time">{t('time')}</Label>
              <Input id="fu-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} className="w-36" />
            </div>
            <Button type="button" onClick={book} disabled={busy || !time || !doctorId}>
              {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <CalendarPlus className="mr-2 h-4 w-4" aria-hidden="true" />}
              {t('book')}
            </Button>
          </div>
        )}
        {valid && !booked && !can('appointments.write') && <p className="text-sm text-muted-foreground">{t('notBooked', { date: day(followUpDate as string) })}</p>}
      </CardContent>
    </Card>
  )
}
