'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAppointment, useUpdateAppointment } from '@/lib/hooks/useAppointments'
import type { AppointmentStatus } from '@/types/appointment'

const STATUS_OPTIONS: AppointmentStatus[] = [
  'scheduled',
  'confirmed',
  'in_progress',
  'completed',
  'cancelled',
  'no_show',
]

export default function EditAppointmentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { data: appointment, isLoading } = useAppointment(id)
  const updateAppointment = useUpdateAppointment()
  const [conflictMessage, setConflictMessage] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    appointment_date: '',
    appointment_time: '',
    duration_minutes: 30,
    status: 'scheduled' as AppointmentStatus,
    reason: '',
    notes: '',
  })

  useEffect(() => {
    if (!appointment) return
    setFormData({
      appointment_date: appointment.appointment_date,
      appointment_time: appointment.appointment_time,
      duration_minutes: appointment.duration_minutes,
      status: appointment.status,
      reason: appointment.reason || '',
      notes: appointment.notes || '',
    })
  }, [appointment])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setConflictMessage(null)

    try {
      await updateAppointment.mutateAsync({
        id,
        data: {
          appointment_date: formData.appointment_date,
          appointment_time: formData.appointment_time,
          duration_minutes: formData.duration_minutes,
          status: formData.status,
          reason: formData.reason || undefined,
          notes: formData.notes || undefined,
        },
      })
      router.push(`/appointments/${id}`)
    } catch (error: any) {
      if (error?.response?.status === 409) {
        setConflictMessage(
          error?.response?.data?.detail ||
            'Selected doctor time slot is already booked. Please choose another time.'
        )
      }
    }
  }

  const applyStatus = (status: AppointmentStatus) => {
    setFormData((prev) => ({ ...prev, status }))
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (!appointment) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Appointment not found</p>
        <Link href="/appointments">
          <Button className="mt-4">Back to Appointments</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/appointments/${id}`}>
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Edit Appointment</h1>
          <p className="text-muted-foreground">Update schedule, status, and notes</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 border rounded-lg p-6 space-y-4">
        {conflictMessage ? (
          <div className="rounded-md border border-red-200 bg-red-50 text-red-700 px-3 py-2 text-sm">
            {conflictMessage}
          </div>
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="appointment_date">Date</Label>
            <Input
              id="appointment_date"
              type="date"
              value={formData.appointment_date}
              onChange={(event) =>
                setFormData((prev) => ({ ...prev, appointment_date: event.target.value }))
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="appointment_time">Time</Label>
            <Input
              id="appointment_time"
              type="time"
              value={formData.appointment_time}
              onChange={(event) =>
                setFormData((prev) => ({ ...prev, appointment_time: event.target.value }))
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="duration_minutes">Duration (minutes)</Label>
            <Input
              id="duration_minutes"
              type="number"
              min={15}
              max={240}
              value={formData.duration_minutes}
              onChange={(event) =>
                setFormData((prev) => ({
                  ...prev,
                  duration_minutes: Number(event.target.value || 30),
                }))
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={formData.status}
              onChange={(event) =>
                setFormData((prev) => ({ ...prev, status: event.target.value as AppointmentStatus }))
              }
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => applyStatus('confirmed')}>
            Mark Confirmed
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => applyStatus('in_progress')}>
            Mark In Progress
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => applyStatus('completed')}>
            Mark Completed
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => applyStatus('cancelled')}>
            Mark Cancelled
          </Button>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reason">Reason</Label>
          <Input
            id="reason"
            value={formData.reason}
            onChange={(event) => setFormData((prev) => ({ ...prev, reason: event.target.value }))}
            placeholder="Consultation reason"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Input
            id="notes"
            value={formData.notes}
            onChange={(event) => setFormData((prev) => ({ ...prev, notes: event.target.value }))}
            placeholder="Optional notes"
          />
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={updateAppointment.isLoading}>
            {updateAppointment.isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
