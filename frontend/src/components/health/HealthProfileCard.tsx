'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { HeartPulse, Loader2, Plus, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useHealthOptions, useHealthProfile, useSaveHealthProfile } from '@/lib/hooks/useHealth'
import type { AllergyEntry, HealthProfile, HealthProfileInput } from '@/types/health'
import { useCodeLabel } from './useCodeLabel'
import { localToday } from './localDate'

const NONE = '__none'

function toInput(p: HealthProfile): HealthProfileInput {
  return {
    chronic_conditions: p.chronic_conditions,
    allergies: p.allergies,
    family_history: p.family_history,
    smoking: p.smoking,
    alcohol: p.alcohol,
    betel_tobacco: p.betel_tobacco,
    diet_type: p.diet_type,
    pregnant: p.pregnant,
    lmp_date: p.lmp_date,
    breastfeeding: p.breastfeeding,
    on_allopathic_medicines: p.on_allopathic_medicines,
    on_blood_thinners: p.on_blood_thinners,
    recent_surgery: p.recent_surgery,
    current_medicines_note: p.current_medicines_note,
    past_surgeries_note: p.past_surgeries_note,
  }
}

/** Long-lived health background: what stays true between visits. Doctors edit; receptionists only read. */
export function HealthProfileCard({ patientId, canEdit }: { patientId: string; canEdit: boolean }) {
  const t = useTranslations('healthUi.profile')
  const locale = useLocale()
  const { data: profile, isLoading } = useHealthProfile(patientId)
  const [open, setOpen] = useState(false)
  const conditionLabel = useCodeLabel('chronic')
  const familyLabel = useCodeLabel('family')
  const habitLabel = useCodeLabel('habit')
  const dietLabel = useCodeLabel('diet')
  const allergyTypeLabel = useCodeLabel('allergyType')
  const severityLabel = useCodeLabel('severity')
  const flagLabel = useCodeLabel('flag')

  const rows: { title: string; value: string | null }[] = profile
    ? [
        { title: t('sections.conditions'), value: profile.chronic_conditions.map(conditionLabel).join(', ') || null },
        {
          title: t('sections.allergies'),
          value: profile.allergies.map((a) => `${a.substance} (${allergyTypeLabel(a.type)}${a.severity ? `, ${severityLabel(a.severity)}` : ''})`).join('; ') || null,
        },
        { title: t('sections.family'), value: profile.family_history.map(familyLabel).join(', ') || null },
        {
          title: t('sections.habits'),
          value:
            [
              profile.smoking && `${t('smoking')}: ${habitLabel(profile.smoking)}`,
              profile.alcohol && `${t('alcohol')}: ${habitLabel(profile.alcohol)}`,
              profile.betel_tobacco && `${t('betel')}: ${habitLabel(profile.betel_tobacco)}`,
              profile.diet_type && `${t('diet')}: ${dietLabel(profile.diet_type)}`,
            ]
              .filter(Boolean)
              .join(' · ') || null,
        },
        {
          title: t('sections.pregnancy'),
          value:
            [profile.pregnant && flagLabel('pregnant'), profile.breastfeeding && flagLabel('breastfeeding')].filter(Boolean).join(', ') || null,
        },
        {
          title: t('sections.medicines'),
          value:
            [
              profile.on_allopathic_medicines && flagLabel('on_allopathic_medicines'),
              profile.on_blood_thinners && flagLabel('on_blood_thinners'),
              profile.recent_surgery && flagLabel('recent_surgery'),
              profile.current_medicines_note,
              profile.past_surgeries_note,
            ]
              .filter(Boolean)
              .join(' · ') || null,
        },
      ]
    : []

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              {t('title')}
            </CardTitle>
            <CardDescription>{t('description')}</CardDescription>
          </div>
          {canEdit && profile && (
            <Button type="button" variant="outline" onClick={() => setOpen(true)}>
              {t('edit')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && <Loader2 className="h-5 w-5 animate-spin text-emerald-600" aria-hidden="true" />}
        {profile && !profile.exists && <p className="text-sm text-muted-foreground">{t('empty')}</p>}
        {profile?.exists && (
          <dl className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2">
            {rows.map((r) => (
              <div key={r.title}>
                <dt className="text-sm text-muted-foreground">{r.title}</dt>
                <dd className="text-sm font-medium">{r.value ?? <span className="text-muted-foreground">—</span>}</dd>
              </div>
            ))}
          </dl>
        )}
        {profile?.updated_at && (
          <p className="mt-3 text-xs text-muted-foreground">
            {t('lastUpdated', { date: new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(profile.updated_at)) })}
          </p>
        )}
        {!canEdit && <Badge variant="outline" className="mt-3">{t('readOnly')}</Badge>}
      </CardContent>
      {open && profile && <HealthProfileDialog patientId={patientId} profile={profile} onClose={() => setOpen(false)} />}
    </Card>
  )
}

