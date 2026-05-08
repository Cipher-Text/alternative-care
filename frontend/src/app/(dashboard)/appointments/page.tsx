'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Calendar, Loader2, PlusCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppointments } from '@/lib/hooks/useAppointments'

export default function AppointmentsPage() {
  const [limit] = useState(50)
  const { data: appointments, isLoading, error } = useAppointments({ limit })

  if (isLoading) {
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

      {appointments && appointments.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/40">
              <tr>
                <th className="text-left px-4 py-3">Date</th>
                <th className="text-left px-4 py-3">Time</th>
                <th className="text-left px-4 py-3">Patient ID</th>
                <th className="text-left px-4 py-3">Doctor ID</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Reason</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((appointment) => (
                <tr key={appointment.id} className="border-t">
                  <td className="px-4 py-3">{appointment.appointment_date}</td>
                  <td className="px-4 py-3">{appointment.appointment_time}</td>
                  <td className="px-4 py-3 font-mono text-xs">{appointment.patient_id}</td>
                  <td className="px-4 py-3 font-mono text-xs">{appointment.doctor_id}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block rounded-md bg-indigo-50 text-indigo-700 px-2 py-1 text-xs">
                      {appointment.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{appointment.reason || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
          <Calendar className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
          <p className="text-muted-foreground">No appointments yet.</p>
          <Link href="/appointments/new">
            <Button className="mt-4">
              <PlusCircle className="mr-2 h-4 w-4" />
              Create First Appointment
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}
