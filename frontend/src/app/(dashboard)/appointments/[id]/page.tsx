'use client'

import { use } from 'react'
import Link from 'next/link'
import { ArrowLeft, Calendar, Clock, FileText, Loader2, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppointment } from '@/lib/hooks/useAppointments'
import { usePatients } from '@/lib/hooks/usePatients'

export default function AppointmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: appointment, isLoading, error } = useAppointment(id)
  const { data: patients } = usePatients({ limit: 500 })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !appointment) {
    return (
      <div className="text-center py-10">
        <p className="text-lg font-semibold">Appointment not found</p>
        <Link href="/appointments">
          <Button className="mt-4">Back to Appointments</Button>
        </Link>
      </div>
    )
  }

  const patient = patients?.find((item) => item.id === appointment.patient_id)

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/appointments">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Appointment Details</h1>
            <p className="text-muted-foreground">Review appointment and update status</p>
          </div>
        </div>
        <Link href={`/appointments/${appointment.id}/edit`}>
          <Button>Edit Appointment</Button>
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 border rounded-lg p-6 space-y-4">
        <div className="flex items-start gap-3">
          <User className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">Patient</p>
            <p className="font-medium">{patient ? `${patient.first_name} ${patient.last_name}` : appointment.patient_id}</p>
            <p className="text-xs text-muted-foreground">{patient?.patient_code || 'Unknown code'}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">Date</p>
            <p className="font-medium">{appointment.appointment_date}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Clock className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">Time & Duration</p>
            <p className="font-medium">{appointment.appointment_time} ({appointment.duration_minutes} min)</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">Status</p>
            <p className="font-medium">{appointment.status}</p>
          </div>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Reason</p>
          <p className="font-medium">{appointment.reason || '-'}</p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Notes</p>
          <p className="font-medium">{appointment.notes || '-'}</p>
        </div>
      </div>
    </div>
  )
}
