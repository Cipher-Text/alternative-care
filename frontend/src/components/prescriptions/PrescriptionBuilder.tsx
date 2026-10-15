'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useCreatePrescription, useUpdatePrescription } from '@/lib/hooks/usePrescriptions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { SafetyBanner } from '@/components/health/SafetyBanner'
import { PatientSelector } from './PatientSelector'
import { VisitPicker } from './VisitPicker'
import { useVisits } from '@/lib/hooks/useHealth'
import { CASE_SYSTEMS, useCaseSystems, useVisitCase, type CaseSystem } from '@/lib/hooks/useCaseTaking'
import { medicineRowsFromCase } from '@/lib/prescriptions/medicineRowsFromCase'
import type { VisitListItem } from '@/types/health'
import { MedicineItemsBuilder, blankMedicineRow, isRowComplete, isRowStarted } from './MedicineItemsBuilder'
import type { Prescription, PrescriptionItemCreate } from '@/types/prescription'
import { Save, CheckCircle, Loader2 } from 'lucide-react'
import { useCan } from '@/lib/auth/permissions'

interface PrescriptionBuilderProps {
  prescription?: Prescription
  isEdit?: boolean
}

export function PrescriptionBuilder({ prescription, isEdit = false }: PrescriptionBuilderProps) {
  const router = useRouter()
  const { can } = useCan()
  const t = useTranslations('rxBuilderUi')
  const createPrescription = useCreatePrescription()
  const updatePrescription = useUpdatePrescription()

  // Form state
  // Coming from a patient or a visit ("Write prescription"): /prescriptions/new?patient=..&visit=..
  const params = useSearchParams()
  const fromVisit = isEdit ? '' : params.get('visit') || ''
  const [patientId, setPatientId] = useState<string>(prescription?.patient_id || (isEdit ? '' : params.get('patient') || ''))
  const [visitId, setVisitId] = useState<string>(prescription?.visit_id || fromVisit)
  const [diagnosis, setDiagnosis] = useState<string>(prescription?.diagnosis || '')
  const [doctorsNotes, setDoctorsNotes] = useState<string>(prescription?.doctors_notes || '')
  const [advice, setAdvice] = useState<string>(prescription?.advice || '')

  // Choosing a visit fills the diagnosis and advice from it, only into boxes that are still empty
  const prefillFrom = (visit?: VisitListItem) => {
    if (!visit) return
    if (!diagnosis.trim() && visit.provisional_diagnosis) setDiagnosis(visit.provisional_diagnosis)
    if (!advice.trim() && visit.treatment_plan) setAdvice(visit.treatment_plan)
  }
  const { data: patientVisits } = useVisits(patientId || undefined)
  const [prefilledFromUrl, setPrefilledFromUrl] = useState(false)
  if (fromVisit && !prefilledFromUrl && patientVisits) {
    setPrefilledFromUrl(true)
    prefillFrom(patientVisits.find((v) => v.id === fromVisit))
  }

  const [items, setItems] = useState<PrescriptionItemCreate[]>(
    prescription?.items.map((item) => ({
      medicine_id: item.medicine_id,
      medicine_name: item.medicine_name,
      dosage: item.dosage,
      frequency: item.frequency,
      duration: item.duration,
      quantity: item.quantity,
      instructions: item.instructions,
      display_order: item.display_order,
    })) || [blankMedicineRow()]
  )

  // The medicines named in the visit's case details (homeopathy, Ayurveda, Unani) become the first rows
  const clinicSystems = useCaseSystems()
  const th = useTranslations('caseTakingUi.homeopathy')
  const ta = useTranslations('caseTakingUi.ayurveda')
  const tu = useTranslations('caseTakingUi.unani')
  const caseLabels: Record<CaseSystem, typeof th> = { homeopathy: th, ayurveda: ta, unani: tu }
  const homeoCase = useVisitCase(fromVisit, 'homeopathy', Boolean(fromVisit) && clinicSystems.includes('homeopathy'))
  const ayurvedaCase = useVisitCase(fromVisit, 'ayurveda', Boolean(fromVisit) && clinicSystems.includes('ayurveda'))
  const unaniCase = useVisitCase(fromVisit, 'unani', Boolean(fromVisit) && clinicSystems.includes('unani'))
  const caseQueries = { homeopathy: homeoCase, ayurveda: ayurvedaCase, unani: unaniCase }
  const caseSettled = CASE_SYSTEMS.every((s) => !clinicSystems.includes(s) || !caseQueries[s].isLoading)
  const [rowsFromCase, setRowsFromCase] = useState(0)
  // Rows replaced from outside the row editor start the editor afresh, so each medicine box shows its row's text
  const [rowsVersion, setRowsVersion] = useState(0)
  const [rowsPrefilled, setRowsPrefilled] = useState(false)
  if (fromVisit && !isEdit && !rowsPrefilled && clinicSystems.length > 0 && caseSettled) {
    setRowsPrefilled(true)
    const rows = CASE_SYSTEMS.flatMap((s) => {
      const data = caseQueries[s].data?.data
      const t = caseLabels[s]
      return data
        ? medicineRowsFromCase(s, data, (key, code) => (code ? t(`fields.${key}.options.${code}`) : t(`fields.${key}.label`)))
        : []
    }).map((r, i) => ({ ...r, display_order: i }))
    // Only into a form that is still untouched
    if (rows.length > 0 && items.length === 1 && !isRowStarted(items[0])) {
      setItems(rows)
      setRowsFromCase(rows.length)
      setRowsVersion((v) => v + 1)
    }
  }

  // Rows are typed in place. Untouched blank rows are left out; a row that was started but not finished blocks saving
  const finishedItems = items.filter(isRowComplete)
  const hasUnfinishedRow = items.some((item) => isRowStarted(item) && !isRowComplete(item))

  // Validation
  const isValid = Boolean(patientId) && finishedItems.length > 0 && !hasUnfinishedRow

  const handleSaveDraft = async () => {
    if (!patientId || hasUnfinishedRow) return

    const data = {
      patient_id: patientId,
      visit_id: visitId || null,
      diagnosis: diagnosis || null,
      doctors_notes: doctorsNotes || null,
      advice: advice || null,
      items: finishedItems,
      status: 'draft' as const,
    }

    if (isEdit && prescription) {
      // Update existing draft
      await updatePrescription.mutateAsync({
        id: prescription.id,
        data: {
          diagnosis: diagnosis || null,
          doctors_notes: doctorsNotes || null,
          advice: advice || null,
          items: finishedItems,
        },
      })
      router.push(`/prescriptions/${prescription.id}`)
    } else {
      // Create new draft
      const result = await createPrescription.mutateAsync(data)
      router.push(`/prescriptions/${result.id}`)
    }
  }

  const handleIssue = async () => {
    if (!isValid) return

    const data = {
      patient_id: patientId,
      visit_id: visitId || null,
      diagnosis: diagnosis || null,
      doctors_notes: doctorsNotes || null,
      advice: advice || null,
      items: finishedItems,
      status: 'issued' as const,
    }

    if (isEdit && prescription) {
      // Update and issue
      await updatePrescription.mutateAsync({
        id: prescription.id,
        data: {
          diagnosis: diagnosis || null,
          doctors_notes: doctorsNotes || null,
          advice: advice || null,
          items: finishedItems,
          status: 'issued',
        },
      })
      router.push(`/prescriptions/${prescription.id}`)
    } else {
      // Create and issue
      const result = await createPrescription.mutateAsync(data)
      router.push(`/prescriptions/${result.id}`)
    }
  }

  const isLoading = createPrescription.isLoading || updatePrescription.isLoading

  return (
    <div className="space-y-6">
      {/* Patient & Visit Information */}
      <Card>
        <CardHeader>
          <CardTitle>{t('patientInfo')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="patient">
              {t('patient')} <span className="text-red-500">*</span>
            </Label>
            <PatientSelector
              value={patientId}
              onChange={(id) => {
                setPatientId(id)
                setVisitId('') // a visit belongs to one patient
              }}
              disabled={isEdit}
            />
            {isEdit && (
              <p className="text-xs text-muted-foreground">
                {t('patientLocked')}
              </p>
            )}
          </div>

          {patientId && <SafetyBanner patientId={patientId} linkToPatient />}

          <div className="space-y-2">
            <Label htmlFor="visit_id">{t('visitId')}</Label>
            <VisitPicker
              patientId={patientId}
              value={visitId}
              disabled={isEdit}
              onChange={(id, visit) => {
                setVisitId(id)
                prefillFrom(visit)
              }}
            />
            <p className="text-xs text-muted-foreground">{t('visitHint')}</p>
          </div>
        </CardContent>
      </Card>

      {/* Clinical Information */}
      <Card>
        <CardHeader>
          <CardTitle>{t('clinicalInfo')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="diagnosis">{t('diagnosis')}</Label>
            <Input
              id="diagnosis"
              placeholder={t('diagnosisPlaceholder')}
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="doctors_notes">{t('doctorsNotes')}</Label>
            <Textarea
              id="doctors_notes"
              placeholder={t('doctorsNotesPlaceholder')}
              value={doctorsNotes}
              onChange={(e) => setDoctorsNotes(e.target.value)}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="advice">{t('advice')}</Label>
            <Textarea
              id="advice"
              placeholder={t('advicePlaceholder')}
              value={advice}
              onChange={(e) => setAdvice(e.target.value)}
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Medicines */}
      <Card>
        <CardHeader>
          <CardTitle>
            {t('medicines')} <span className="text-red-500">*</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {rowsFromCase > 0 && <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">{t('prefilledFromVisit', { count: rowsFromCase })}</p>}
          <MedicineItemsBuilder
            key={rowsVersion}
            items={items}
            onChange={setItems}
            prescriptionId={prescription?.id}
            isEdit={isEdit}
          />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center sticky bottom-4 bg-background p-4 border rounded-lg shadow-lg">
        <div className="text-sm text-muted-foreground">
          {!isValid && (
            <p className="text-amber-600">
              {hasUnfinishedRow ? t('unfinishedRowHint') : t('validationHint')}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={!patientId || hasUnfinishedRow || isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            {t('saveDraft')}
          </Button>
          {can('prescriptions.issue') && (
            <Button onClick={handleIssue} disabled={!isValid || isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle className="mr-2 h-4 w-4" />
              )}
              {t('issue')}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
