'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
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
import { enUS } from 'date-fns/locale'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAppointments } from '@/lib/hooks/useAppointments'
import { usePatients } from '@/lib/hooks/usePatients'
import type { Appointment, AppointmentStatus } from '@/types/appointment'

const locales = {
  'en-US': enUS,
}

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
})

const STATUS_OPTIONS: Array<{ label: string; value: AppointmentStatus | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Confirmed', value: 'confirmed' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'No Show', value: 'no_show' },
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
  const router = useRouter()
  const [limit] = useState(100)
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
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-500 py-8">
        <p className="text-lg font-semibold">Failed to load appointments</p>
        <p className="text-sm">Please try again later</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Appointments</h1>
          <p className="text-muted-foreground">Manage upcoming and past appointments</p>
        </div>
        <Link href="/appointments/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Appointment
          </Button>
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 border rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="patient-filter">
            Search patient
          </label>
          <Input
            id="patient-filter"
            placeholder="Name or patient code"
            value={patientQuery}
            onChange={(event) => setPatientQuery(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="status-filter">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as AppointmentStatus | 'all')}
            className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">View</label>
          <div className="flex gap-2">
            <Button
              type="button"
              variant={viewMode === 'calendar' ? 'default' : 'outline'}
              onClick={() => setViewMode('calendar')}
            >
              Calendar
            </Button>
            <Button
              type="button"
              variant={viewMode === 'list' ? 'default' : 'outline'}
              onClick={() => setViewMode('list')}
            >
              List
            </Button>
          </div>
        </div>
      </div>

      {viewMode === 'calendar' ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <Calendar
            localizer={localizer}
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
            messages={{
              showMore: (total) => `+${total} more`,
            }}
          />
        </div>
      ) : filteredAppointments.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/40">
              <tr>
                <th className="text-left px-4 py-3">Date</th>
                <th className="text-left px-4 py-3">Time</th>
                <th className="text-left px-4 py-3">Patient</th>
                <th className="text-left px-4 py-3">Doctor</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Reason</th>
              </tr>
            </thead>
            <tbody>
              {filteredAppointments.map((appointment) => {
                const patient = patientById.get(appointment.patient_id)
                return (
                  <tr key={appointment.id} className="border-t">
                    <td className="px-4 py-3">{appointment.appointment_date}</td>
                    <td className="px-4 py-3">{appointment.appointment_time}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{patient?.name || 'Unknown patient'}</div>
                      <div className="text-xs text-muted-foreground">
                        {appointment.patient_id}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{appointment.doctor_id}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block rounded-md bg-indigo-50 text-indigo-700 px-2 py-1 text-xs">
                        {appointment.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div>{appointment.reason || '-'}</div>
                      <Link
                        href={`/appointments/${appointment.id}`}
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        View details
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
          <CalendarIcon className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
          <p className="text-muted-foreground">No appointments found.</p>
          <Link href="/appointments/new">
            <Button className="mt-4">
              <PlusCircle className="mr-2 h-4 w-4" />
              Create Appointment
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}
