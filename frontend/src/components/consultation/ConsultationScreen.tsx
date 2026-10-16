'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { useQueryClient } from 'react-query'
import { toast } from 'react-hot-toast'
import { ArrowLeft, CheckCircle, FileText, Loader2, Printer, Save } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { SafetyBanner } from '@/components/health/SafetyBanner'
import { useCodeLabel } from '@/components/health/useCodeLabel'
import { CaseForm } from '@/components/case-taking/CaseForm'
import { fieldErrors } from '@/components/case-taking/PatientCaseCard'
import { MedicineItemsBuilder, blankMedicineRow, isRowComplete, isRowStarted } from '@/components/prescriptions/MedicineItemsBuilder'
import { prescriptionsApi } from '@/lib/api/prescriptions'
import { caseTakingApi } from '@/lib/api/caseTaking'
import { healthApi } from '@/lib/api/health'
import { errorMessage } from '@/lib/apiErrors'
import { useCan } from '@/lib/auth/permissions'
import { CASE_SYSTEMS, caseKeys, useCaseSystems, useVisitCase, type CaseSystem } from '@/lib/hooks/useCaseTaking'
import { healthKeys, useHealthOptions, useVisit } from '@/lib/hooks/useHealth'
import { usePatient } from '@/lib/hooks/usePatients'
import { usePrescription, usePrescriptions, useViewPrescriptionPdf } from '@/lib/hooks/usePrescriptions'
import { medicineRowsFromCase } from '@/lib/prescriptions/medicineRowsFromCase'
import type { CaseData } from '@/types/caseTaking'
import type { VisitDetail } from '@/types/health'
import type { Patient } from '@/types/patient'
import type { PrescriptionItemCreate } from '@/types/prescription'
import { FollowUpBooking } from './FollowUpBooking'
import { VisitPaymentSection } from './VisitPaymentSection'
import { NONE, NUMBER_FIELDS, SUPERSEDED_BY_MEDICINES, bmiOf, draftFromVisit, visitPayload, type VisitDraft } from './visitDraft'

/** Whole years between a birth date and a day (both YYYY-MM-DD). */
function ageOn(birth: string, day: string): number {
  const [by, bm, bd] = birth.split('-').map(Number)
  const [dy, dm, dd] = day.split('-').map(Number)
  return dy - by - (dm < bm || (dm === bm && dd < bd) ? 1 : 0)
}

const VISIT_TYPES = ['consultation', 'follow_up', 'emergency', 'routine_checkup'] as const

/**
 * One screen per consultation, top to bottom like the paper case sheet: complaint and history, vitals, case details,
 * diagnosis and plan (entered once), medicines, then Save / Issue prescription / Finish. Replaces the separate visit pop-up
 * and the separate prescription form for the usual case; the prescription is created from this page.
 */
export function ConsultationScreen({ visitId }: { visitId: string }) {
  const t = useTranslations('consultationUi')
  const { data: visit, isLoading, error } = useVisit(visitId)
  const { data: patient } = usePatient(visit?.patient_id ?? '')

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center" role="status" aria-label={t('loading')}>
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" aria-hidden="true" />
      </div>
    )
  }
  if (error || !visit) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg font-semibold">{t('notFound')}</p>
        <Button asChild variant="outline" className="mt-4">
          <Link href="/patients">{t('backToPatients')}</Link>
        </Button>
      </div>
    )
  }
  return <ConsultationForm visit={visit} patient={patient} />
}

