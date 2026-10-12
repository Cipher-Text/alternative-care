'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { parseISO } from 'date-fns'
import { Loader2, Plus, Stethoscope } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useAuthStore } from '@/store/authStore'
import { errorMessage } from '@/lib/apiErrors'
import { toast } from 'react-hot-toast'
import { useCreateVisit, useHealthOptions, useVisits } from '@/lib/hooks/useHealth'
import { useCaseSystems, useSaveVisitCase } from '@/lib/hooks/useCaseTaking'
import { CaseForm } from '@/components/case-taking/CaseForm'
import { VisitCaseDetails } from '@/components/case-taking/VisitCaseDetails'
import type { CaseData } from '@/types/caseTaking'
import type { VisitInput, VisitListItem } from '@/types/health'
import { useCodeLabel } from './useCodeLabel'
import { localToday } from './localDate'

const NONE = '__none'
const VISIT_TYPES = ['consultation', 'follow_up', 'emergency', 'routine_checkup'] as const

/** Number fields: [form key, i18n label key, min, max, whole numbers only] */
const NUMBER_FIELDS = [
  ['temperature_c', 'temperature', 30, 45, false],
  ['pulse_bpm', 'pulse', 20, 250, true],
  ['respiratory_rate', 'respiratoryRate', 4, 80, true],
  ['spo2_percent', 'spo2', 50, 100, true],
  ['weight_kg', 'weight', 0.3, 500, false],
  ['height_cm', 'height', 30, 260, false],
  ['pain_score', 'pain', 0, 10, true],
] as const

export function bmiOf(weightKg: number | null | undefined, heightCm: number | null | undefined): number | null {
  if (!weightKg || !heightCm) return null
  const m = heightCm / 100
  return Math.round((weightKg / (m * m)) * 10) / 10
}

/** Visit history with the vitals taken, and a form to record a new visit (doctors only). */
export function VisitsCard({ patientId, canEdit }: { patientId: string; canEdit: boolean }) {
  const t = useTranslations('healthUi.visits')
  const { data: visits, isLoading } = useVisits(patientId)
  const [open, setOpen] = useState(false)
  const systems = useCaseSystems()

  return (
    <Card>
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
            <Button type="button" onClick={() => setOpen(true)}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              {t('add')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && <Loader2 className="h-5 w-5 animate-spin text-emerald-600" aria-hidden="true" />}
        {visits && visits.length === 0 && <p className="text-sm text-muted-foreground">{t('empty')}</p>}
        {visits?.map((v) => <VisitRow key={v.id} visit={v} systems={systems} canEdit={canEdit} />)}
        {!canEdit && <Badge variant="outline">{t('readOnly')}</Badge>}
      </CardContent>
      {open && <VisitDialog patientId={patientId} systems={systems} onClose={() => setOpen(false)} />}
    </Card>
  )
}

function VisitRow({ visit, systems, canEdit }: { visit: VisitListItem; systems: readonly string[]; canEdit: boolean }) {
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
    <div className="space-y-2 rounded-md border p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">
          {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(parseISO(visit.visit_date))}
        </span>
        <Badge variant="outline">{typeLabel(visit.visit_type)}</Badge>
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
        <VisitCaseDetails key={system} visitId={visit.id} system={system} canEdit={canEdit} />
      ))}
    </div>
  )
}

type Draft = Record<string, string>

