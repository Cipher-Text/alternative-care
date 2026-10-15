'use client'

import { useLocale, useTranslations } from 'next-intl'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useVisits } from '@/lib/hooks/useHealth'
import type { VisitListItem } from '@/types/health'

const NONE = '__none'

/** Pick which of this patient's visits the prescription belongs to (or none, for a quick repeat prescription). */
export function VisitPicker({
  patientId,
  value,
  onChange,
  disabled = false,
}: {
  patientId: string
  value: string
  onChange: (visitId: string, visit?: VisitListItem) => void
  disabled?: boolean
}) {
  const t = useTranslations('rxVisitPickerUi')
  const locale = useLocale()
  const { data: visits = [], isLoading } = useVisits(patientId || undefined)
  const date = (iso: string) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(`${iso}T00:00:00`))

  return (
    <Select
      value={value || NONE}
      disabled={disabled || !patientId}
      onValueChange={(v) => onChange(v === NONE ? '' : v, visits.find((x) => x.id === v))}
    >
      <SelectTrigger aria-label={t('label')}>
        <SelectValue placeholder={patientId ? t('none') : t('pickPatientFirst')} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE}>{t('none')}</SelectItem>
        {isLoading && <p className="px-3 py-2 text-sm text-muted-foreground">{t('loading')}</p>}
        {!isLoading && visits.length === 0 && patientId && <p className="px-3 py-2 text-sm text-muted-foreground">{t('noVisits')}</p>}
        {visits.map((v) => (
          <SelectItem key={v.id} value={v.id}>
            {date(v.visit_date)}
            {v.chief_complaint ? ` · ${v.chief_complaint.slice(0, 50)}` : ''}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