function ConsultationForm({ visit, patient }: { visit: VisitDetail; patient: Patient | undefined }) {
  const t = useTranslations('consultationUi')
  const tv = useTranslations('healthUi.visits')
  const tc = useTranslations('caseTakingUi.panel')
  const locale = useLocale()
  const queryClient = useQueryClient()
  const { can } = useCan()
  const canEdit = can('visits.write')
  const canWriteRx = can('prescriptions.write')
  const canIssue = can('prescriptions.issue')
  const { data: options } = useHealthOptions()
  const typeLabel = useCodeLabel('visitType')
  const flagLabel = useCodeLabel('redFlag')
  const referralLabel = useCodeLabel('referral')
  const sugarLabel = useCodeLabel('sugarType')
  const viewPdf = useViewPrescriptionPdf()

  // ---- the visit itself
  const [draft, setDraft] = useState<VisitDraft>(() => draftFromVisit(visit))
  const [flags, setFlags] = useState<string[]>(() => visit.red_flags ?? [])
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState<null | 'save' | 'issue' | 'finish'>(null)
  const set = (key: string, value: string) => {
    setDraft((d) => ({ ...d, [key]: value }))
    setDirty(true)
  }
  const num = (key: string): number | null => (draft[key]?.trim() ? Number(draft[key]) : null)
  const bmi = bmiOf(num('weight_kg'), num('height_cm'))

  // ---- case details, per system the clinic practises
  const systems = useCaseSystems()
  const homeoCase = useVisitCase(visit.id, 'homeopathy', systems.includes('homeopathy'))
  const ayurvedaCase = useVisitCase(visit.id, 'ayurveda', systems.includes('ayurveda'))
  const unaniCase = useVisitCase(visit.id, 'unani', systems.includes('unani'))
  const caseQueries = { homeopathy: homeoCase, ayurveda: ayurvedaCase, unani: unaniCase }
  const [caseData, setCaseData] = useState<Partial<Record<CaseSystem, CaseData>>>({})
  const [caseLoaded, setCaseLoaded] = useState<Partial<Record<CaseSystem, boolean>>>({})
  const [caseTouched, setCaseTouched] = useState<Partial<Record<CaseSystem, boolean>>>({})
  const [caseErrors, setCaseErrors] = useState<Record<string, string>>({})
  for (const s of CASE_SYSTEMS) {
    const record = caseQueries[s].data
    if (systems.includes(s) && record && !caseLoaded[s]) {
      setCaseLoaded((l) => ({ ...l, [s]: true }))
      setCaseData((d) => ({ ...d, [s]: record.data }))
    }
  }
  const caseReady = CASE_SYSTEMS.every((s) => !systems.includes(s) || caseLoaded[s] || caseQueries[s].isError)

  // ---- prescriptions written for this visit
  const { data: visitPrescriptions } = usePrescriptions({ visit_id: visit.id, limit: 20 })
  const draftRx = visitPrescriptions?.find((p) => p.status === 'draft')
  const sentRx = (visitPrescriptions ?? []).filter((p) => p.status !== 'draft')
  const { data: draftFull } = usePrescription(draftRx?.id ?? '')
  const [items, setItems] = useState<PrescriptionItemCreate[]>([blankMedicineRow()])
  const [itemsInit, setItemsInit] = useState(false)
  const [itemsTouched, setItemsTouched] = useState(false)
  const [rowsVersion, setRowsVersion] = useState(0)
  const [rowsFromCase, setRowsFromCase] = useState(0)
  const th = useTranslations('caseTakingUi.homeopathy')
  const ta = useTranslations('caseTakingUi.ayurveda')
  const tu = useTranslations('caseTakingUi.unani')
  const caseLabels = { homeopathy: th, ayurveda: ta, unani: tu }
  if (!itemsInit && visitPrescriptions && caseReady && (!draftRx || draftFull)) {
    setItemsInit(true)
    if (draftFull && draftFull.items.length > 0) {
      setItems(
        draftFull.items.map((item) => ({
          medicine_id: item.medicine_id,
          medicine_name: item.medicine_name,
          dosage: item.dosage,
          frequency: item.frequency,
          duration: item.duration,
          quantity: item.quantity,
          instructions: item.instructions,
          display_order: item.display_order,
        }))
      )
      setRowsVersion((v) => v + 1)
    } else if (!draftRx && sentRx.length === 0) {
      // A visit whose medicines were written in the older case-form fields: they become the first rows
      const rows = systems.flatMap((s) => {
        const data = caseData[s]
        const label = caseLabels[s]
        return data ? medicineRowsFromCase(s, data, (key, code) => (code ? label(`fields.${key}.options.${code}`) : label(`fields.${key}.label`))) : []
      })
      if (rows.length > 0) {
        setItems(rows)
        setRowsFromCase(rows.length)
        setRowsVersion((v) => v + 1)
        setItemsTouched(true)
        setDirty(true)
      }
    }
  }
  const finishedRows = items.filter(isRowComplete)
  const hasUnfinishedRow = items.some((item) => isRowStarted(item) && !isRowComplete(item))

  // Leaving with unsaved changes asks first
  useEffect(() => {
    if (!dirty) return
    const guard = (event: BeforeUnloadEvent) => {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', guard)
    return () => window.removeEventListener('beforeunload', guard)
  }, [dirty])

  // ---- saving
  const refresh = () => {
    queryClient.invalidateQueries(['health', 'visit', visit.id])
    queryClient.invalidateQueries(healthKeys.visits(visit.patient_id))
    queryClient.invalidateQueries('prescriptions')
    queryClient.invalidateQueries('appointments')
    queryClient.invalidateQueries(['dashboard'])
  }

  /** Saves the visit, the case details that changed and the draft medicines. Returns the id of the draft prescription, if any. */
  const saveAll = async (opts: { finish?: boolean; forIssue?: boolean } = {}): Promise<{ ok: boolean; rxId?: string }> => {
    if (canEdit) {
      const { errors: found, payload } = visitPayload(draft, flags, {
        numberInvalid: (min, max) => tv('numberInvalid', { min, max }),
        bpPair: tv('bpPair'),
        bpOrder: tv('bpOrder'),
        sugarPair: tv('sugarPair'),
      })
      setErrors(found)
      if (Object.keys(found).length > 0) {
        toast.error(t('fixErrors'))
        return { ok: false }
      }
      try {
        await healthApi.updateVisit(visit.id, opts.finish ? { ...payload, status: 'completed' } : payload)
      } catch (error) {
        toast.error(errorMessage(error, tv('saveFailed')))
        return { ok: false }
      }
      for (const s of systems) {
        if (!caseTouched[s]) continue
        try {
          const record = await caseTakingApi.saveVisit(visit.id, s, caseData[s] ?? {})
          queryClient.setQueryData(caseKeys.visit(visit.id, s), record)
          setCaseErrors({})
        } catch (error) {
          setCaseErrors(fieldErrors(error))
          toast.error(errorMessage(error, tc('saveFailed')))
          return { ok: false }
        }
      }
    }

    let rxId = draftRx?.id
    if (canWriteRx && (itemsTouched || opts.forIssue)) {
      if (hasUnfinishedRow) {
        toast.error(t('unfinishedRow'))
        if (opts.forIssue) return { ok: false }
      } else {
        try {
          // The prescription takes its diagnosis and advice from this visit: they are entered once, here
          const diagnosis = draft.provisional_diagnosis?.trim() || null
          const advice = draft.treatment_plan?.trim() || null
          if (rxId) {
            await prescriptionsApi.update(rxId, { diagnosis, advice, items: finishedRows })
          } else if (finishedRows.length > 0) {
            rxId = (await prescriptionsApi.create({ patient_id: visit.patient_id, visit_id: visit.id, diagnosis, advice, items: finishedRows, status: 'draft' })).id
          }
          setItemsTouched(false)
        } catch (error) {
          toast.error(errorMessage(error, t('medicinesFailed')))
          return { ok: false }
        }
      }
    }
    setDirty(false)
    refresh()
    return { ok: true, rxId }
  }

  const onSave = async () => {
    setBusy('save')
    const result = await saveAll()
    setBusy(null)
    if (result.ok) toast.success(t('saved'))
  }

  const onIssue = async () => {
    if (finishedRows.length === 0) {
      toast.error(t('needMedicine'))
      return
    }
    setBusy('issue')
    const result = await saveAll({ forIssue: true })
    if (result.ok && result.rxId) {
      try {
        await prescriptionsApi.update(result.rxId, { status: 'issued' })
        toast.success(t('issued'))
        // The issued prescription is permanent: the editor starts a fresh, empty one
        setItems([blankMedicineRow()])
        setRowsVersion((v) => v + 1)
        setItemsTouched(false)
        setRowsFromCase(0)
        refresh()
      } catch (error) {
        toast.error(errorMessage(error, t('issueFailed')))
      }
    }
    setBusy(null)
  }

  const onFinish = async () => {
    setBusy('finish')
    const result = await saveAll({ finish: true })
    setBusy(null)
    if (result.ok) toast.success(tv('finished'))
  }

  // ---- drawing
  const field = (key: string, label: string, inputMode: 'numeric' | 'decimal' = 'decimal') => (
    <div key={key} className="space-y-1.5">
      <Label htmlFor={`c-${key}`}>{label}</Label>
      <Input id={`c-${key}`} inputMode={inputMode} value={draft[key] ?? ''} onChange={(e) => set(key, e.target.value)} aria-invalid={Boolean(errors[key])} />
      {errors[key] && <p role="alert" className="text-xs text-red-600">{errors[key]}</p>}
    </div>
  )
  const area = (key: string, label: string, rows = 2) => (
    <div key={key} className="space-y-1.5">
      <Label htmlFor={`c-${key}`}>{label}</Label>
      <Textarea id={`c-${key}`} rows={rows} value={draft[key] ?? ''} onChange={(e) => set(key, e.target.value)} />
    </div>
  )
  const when = (iso: string) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(`${iso}T00:00:00`))
  const completed = visit.status === 'completed'
  // Age on the day of the visit (so the screen shows the same age whenever it is opened)
  const age = patient?.date_of_birth ? ageOn(patient.date_of_birth, visit.visit_date) : null

  return (
    <div className="space-y-5 pb-28">
      {/* Patient strip */}
      <div className="space-y-2">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href={`/patients/${visit.patient_id}#visits`}>
            <ArrowLeft className="mr-1 h-4 w-4" aria-hidden="true" />
            {t('backToPatient')}
          </Link>
        </Button>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <h1 className="text-3xl font-bold">{patient?.full_name ?? t('title')}</h1>
          <Badge variant={completed ? 'secondary' : 'default'}>{completed ? tv('completed') : tv('inProgress')}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {[t('title'), when(visit.visit_date), age !== null ? t('years', { age }) : null, patient?.gender ? t(`gender.${patient.gender}`) : null, patient?.phone ?? null].filter(Boolean).join(' · ')}
        </p>
        <SafetyBanner patientId={visit.patient_id} />
      </div>

      {completed && <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">{t('completedNote')}</p>}
      {!canEdit && <p className="rounded-md border px-3 py-2 text-sm text-muted-foreground">{t('readOnly')}</p>}

      <fieldset disabled={!canEdit} className="min-w-0 space-y-5">
        {/* Complaint and history */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{t('sectionComplaint')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="max-w-xs space-y-1.5">
              <Label>{tv('visitType')}</Label>
              <Select value={draft.visit_type} onValueChange={(v) => set('visit_type', v)}>
                <SelectTrigger aria-label={tv('visitType')}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {VISIT_TYPES.map((c) => <SelectItem key={c} value={c}>{typeLabel(c)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            {area('chief_complaint', tv('complaint'))}
            {area('history_of_present_illness', t('history'), 3)}
            {area('examination_notes', tv('examination'))}
          </CardContent>
        </Card>

        {/* Vitals and warning signs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{tv('vitals')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {NUMBER_FIELDS.slice(0, 1).map(([key, label]) => field(key, tv(label)))}
              {NUMBER_FIELDS.slice(1, 2).map(([key, label]) => field(key, tv(label), 'numeric'))}
              <div className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-1">
                {field('bp_systolic', tv('bpSystolic'), 'numeric')}
                {field('bp_diastolic', tv('bpDiastolic'), 'numeric')}
              </div>
              {NUMBER_FIELDS.slice(2, 4).map(([key, label]) => field(key, tv(label), 'numeric'))}
              {NUMBER_FIELDS.slice(4, 6).map(([key, label]) => field(key, tv(label)))}
              {field('blood_sugar_mmol', tv('sugar'))}
              <div className="space-y-1.5">
                <Label>{tv('sugarType')}</Label>
                <Select value={draft.blood_sugar_type} onValueChange={(v) => set('blood_sugar_type', v)}>
                  <SelectTrigger aria-label={tv('sugarType')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>—</SelectItem>
                    {(options?.blood_sugar_types ?? []).map((c) => <SelectItem key={c} value={c}>{sugarLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {NUMBER_FIELDS.slice(6).map(([key, label]) => field(key, tv(label), 'numeric'))}
            </div>
            {errors.bp && <p role="alert" className="text-xs text-red-600">{errors.bp}</p>}
            {errors.sugar && <p role="alert" className="text-xs text-red-600">{errors.sugar}</p>}
            {bmi !== null && <p className="text-sm text-muted-foreground">{tv('bmi')}: <span className="font-medium">{bmi}</span></p>}

            <div className="space-y-2 border-t pt-3">
              <h3 className="text-sm font-semibold">{tv('redFlags')}</h3>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {(options?.red_flags ?? []).map((code) => (
                  <label key={code} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={flags.includes(code)}
                      onChange={() => {
                        setFlags((f) => (f.includes(code) ? f.filter((c) => c !== code) : [...f, code]))
                        setDirty(true)
                      }}
                    />
                    {flagLabel(code)}
                  </label>
                ))}
              </div>
              <div className="max-w-sm space-y-1.5">
                <Label>{tv('referral')}</Label>
                <Select value={draft.referral_urgency} onValueChange={(v) => set('referral_urgency', v)}>
                  <SelectTrigger aria-label={tv('referral')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>—</SelectItem>
                    {(options?.referral_urgencies ?? []).map((c) => <SelectItem key={c} value={c}>{referralLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Case details for each system the clinic practises */}
        {systems.map((s) => (
          <CaseSection
            key={s}
            system={s}
            ready={Boolean(caseLoaded[s])}
            value={caseData[s] ?? {}}
            errors={caseErrors}
            onChange={(next) => {
              setCaseData((d) => ({ ...d, [s]: next }))
              setCaseTouched((c) => ({ ...c, [s]: true }))
              setDirty(true)
            }}
          />
        ))}

        {/* Diagnosis and plan: entered once */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{t('sectionDiagnosis')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {area('provisional_diagnosis', tv('diagnosis'))}
            {area('treatment_plan', tv('plan'), 3)}
            <p className="text-xs text-muted-foreground">{t('planHint')}</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="c-follow_up_date">{tv('followUpDate')}</Label>
                <Input id="c-follow_up_date" type="date" min={visit.visit_date} value={draft.follow_up_date ?? ''} onChange={(e) => set('follow_up_date', e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="c-follow_up_notes">{tv('followUpNote')}</Label>
                <Input id="c-follow_up_notes" maxLength={300} value={draft.follow_up_notes ?? ''} onChange={(e) => set('follow_up_notes', e.target.value)} />
              </div>
            </div>
          </CardContent>
        </Card>
      </fieldset>

      {/* Medicines: becomes the prescription */}
      {(canWriteRx || sentRx.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              {t('sectionMedicines')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {sentRx.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold">{t('sentPrescriptions')}</h3>
                {sentRx.map((p) => (
                  <div key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm">
                    <Link href={`/prescriptions/${p.id}`} className="font-medium hover:underline">
                      {tv(`rxStatus.${p.status}`)} · {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(p.created_at))}
                    </Link>
                    {p.status === 'issued' && (
                      <Button type="button" size="sm" variant="outline" disabled={viewPdf.isLoading} onClick={() => viewPdf.mutate(p.id)}>
                        <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                        {t('viewPdf')}
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
            {canWriteRx && (
              <div className="space-y-3">
                {sentRx.length > 0 && <h3 className="text-sm font-semibold">{t('newPrescription')}</h3>}
                {rowsFromCase > 0 && (
                  <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
                    {t('fromCaseNote', { count: rowsFromCase })}
                  </p>
                )}
                <MedicineItemsBuilder
                  key={rowsVersion}
                  items={items}
                  onChange={(next) => {
                    setItems(next)
                    setItemsTouched(true)
                    setDirty(true)
                  }}
                />
                {hasUnfinishedRow && <p className="text-sm text-amber-600">{t('unfinishedRow')}</p>}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* The next appointment, and the payment for this visit */}
      <FollowUpBooking patientId={visit.patient_id} visitDate={visit.visit_date} followUpDate={draft.follow_up_date || undefined} notes={draft.follow_up_notes} />
      {(can('payments.read') || can('payments.write')) && (
        <VisitPaymentSection visitId={visit.id} patientId={visit.patient_id} visitType={draft.visit_type} />
      )}

      {/* Actions */}
      <div className="sticky bottom-4 z-10 flex flex-col gap-3 rounded-lg border bg-background p-4 shadow-lg sm:flex-row sm:items-center sm:justify-between">
        <p className={`text-sm ${dirty ? 'text-amber-600' : 'text-muted-foreground'}`} role="status">
          {dirty ? t('unsaved') : t('allSaved')}
        </p>
        <div className="flex flex-wrap gap-2">
          {(canEdit || canWriteRx) && (
            <Button type="button" variant="outline" onClick={onSave} disabled={busy !== null}>
              {busy === 'save' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <Save className="mr-2 h-4 w-4" aria-hidden="true" />}
              {t('save')}
            </Button>
          )}
          {canWriteRx && canIssue && (
            <Button type="button" onClick={onIssue} disabled={busy !== null || finishedRows.length === 0 || hasUnfinishedRow}>
              {busy === 'issue' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <FileText className="mr-2 h-4 w-4" aria-hidden="true" />}
              {t('issue')}
            </Button>
          )}
          {canEdit && !completed && (
            <Button type="button" variant="outline" onClick={onFinish} disabled={busy !== null}>
              {busy === 'finish' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <CheckCircle className="mr-2 h-4 w-4" aria-hidden="true" />}
              {t('finish')}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

function CaseSection({
  system,
  ready,
  value,
  errors,
  onChange,
}: {
  system: CaseSystem
  ready: boolean
  value: CaseData
  errors: Record<string, string>
  onChange: (next: CaseData) => void
}) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tc = useTranslations('consultationUi')
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{tc('sectionCase', { system: t('title') })}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {!ready ? (
          <Loader2 className="h-5 w-5 animate-spin text-emerald-600" aria-hidden="true" />
        ) : (
          <>
            <p className="text-xs text-muted-foreground">{tc('caseMedicinesNote')}</p>
            <CaseForm system={system} scope="visit" value={value} onChange={onChange} errors={errors} exclude={SUPERSEDED_BY_MEDICINES[system] ?? []} />
          </>
        )}
      </CardContent>
    </Card>
  )
}