function HealthProfileDialog({ patientId, profile, onClose }: { patientId: string; profile: HealthProfile; onClose: () => void }) {
  const t = useTranslations('healthUi.profile')
  const { data: options } = useHealthOptions()
  const save = useSaveHealthProfile(patientId)
  const [form, setForm] = useState<HealthProfileInput>(() => toInput(profile))
  const [errors, setErrors] = useState<{ allergy?: boolean; lmp?: boolean }>({})
  const conditionLabel = useCodeLabel('chronic')
  const familyLabel = useCodeLabel('family')
  const habitLabel = useCodeLabel('habit')
  const dietLabel = useCodeLabel('diet')
  const allergyTypeLabel = useCodeLabel('allergyType')
  const severityLabel = useCodeLabel('severity')

  const set = <K extends keyof HealthProfileInput>(key: K, value: HealthProfileInput[K]) => setForm((f) => ({ ...f, [key]: value }))
  const toggle = (key: 'chronic_conditions' | 'family_history', code: string) =>
    set(key, form[key].includes(code) ? form[key].filter((c) => c !== code) : [...form[key], code])
  const setAllergy = (i: number, patch: Partial<AllergyEntry>) =>
    set('allergies', form.allergies.map((a, j) => (j === i ? { ...a, ...patch } : a)))

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const today = localToday()
    const next = {
      allergy: form.allergies.some((a) => a.substance.trim().length === 0),
      lmp: Boolean(form.lmp_date && form.lmp_date > today),
    }
    setErrors(next)
    if (next.allergy || next.lmp) return
    try {
      await save.mutateAsync({
        ...form,
        allergies: form.allergies.map((a) => ({ ...a, substance: a.substance.trim() })),
        lmp_date: form.pregnant ? form.lmp_date : null,
        current_medicines_note: form.current_medicines_note?.trim() || null,
        past_surgeries_note: form.past_surgeries_note?.trim() || null,
      })
      onClose()
    } catch {
      /* the mutation's onError already showed the reason */
    }
  }

  const checkboxGroup = (key: 'chronic_conditions' | 'family_history', codes: string[], label: (c: string) => string) => (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {codes.map((code) => (
        <label key={code} className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form[key].includes(code)} onChange={() => toggle(key, code)} />
          {label(code)}
        </label>
      ))}
    </div>
  )
  const habitSelect = (key: 'smoking' | 'alcohol' | 'betel_tobacco', title: string) => (
    <div className="space-y-1.5">
      <Label>{title}</Label>
      <Select value={form[key] ?? NONE} onValueChange={(v) => set(key, v === NONE ? null : v)}>
        <SelectTrigger aria-label={title}><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>{t('choose')}</SelectItem>
          {(options?.habit_statuses ?? []).map((c) => <SelectItem key={c} value={c}>{habitLabel(c)}</SelectItem>)}
        </SelectContent>
      </Select>
    </div>
  )
  const section = (title: string) => <h3 className="border-b pb-1 text-sm font-semibold">{title}</h3>

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>{t('description')}</DialogDescription>
        </DialogHeader>
        <form className="space-y-6" onSubmit={submit} noValidate>
          <section className="space-y-3">
            {section(t('sections.conditions'))}
            {checkboxGroup('chronic_conditions', options?.chronic_conditions ?? [], conditionLabel)}
          </section>

          <section className="space-y-3">
            {section(t('sections.allergies'))}
            {form.allergies.map((a, i) => (
              <div key={i} className="grid grid-cols-1 gap-2 rounded-md border p-3 sm:grid-cols-[9rem_1fr_8rem_auto]">
                <Select value={a.type} onValueChange={(v) => setAllergy(i, { type: v })}>
                  <SelectTrigger aria-label={t('allergyType')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(options?.allergy_types ?? []).map((c) => <SelectItem key={c} value={c}>{allergyTypeLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
                <Input
                  aria-label={t('allergySubstance')}
                  placeholder={t('allergySubstancePlaceholder')}
                  maxLength={100}
                  value={a.substance}
                  onChange={(e) => setAllergy(i, { substance: e.target.value })}
                />
                <Select value={a.severity ?? NONE} onValueChange={(v) => setAllergy(i, { severity: v === NONE ? null : v })}>
                  <SelectTrigger aria-label={t('allergySeverity')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>{t('choose')}</SelectItem>
                    {(options?.allergy_severities ?? []).map((c) => <SelectItem key={c} value={c}>{severityLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
                <Button type="button" variant="ghost" size="icon" aria-label={t('removeAllergy')} onClick={() => set('allergies', form.allergies.filter((_, j) => j !== i))}>
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                </Button>
              </div>
            ))}
            {errors.allergy && <p role="alert" className="text-sm text-red-600">{t('allergyNeedsName')}</p>}
            <Button type="button" variant="outline" size="sm" disabled={form.allergies.length >= 30} onClick={() => set('allergies', [...form.allergies, { type: 'drug', substance: '', severity: null }])}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              {t('addAllergy')}
            </Button>
          </section>

          <section className="space-y-3">
            {section(t('sections.family'))}
            {checkboxGroup('family_history', options?.family_history ?? [], familyLabel)}
          </section>

          <section className="space-y-3">
            {section(t('sections.habits'))}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {habitSelect('smoking', t('smoking'))}
              {habitSelect('alcohol', t('alcohol'))}
              {habitSelect('betel_tobacco', t('betel'))}
              <div className="space-y-1.5">
                <Label>{t('diet')}</Label>
                <Select value={form.diet_type ?? NONE} onValueChange={(v) => set('diet_type', v === NONE ? null : v)}>
                  <SelectTrigger aria-label={t('diet')}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>{t('choose')}</SelectItem>
                    {(options?.diet_types ?? []).map((c) => <SelectItem key={c} value={c}>{dietLabel(c)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </section>

          <section className="space-y-3">
            {section(t('sections.pregnancy'))}
            <div className="flex flex-wrap gap-6">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.pregnant} onChange={(e) => set('pregnant', e.target.checked)} />
                {t('pregnant')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.breastfeeding} onChange={(e) => set('breastfeeding', e.target.checked)} />
                {t('breastfeeding')}
              </label>
            </div>
            {form.pregnant && (
              <div className="max-w-xs space-y-1.5">
                <Label htmlFor="hp-lmp">{t('lmp')}</Label>
                <Input id="hp-lmp" type="date" value={form.lmp_date ?? ''} onChange={(e) => set('lmp_date', e.target.value || null)} aria-invalid={errors.lmp} />
                {errors.lmp && <p role="alert" className="text-sm text-red-600">{t('lmpInvalid')}</p>}
              </div>
            )}
          </section>

          <section className="space-y-3">
            {section(t('sections.medicines'))}
            <div className="grid gap-2">
              {([['on_allopathic_medicines', 'allopathic'], ['on_blood_thinners', 'bloodThinners'], ['recent_surgery', 'recentSurgery']] as const).map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={form[key]} onChange={(e) => set(key, e.target.checked)} />
                  {t(label)}
                </label>
              ))}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="hp-meds">{t('medicinesNote')}</Label>
              <Textarea id="hp-meds" rows={2} maxLength={1000} value={form.current_medicines_note ?? ''} onChange={(e) => set('current_medicines_note', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="hp-surg">{t('surgeriesNote')}</Label>
              <Textarea id="hp-surg" rows={2} maxLength={1000} value={form.past_surgeries_note ?? ''} onChange={(e) => set('past_surgeries_note', e.target.value)} />
            </div>
          </section>

          <DialogFooter className="gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>{t('cancel')}</Button>
            <Button type="submit" disabled={save.isLoading}>
              {save.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {save.isLoading ? t('saving') : t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
