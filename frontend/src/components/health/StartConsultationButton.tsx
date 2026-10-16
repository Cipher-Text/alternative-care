'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { Loader2, Play } from 'lucide-react'
import { useQueryClient } from 'react-query'
import { Button } from '@/components/ui/button'
import { healthApi } from '@/lib/api/health'
import { rawDetail, errorMessage } from '@/lib/apiErrors'
import { useCan } from '@/lib/auth/permissions'
import { useAuthStore } from '@/store/authStore'
import { localToday } from './localDate'

/**
 * "Start consultation" on an appointment: opens the visit started from it, or starts one (linked to the appointment, which
 * becomes "in progress") and goes to the patient's visits. Only people who may write visits see it.
 */
export function StartConsultationButton({
  appointmentId,
  patientId,
  reason,
  size = 'sm',
  variant = 'default',
}: {
  appointmentId: string
  patientId: string
  /** The appointment's reason: becomes the visit's first complaint */
  reason?: string | null
  size?: 'sm' | 'default'
  variant?: 'default' | 'outline'
}) {
  const t = useTranslations('healthUi.visits')
  const router = useRouter()
  const queryClient = useQueryClient()
  const { can } = useCan()
  const doctorId = useAuthStore((state) => state.user?.id)
  const [busy, setBusy] = useState(false)

  if (!can('visits.write') || !doctorId) return null

  const open = (visitId: string) => router.push(`/consultations/${visitId}`)

  const start = async () => {
    setBusy(true)
    try {
      const existing = await healthApi.visitForAppointment(appointmentId)
      if (existing) return open(existing.id)
      const visit = await healthApi.createVisit({
        patient_id: patientId,
        doctor_id: doctorId,
        visit_date: localToday(),
        visit_type: 'consultation',
        appointment_id: appointmentId,
        chief_complaint: reason?.trim() || undefined,
      } as Parameters<typeof healthApi.createVisit>[0])
      queryClient.invalidateQueries('appointments')
      queryClient.invalidateQueries(['dashboard'])
      open(visit.id)
    } catch (error) {
      const detail = rawDetail(error) as { code?: string; visit_id?: string } | undefined
      // Someone else started it a moment ago: open that one
      if (detail && typeof detail === 'object' && detail.code === 'visit_exists' && detail.visit_id) return open(detail.visit_id)
      toast.error(errorMessage(error, t('startFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Button type="button" size={size} variant={variant} onClick={start} disabled={busy}>
      {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <Play className="mr-2 h-4 w-4" aria-hidden="true" />}
      {t('start')}
    </Button>
  )
}
