'use client'

import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Pager, clientPage, usePager } from '@/components/shared/Pager'
import { useRouter } from 'next/navigation'
import { Calendar as CalendarIcon, Loader2, PlusCircle } from 'lucide-react'
import { Calendar, dateFnsLocalizer, type View } from 'react-big-calendar'
import {
  format,
  parse,
  startOfWeek,
  getDay,
  parseISO,
  setHours,
  setMinutes,
} from 'date-fns'
import { bn, enUS } from 'date-fns/locale'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAppointments } from '@/lib/hooks/useAppointments'
import { useAppointmentRequests } from '@/lib/hooks/useAppointmentRequests'
import { usePatients } from '@/lib/hooks/usePatients'
import type { Appointment, AppointmentStatus } from '@/types/appointment'

const locales = {
  'en-US': enUS,
  bn,
}

const STATUS_VALUES: Array<AppointmentStatus | 'all'> = [
  'all',
  'scheduled',
  'confirmed',
  'in_progress',
  'completed',
  'cancelled',
  'no_show',
]

type AppointmentEvent = {
  id: string
  title: string
  start: Date
  end: Date
  resource: Appointment
}

function toDateTime(dateText: string, timeText: string): Date {
  const date = parseISO(dateText)
  const [hours, minutes] = timeText.split(':').map(Number)
  return setMinutes(setHours(date, hours || 0), minutes || 0)
}