function VisitDialog({ patientId, systems, onClose }: { patientId: string; systems: readonly string[]; onClose: () => void }) {
  const t = useTranslations('healthUi.visits')
  const userId = useAuthStore((s) => s.user?.id)
  const { data: options } = useHealthOptions()
  const create = useCreateVisit(patientId)
  const saveCase = useSaveVisitCase()
  const tc = useTranslations('caseTakingUi.panel')
  const [caseData, setCaseData] = useState<Record<string, CaseData>>({})
  const typeLabel = useCodeLabel('visitType')
  const flagLabel = useCodeLabel('redFlag')
  const referralLabel = useCodeLabel('referral')
  const sugarLabel = useCodeLabel('sugarType')
  const [draft, setDraft] = useState<Draft>({
    visit_date: localToday(),
    visit_type: 'consultation',
    blood_sugar_type: NONE,
    referral_urgency: NONE,
  })
  const [flags, setFlags] = useState<string[]>([])
  const [errors, setErrors] = useState<Record<string, string>>({})

  const set = (key: string, value: string) => setDraft((d) => ({ ...d, [key]: value }))
  const num = (key: string): number | null => (draft[key]?.trim() ? Number(draft[key]) : null)
  const bmi = bmiOf(num('weight_kg'), num('height_cm'))

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!userId) return
    const next: Record<string, string> = {}
    const payload: Record<string, number | string | string[]> = {}
    for (const [key, , min, max, whole] of NUMBER_FIELDS) {
      const n = num(key)
      if (n === null) continue
      if (!Number.isFinite(n) || n < min || n > max || (whole && !Number.isInteger(n))) next[key] = t('numberInvalid', { min, max })
      else payload[key] = n
    }
    const sys = num('bp_systolic')
    const dia = num('bp_diastolic')
    if ((sys === null) !== (dia === null)) next.bp = t('bpPair')
    else if (sys !== null && dia !== null) {
      if (!Number.isInteger(sys) || !Number.isInteger(dia) || sys < 40 || sys > 300 || dia < 20 || dia > 200) next.bp = t('numberInvalid', { min: 20, max: 300 })
      else if (dia >= sys) next.bp = t('bpOrder')
      else Object.assign(payload, { bp_systolic: sys, bp_diastolic: dia })
    }
    const sugar = num('blood_sugar_mmol')
    if (sugar !== null) {
      if (!Number.isFinite(sugar) || sugar < 1 || sugar > 60) next.sugar = t('numberInvalid', { min: 1, max: 60 })
      else {
        payload.blood_sugar_mmol = sugar
        if (draft.blood_sugar_type !== NONE) payload.blood_sugar_type = draft.blood_sugar_type
      }
    } else if (draft.blood_sugar_type !== NONE) next.sugar = t('sugarPair')
    setErrors(next)
    if (Object.keys(next).length > 0) return

    const body: VisitInput = {
      ...(payload as Partial<VisitInput>),
      patient_id: patientId,
      doctor_id: userId,
      visit_date: draft.visit_date,
      visit_type: draft.visit_type,
      chief_complaint: draft.chief_complaint?.trim() || undefined,
      examination_notes: draft.examination_notes?.trim() || undefined,
      provisional_diagnosis: draft.provisional_diagnosis?.trim() || undefined,
      treatment_plan: draft.treatment_plan?.trim() || undefined,
      red_flags: flags.length > 0 ? flags : undefined,
      referral_urgency: draft.referral_urgency !== NONE ? draft.referral_urgency : undefined,
    }
    let visit: VisitListItem
    try {
      visit = await create.mutateAsync(body)
    } catch {
      return // the mutation's onError already showed the reason
    }
    // The visit exists now; each system's details are saved to it. A failure here never loses the visit:
    // the details can be completed later from the visit's own "details" link.
    for (const system of systems) {
      const data = caseData[system]
      if (!data || Object.keys(data).length === 0) continue
      try {
        await saveCase.mutateAsync({ visitId: visit.id, system, data })
      } catch (error) {
        toast.error(errorMessage(error, tc('saveFailed')))
      }
    }
    onClose()
  }

  const field = (key: string, label: string, opts?: { inputMode?: 'numeric' | 'decimal' }) => (
    <div className="space-y-1.5">
      <Label htmlFor={`v-${key}`}>{label}</Label>
      <Input id={`v-${key}`} inputMode={opts?.inputMode ?? 'decimal'} value={draft[key] ?? ''} onChange={(e) => set(key, e.target.value)} aria-invalid={Boolean(errors[key])} />
      {errors[key] && <p role="alert" className="text-xs text-red-600">{errors[key]}</p>}
    </div>
  )

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t('dialogTitle')}</DialogTitle>
          <DialogDescription>{t('description')}</DialogDescription>
        </DialogHeader>
        <form className="space-y-5" onSubmit={submit} noValidate>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="v-date">{t('visitDate')}</Label>
              <Input id="v-date" type="date" value={draft.visit_date} onChange={(e) => set('visit_date', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>{t('visitType')}</Label>
              <Select value={draft.visit_type} onValueChange={(v) => set('visit_type', v)}>
                <SelectTrigger aria-label={t('visitType')}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {VISIT_TYPES.map((c) => <SelectItem key={c} value={c}>{typeLabel(c)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="v-complaint">{t('complaint')}</Label>
            <Textarea id="v-complaint" rows={2} value={draft.chief_complaint ?? ''} onChange={(e) => set('chief_complaint', e.target.value)} />
          </div>

          <section className="space-y-3">
            <h3 className="border-b pb-1 text-sm font-semibold">{t('vitals')}</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {NUMBER_FIELDS.slice(0, 1).map(([key, label]) => field(key, t(label)))}
              {NUMBER_FIELDS.slice(1, 2).map(([key, label]) => field(key, t(label), { inputMode: 'numeric' }))}
              <div className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-1">
                {field('bp_systolic', t('bpSystolic'), { inputMode: 'numeric' })}
                {field('bp_diastolic', t('bpDiastolic'), { inputMode: 'numeric' })}
              </div>
              {NUMBER_FIELDS.slice(2, 4).map(([key, label]) => field(key, t(label), { inputMode: 'numeric' }))}
              {NUMBER_FIELDS.slice(4, 6).map(([key, label]) => field(key, t(label)))}
              {field('blood_sugar_mmol', t('sugar'))}
              <div className="space-y-1.5">
                <Label>{t('sugarType')}</Label>
                <Select value={draft.blood_sugar_type} onValueChange={(v) => set('blood_sugar_type', v)}>
                  <SelectTrigger aria-label={t('sugarType')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>—</SelectItem>
                    {(options?.blood_sugar_types ?? []).map((c) => <SelectItem key={c} value={c}>{sugarLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {NUMBER_FIELDS.slice(6).map(([key, label]) => field(key, t(label), { inputMode: 'numeric' }))}
            </div>
            {errors.bp && <p role="alert" className="text-xs text-red-600">{errors.bp}</p>}
            {errors.sugar && <p role="alert" className="text-xs text-red-600">{errors.sugar}</p>}
            {bmi !== null && <p className="text-sm text-muted-foreground">{t('bmi')}: <span className="font-medium">{bmi}</span></p>}
          </section>

          <section className="space-y-2">
            <h3 className="border-b pb-1 text-sm font-semibold">{t('redFlags')}</h3>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {(options?.red_flags ?? []).map((code) => (
                <label key={code} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={flags.includes(code)} onChange={() => setFlags((f) => (f.includes(code) ? f.filter((c) => c !== code) : [...f, code]))} />
                  {flagLabel(code)}
                </label>
              ))}
            </div>
            <div className="max-w-sm space-y-1.5">
              <Label>{t('referral')}</Label>
              <Select value={draft.referral_urgency} onValueChange={(v) => set('referral_urgency', v)}>
                <SelectTrigger aria-label={t('referral')}><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>—</SelectItem>
                  {(options?.referral_urgencies ?? []).map((c) => <SelectItem key={c} value={c}>{referralLabel(c)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </section>

          {systems.map((system) => (
            <CaseFormSection key={system} system={system} value={caseData[system] ?? {}} onChange={(next) => setCaseData((d) => ({ ...d, [system]: next }))} />
          ))}

          <div className="space-y-1.5">
            <Label htmlFor="v-exam">{t('examination')}</Label>
            <Textarea id="v-exam" rows={2} value={draft.examination_notes ?? ''} onChange={(e) => set('examination_notes', e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="v-diagnosis">{t('diagnosis')}</Label>
            <Textarea id="v-diagnosis" rows={2} value={draft.provisional_diagnosis ?? ''} onChange={(e) => set('provisional_diagnosis', e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="v-plan">{t('plan')}</Label>
            <Textarea id="v-plan" rows={2} value={draft.treatment_plan ?? ''} onChange={(e) => set('treatment_plan', e.target.value)} />
          </div>

          <DialogFooter className="gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>{t('cancel')}</Button>
            <Button type="submit" disabled={create.isLoading || !userId}>
              {create.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {create.isLoading ? t('saving') : t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function CaseFormSection({ system, value, onChange }: { system: string; value: CaseData; onChange: (next: CaseData) => void }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  return (
    <section className="space-y-3 rounded-md border p-3">
      <h3 className="text-sm font-semibold">{tp('visitTitle', { system: t('title') })}</h3>
      <CaseForm system={system} scope="visit" value={value} onChange={onChange} />
    </section>
  )
}
