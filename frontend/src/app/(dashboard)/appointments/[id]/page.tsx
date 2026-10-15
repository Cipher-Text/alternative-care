'use client'

import { use } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { ArrowLeft, Calendar, Clock, FileText, Loader2, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppointment } from '@/lib/hooks/useAppointments'
import { usePatients } from '@/lib/hooks/usePatients'
import { StartConsultationButton } from '@/components/health/StartConsultationButton'

export default function AppointmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations('apptDetailUi')
  const { id } = use(params)
  const { data: appointment, isLoading, error } = useAppointment(id)
  const { data: patients } = usePatients({ limit: 500 })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (error || !appointment) {
    return (
      <div className="text-center py-10">
        <p className="text-lg font-semibold">{t('notFound')}</p>
        <Link href="/appointments">
          <Button className="mt-4">{t('backToList')}</Button>
        </Link>
      </div>
    )
  }

  const patient = patients?.find((item) => item.id === appointment.patient_id)

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Link href="/appointments">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              {t('back')}
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">{t('title')}</h1>
            <p className="text-muted-foreground">{t('subtitle')}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {['scheduled', 'confirmed', 'in_progress'].includes(appointment.status) && (
            <StartConsultationButton appointmentId={appointment.id} patientId={appointment.patient_id} reason={appointment.reason} size="default" />
          )}
          <Link href={`/appointments/${appointment.id}/edit`}>
            <Button variant="outline">{t('edit')}</Button>
          </Link>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border rounded-lg p-6 space-y-4">
        <div className="flex items-start gap-3">
          <User className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">{t('patient')}</p>
            <p className="font-medium">{patient ? patient.full_name : appointment.patient_id}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">{t('date')}</p>
            <p className="font-medium">{appointment.appointment_date}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Clock className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">{t('timeDuration')}</p>
            <p className="font-medium">{appointment.appointment_time} ({appointment.duration_minutes} {t('minShort')})</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div>
            <p className="text-sm text-muted-foreground">{t('status')}</p>
            <p className="font-medium">{t(`statusLabels.${appointment.status}`)}</p>
          </div>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">{t('reason')}</p>
          <p className="font-medium">{appointment.reason || '-'}</p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">{t('notes')}</p>
          <p className="font-medium">{appointment.notes || '-'}</p>
        </div>
      </div>
    </div>
  )
}