export default function AppointmentsPage() {
  const tp = useTranslations('pages')
  const t = useTranslations('apptUi')
  const tr = useTranslations('appointmentRequestsUi')
  const waiting = useAppointmentRequests({ status: 'requested', limit: 51 }).data?.length ?? 0
  const locale = useLocale()
  const culture = locale === 'bn' ? 'bn' : 'en-US'
  const localizer = useMemo(
    () => dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales }),
    []
  )
  const calendarMessages = useMemo(
    () => ({
      allDay: t('cal.allDay'),
      previous: t('cal.previous'),
      next: t('cal.next'),
      today: t('cal.today'),
      month: t('cal.month'),
      week: t('cal.week'),
      day: t('cal.day'),
      agenda: t('cal.agenda'),
      date: t('cal.date'),
      time: t('cal.time'),
      event: t('cal.event'),
      noEventsInRange: t('cal.noEventsInRange'),
      showMore: (total: number) => t('cal.showMore', { count: total }),
    }),
    [t]
  )
  const router = useRouter()
  // The calendar needs every appointment in view, so load up to the API maximum and page the
  // list view in the browser (the calendar itself is not paged).
  const [limit] = useState(500)
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | 'all'>('all')
  const [patientQuery, setPatientQuery] = useState('')
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('calendar')
  const [calendarView, setCalendarView] = useState<View>('month')

  const { data: appointments, isLoading, error } = useAppointments({ limit })
  const { data: patients, isLoading: isLoadingPatients } = usePatients({ limit: 500 })

  const patientById = useMemo(() => {
    const map = new Map<string, { name: string }>()
    for (const patient of patients || []) {
      map.set(patient.id, { name: patient.full_name })
    }
    return map
  }, [patients])

  const filteredAppointments = useMemo(() => {
    if (!appointments) return []

    return appointments.filter((appointment) => {
      if (statusFilter !== 'all' && appointment.status !== statusFilter) {
        return false
      }

      if (!patientQuery.trim()) {
        return true
      }

      const lookup = patientById.get(appointment.patient_id)
      if (!lookup) return false

      const query = patientQuery.toLowerCase()
      return (
        lookup.name.toLowerCase().includes(query)
      )
    })
  }, [appointments, patientById, patientQuery, statusFilter])

  const pager = usePager(undefined, [statusFilter, patientQuery])
  const listPage = clientPage(filteredAppointments, pager.page, pager.pageSize)

  const events = useMemo<AppointmentEvent[]>(() => {
    return filteredAppointments.map((appointment) => {
      const patient = patientById.get(appointment.patient_id)
      const start = toDateTime(appointment.appointment_date, appointment.appointment_time)
      const end = new Date(start.getTime() + appointment.duration_minutes * 60 * 1000)

      return {
        id: appointment.id,
        title: patient ? patient.name : appointment.patient_id,
        start,
        end,
        resource: appointment,
      }
    })
  }, [filteredAppointments, patientById])

  if (isLoading || isLoadingPatients) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 py-8">
        <p className="text-lg font-semibold">{t('loadFailedTitle')}</p>
        <p className="text-sm">{t('loadFailedHint')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-3xl font-bold">{tp('appointmentsTitle')}</h1>
          <p className="text-muted-foreground">{tp('appointmentsSubtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
        {waiting > 0 && (
          <Link href="/appointment-requests" className="text-sm font-medium text-primary underline">
            {waiting > 50 ? tr('waitingMany') : tr('waiting', { count: waiting })}
          </Link>
        )}
        <Link href="/appointments/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            {tp('newAppointment')}
          </Button>
        </Link>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="patient-filter">
            {t('searchPatient')}
          </label>
          <Input
            id="patient-filter"
            placeholder={t('searchPlaceholder')}
            value={patientQuery}
            onChange={(event) => setPatientQuery(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="status-filter">
            {t('status')}
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as AppointmentStatus | 'all')}
            className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {STATUS_VALUES.map((value) => (
              <option key={value} value={value}>
                {t(`statusOptions.${value}`)}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t('view')}</label>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant={viewMode === 'calendar' ? 'default' : 'outline'}
              onClick={() => setViewMode('calendar')}
            >
              {t('calendar')}
            </Button>
            <Button
              type="button"
              variant={viewMode === 'list' ? 'default' : 'outline'}
              onClick={() => setViewMode('list')}
            >
              {t('list')}
            </Button>
          </div>
        </div>
      </div>

      {viewMode === 'calendar' ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <Calendar
            localizer={localizer}
            culture={culture}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 700 }}
            view={calendarView}
            onView={(nextView) => setCalendarView(nextView)}
            views={['month', 'week', 'day']}
            selectable
            popup
            onSelectEvent={(event) => router.push(`/appointments/${event.resource.id}`)}
            onSelectSlot={(slotInfo) => {
              const dateParam = format(slotInfo.start, 'yyyy-MM-dd')
              const timeParam = format(slotInfo.start, 'HH:mm')
              router.push(`/appointments/new?date=${dateParam}&time=${timeParam}`)
            }}
            messages={calendarMessages}
          />
        </div>
      ) : filteredAppointments.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/40">
              <tr>
                <th className="text-left px-4 py-3">{t('cols.date')}</th>
                <th className="text-left px-4 py-3">{t('cols.time')}</th>
                <th className="text-left px-4 py-3">{t('cols.patient')}</th>
                <th className="text-left px-4 py-3">{t('cols.doctor')}</th>
                <th className="text-left px-4 py-3">{t('cols.status')}</th>
                <th className="text-left px-4 py-3">{t('cols.reason')}</th>
              </tr>
            </thead>
            <tbody>
              {listPage.items.map((appointment) => {
                const patient = patientById.get(appointment.patient_id)
                return (
                  <tr key={appointment.id} className="border-t">
                    <td className="px-4 py-3">{appointment.appointment_date}</td>
                    <td className="px-4 py-3">{appointment.appointment_time}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{patient?.name || t('unknownPatient')}</div>
                      <div className="text-xs text-muted-foreground">
                        {appointment.patient_id}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{appointment.doctor_id}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block rounded-md bg-emerald-50 text-emerald-700 px-2 py-1 text-xs">
                        {t(`statusOptions.${appointment.status}`)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div>{appointment.reason || '-'}</div>
                      <Link
                        href={`/appointments/${appointment.id}`}
                        className="text-xs text-emerald-600 hover:underline"
                      >
                        {t('viewDetails')}
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="px-4 pb-4">
            <Pager
              page={pager.page}
              pageSize={pager.pageSize}
              count={listPage.items.length}
              hasNext={listPage.hasNext}
              total={listPage.total}
              onPageChange={pager.setPage}
              noun="appointments"
            />
          </div>
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
          <CalendarIcon className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
          <p className="text-muted-foreground">{t('empty')}</p>
          <Link href="/appointments/new">
            <Button className="mt-4">
              <PlusCircle className="mr-2 h-4 w-4" />
              {t('create')}
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}
