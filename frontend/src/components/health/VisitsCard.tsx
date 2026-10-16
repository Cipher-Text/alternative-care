'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useLocale, useTranslations } from 'next-intl'
import { parseISO } from 'date-fns'
import { Loader2, Plus, Stethoscope } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'
import { healthApi } from '@/lib/api/health'
import { errorMessage } from '@/lib/apiErrors'
import { useVisits } from '@/lib/hooks/useHealth'
import { useCan } from '@/lib/auth/permissions'
import { usePrescriptions } from '@/lib/hooks/usePrescriptions'
import type { PrescriptionListItem } from '@/types/prescription'
import { useCaseSystems } from '@/lib/hooks/useCaseTaking'
import { VisitCaseDetails } from '@/components/case-taking/VisitCaseDetails'
import { bmiOf } from '@/components/consultation/visitDraft'
import type { VisitListItem } from '@/types/health'
import { useCodeLabel } from './useCodeLabel'
import { localToday } from './localDate'

/** The patient's visits, newest first. Each opens on the consultation screen, where a visit is filled in and a prescription written. */
export function VisitsCard({ patientId, canEdit }: { patientId: string; canEdit: boolean }) {
  const t = useTranslations('healthUi.visits')
  const { data: visits, isLoading } = useVisits(patientId)
  const router = useRouter()
  const userId = useAuthStore((state) => state.user?.id)
  const [starting, setStarting] = useState(false)
  const systems = useCaseSystems()
  const { can } = useCan()
  // One request for all the patient's prescriptions; each visit shows the ones written for it
  const { data: prescriptions } = usePrescriptions(can('prescriptions.read') ? { patient_id: patientId, limit: 100 } : undefined)
  // A patient who walks in with no appointment: a blank visit for today, opened on the consultation screen
  const startWalkIn = async () => {
    if (!userId) return
    setStarting(true)
    try {
      const visit = await healthApi.createVisit({ patient_id: patientId, doctor_id: userId, visit_date: localToday(), visit_type: 'consultation' })
      router.push(`/consultations/${visit.id}`)
    } catch (error) {
      toast.error(errorMessage(error, t('startFailed')))
      setStarting(false)
    }
  }
  const byVisit = (visitId: string) => (can('prescriptions.read') ? (prescriptions ?? []).filter((p) => p.visit_id === visitId) : [])

  return (
    <Card id="visits">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              {t('title')}
            </CardTitle>
            <CardDescription>{t('description')}</CardDescription>
          </div>
          {canEdit && (
            <Button type="button" disabled={starting || !userId} onClick={startWalkIn}>
              {starting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <Plus className="mr-2 h-4 w-4" aria-hidden="true" />}
              {t('add')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && <Loader2 className="h-5 w-5 animate-spin text-emerald-600" aria-hidden="true" />}
        {visits && visits.length === 0 && <p className="text-sm text-muted-foreground">{t('empty')}</p>}
        {visits?.map((v) => <VisitRow key={v.id} visit={v} systems={systems} canEdit={canEdit} prescriptions={byVisit(v.id)} />)}
        {!canEdit && <Badge variant="outline">{t('readOnly')}</Badge>}
      </CardContent>
    </Card>
  )
}

function VisitRow({ visit, systems, canEdit, prescriptions }: { visit: VisitListItem; systems: readonly string[]; canEdit: boolean; prescriptions: PrescriptionListItem[] }) {
  const t = useTranslations('healthUi.visits')
  const locale = useLocale()
  const typeLabel = useCodeLabel('visitType')
  const flagLabel = useCodeLabel('redFlag')
  const referralLabel = useCodeLabel('referral')
  const bmi = bmiOf(visit.weight_kg, visit.height_cm)
  const vitals = [
    visit.temperature_c != null && `${t('short.temperature')} ${visit.temperature_c}°C`,
    visit.pulse_bpm != null && `${t('short.pulse')} ${visit.pulse_bpm}`,
    visit.bp_systolic != null && visit.bp_diastolic != null && `${t('short.bp')} ${visit.bp_systolic}/${visit.bp_diastolic}`,
    visit.respiratory_rate != null && `${t('short.respiratoryRate')} ${visit.respiratory_rate}`,
    visit.spo2_percent != null && `${t('short.spo2')} ${visit.spo2_percent}%`,
    visit.weight_kg != null && `${t('short.weight')} ${visit.weight_kg} kg`,
    visit.height_cm != null && `${t('short.height')} ${visit.height_cm} cm`,
    bmi != null && `${t('short.bmi')} ${bmi}`,
    visit.blood_sugar_mmol != null && `${t('short.sugar')} ${visit.blood_sugar_mmol} mmol/L`,
    visit.pain_score != null && `${t('short.pain')} ${visit.pain_score}/10`,
  ].filter(Boolean) as string[]

  return (
    <div id={`visit-${visit.id}`} className="space-y-2 rounded-md border p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">
          {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(parseISO(visit.visit_date))}
        </span>
        <Badge variant="outline">{typeLabel(visit.visit_type)}</Badge>
        <Badge variant={visit.status === 'completed' ? 'secondary' : 'default'}>{visit.status === 'completed' ? t('completed') : t('inProgress')}</Badge>
        {visit.referral_urgency && visit.referral_urgency !== 'none' && (
          <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">{referralLabel(visit.referral_urgency)}</Badge>
        )}
      </div>
      {visit.chief_complaint && <p className="text-sm">{visit.chief_complaint}</p>}
      {visit.provisional_diagnosis && <p className="text-sm text-muted-foreground">{visit.provisional_diagnosis}</p>}
      {vitals.length > 0 && (
        <p className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
          {vitals.map((v) => <span key={v}>{v}</span>)}
        </p>
      )}
      {visit.red_flags && visit.red_flags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {visit.red_flags.map((f) => (
            <Badge key={f} className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">{flagLabel(f)}</Badge>
          ))}
        </div>
      )}
      {systems.map((system) => (
        <VisitCaseDetails key={system} visitId={visit.id} system={system} canEdit={false} />
      ))}
      {prescriptions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-t pt-2 text-sm">
          <span className="text-muted-foreground">{t('prescriptions')}</span>
          {prescriptions.map((p) => (
            <Link key={p.id} href={`/prescriptions/${p.id}`} className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs hover:bg-accent">
              {t(`rxStatus.${p.status}`)} · {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(p.created_at))}
            </Link>
          ))}
        </div>
      )}
      <div className="pt-2">
        <Button asChild size="sm" variant={visit.status === 'completed' ? 'outline' : 'default'}>
          <Link href={`/consultations/${visit.id}`}>{canEdit ? (visit.status === 'completed' ? t('openConsultation') : t('continueConsultation')) : t('viewConsultation')}</Link>
        </Button>
      </div>
    </div>
  )
}
