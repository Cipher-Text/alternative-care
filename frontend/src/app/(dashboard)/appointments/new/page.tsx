'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateAppointment } from '@/lib/hooks/useAppointments'

export default function NewAppointmentPage() {
  const router = useRouter()
  const createAppointment = useCreateAppointment()

  const [formData, setFormData] = useState({
    patient_id: '',
    doctor_id: '',
    appointment_date: '',
    appointment_time: '',
    duration_minutes: 30,
    reason: '',
    notes: '',
  })

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    await createAppointment.mutateAsync({
      ...formData,
      reason: formData.reason || undefined,
      notes: formData.notes || undefined,
    })
    router.push('/appointments')
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/appointments">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">New Appointment</h1>
          <p className="text-muted-foreground">Schedule a new appointment</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 border rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="patient_id">Patient ID</Label>
            <Input
              id="patient_id"
              value={formData.patient_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, patient_id: e.target.value }))}
              placeholder="Patient UUID"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="doctor_id">Doctor ID</Label>
            <Input
              id="doctor_id"
              value={formData.doctor_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, doctor_id: e.target.value }))}
              placeholder="Doctor UUID"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="appointment_date">Date</Label>
            <Input
              id="appointment_date"
              type="date"
              value={formData.appointment_date}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, appointment_date: e.target.value }))
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
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, appointment_time: e.target.value }))
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
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  duration_minutes: Number(e.target.value || 30),
                }))
              }
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reason">Reason</Label>
          <Input
            id="reason"
            value={formData.reason}
            onChange={(e) => setFormData((prev) => ({ ...prev, reason: e.target.value }))}
            placeholder="Consultation reason"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Input
            id="notes"
            value={formData.notes}
            onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
            placeholder="Optional notes"
          />
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={createAppointment.isLoading}>
            {createAppointment.isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Creating...
              </>
            ) : (
              'Create Appointment'
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
