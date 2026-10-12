'use client'

import { useTranslations } from 'next-intl'
import { useCaseDefinitions } from '@/lib/hooks/useCaseTaking'
import type { CaseData, CaseFieldDef, CaseScope } from '@/types/caseTaking'

/** Read-only view of saved answers, grouped like the form. Shows only what was answered. */
export function CaseSummary({ system, scope, data }: { system: string; scope: CaseScope; data: CaseData }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const { data: defs } = useCaseDefinitions(system)
  if (!defs) return null

  const text = (f: CaseFieldDef): string => {
    const v = data[f.key]
    const label = (code: string) => t(`fields.${f.key}.options.${code}`)
    if (typeof v === 'string') return f.type === 'one' ? label(v) : v
    if (Array.isArray(v)) {
      if (f.type === 'table') {
        return (v as Record<string, string>[])
          .map((row) => (f.columns ?? []).map((c) => (c.type === 'one' && row[c.key] ? label(row[c.key]) : row[c.key])).filter(Boolean).join(' · '))
          .join('; ')
      }
      return (v as string[]).map(label).join(', ')
    }
    if (v && typeof v === 'object') return `${v.value} ${label(v.unit)}`
    return ''
  }

  const groups = defs.groups
    .filter((g) => g.scope === scope)
    .map((g) => ({ g, rows: defs.fields.filter((f) => f.group === g.key && f.scope === scope && data[f.key] !== undefined) }))
    .filter((x) => x.rows.length > 0)

  return (
    <div className="space-y-3">
      {groups.map(({ g, rows }) => (
        <div key={g.key}>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t(`groups.${g.key}`)}</h4>
          <dl className="mt-1 grid grid-cols-1 gap-x-6 gap-y-1 md:grid-cols-2">
            {rows.map((f) => (
              <div key={f.key} className="text-sm">
                <dt className="inline text-muted-foreground">{t(`fields.${f.key}.label`)}: </dt>
                <dd className="inline font-medium">{text(f)}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </div>
  )
}
