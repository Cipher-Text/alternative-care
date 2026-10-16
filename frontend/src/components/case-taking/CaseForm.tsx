'use client'

import { useTranslations } from 'next-intl'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useCaseDefinitions } from '@/lib/hooks/useCaseTaking'
import type { CaseData, CaseFieldDef, CaseScope, CaseValue } from '@/types/caseTaking'

const NONE = '__none'

interface Props {
  system: string
  scope: CaseScope
  value: CaseData
  onChange: (next: CaseData) => void
  /** Field key -> reason, from the server's 422 */
  errors?: Record<string, string>
  /** Fields not to draw (another part of the screen replaces them); their saved values are kept untouched */
  exclude?: string[]
}

/** Draws the fields of one system's form for one scope, from the server's definitions. Labels come from the
 * translations (caseTakingUi.<system>), so a new field needs no change here. */
export function CaseForm({ system, scope, value, onChange, errors, exclude = [] }: Props) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  const { data: defs } = useCaseDefinitions(system)
  if (!defs) return null

  const set = (key: string, v: CaseValue | undefined) => {
    const next = { ...value }
    if (v === undefined) delete next[key]
    else next[key] = v
    onChange(next)
  }
  const option = (f: CaseFieldDef, code: string) => t(`fields.${f.key}.options.${code}`)

  const control = (f: CaseFieldDef) => {
    const current = value[f.key]
    if (f.type === 'one') {
      return (
        <Select value={typeof current === 'string' ? current : NONE} onValueChange={(v) => set(f.key, v === NONE ? undefined : v)}>
          <SelectTrigger aria-label={t(`fields.${f.key}.label`)}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE}>{tp('choose')}</SelectItem>
            {(f.options ?? []).map((c) => <SelectItem key={c} value={c}>{option(f, c)}</SelectItem>)}
          </SelectContent>
        </Select>
      )
    }
    if (f.type === 'many') {
      const chosen = Array.isArray(current) ? (current as string[]) : []
      return (
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 sm:grid-cols-3">
          {(f.options ?? []).map((c) => (
            <label key={c} className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-1"
                checked={chosen.includes(c)}
                onChange={() => {
                  const next = chosen.includes(c) ? chosen.filter((x) => x !== c) : [...chosen, c]
                  set(f.key, next.length > 0 ? next : undefined)
                }}
              />
              {option(f, c)}
            </label>
          ))}
        </div>
      )
    }
    if (f.type === 'text' && (f.max_length ?? 500) <= 100) {
      // The short lines of the paper form (a colour, a yes-or-no kind of note) are one line, not a box
      return (
        <Input
          maxLength={f.max_length}
          aria-label={t(`fields.${f.key}.label`)}
          value={typeof current === 'string' ? current : ''}
          onChange={(e) => set(f.key, e.target.value || undefined)}
        />
      )
    }
    if (f.type === 'text') {
      return (
        <Textarea
          rows={2}
          maxLength={f.max_length}
          aria-label={t(`fields.${f.key}.label`)}
          value={typeof current === 'string' ? current : ''}
          onChange={(e) => set(f.key, e.target.value || undefined)}
        />
      )
    }
    if (f.type === 'quantity') {
      const q = current && !Array.isArray(current) && typeof current === 'object' ? (current as { value: number; unit: string }) : null
      const update = (patch: Partial<{ value: string; unit: string }>) => {
        const number = patch.value !== undefined ? patch.value : q ? String(q.value) : ''
        const unit = patch.unit ?? q?.unit ?? f.units?.[0] ?? ''
        if (!number.trim()) return set(f.key, undefined)
        const n = Number(number)
        set(f.key, Number.isFinite(n) && n >= 1 ? ({ value: Math.min(1000, Math.trunc(n)), unit } as CaseValue) : undefined)
      }
      return (
        <div className="grid max-w-xs grid-cols-2 gap-2">
          <Input inputMode="numeric" aria-label={tp('number')} value={q ? String(q.value) : ''} onChange={(e) => update({ value: e.target.value.replace(/\D/g, '') })} />
          <Select value={q?.unit ?? f.units?.[0]} onValueChange={(v) => update({ unit: v })}>
            <SelectTrigger aria-label={tp('unit')}><SelectValue /></SelectTrigger>
            <SelectContent>
              {(f.units ?? []).map((u) => <SelectItem key={u} value={u}>{option(f, u)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      )
    }
    // table
    const rows = Array.isArray(current) ? (current as Record<string, string>[]) : []
    const setRows = (next: Record<string, string>[]) => set(f.key, next.length > 0 ? next : undefined)
    const maxRows = f.max_rows ?? 20
    // One track per column: a choice is narrow, a long text takes the rest, then the remove button
    const tracks = [...(f.columns ?? []).map((c) => (c.type === 'one' ? '10rem' : (c.max_length ?? 100) > 50 ? '1fr' : '9rem')), 'auto'].join(' ')
    return (
      <div className="space-y-2">
        {rows.map((row, i) => (
          <div key={i} className="grid grid-cols-1 gap-2 rounded-md border p-2 sm:[grid-template-columns:var(--cols)]" style={{ '--cols': tracks } as React.CSSProperties}>
            {(f.columns ?? []).map((c) =>
              c.type === 'one' ? (
                <Select key={c.key} value={row[c.key] ?? NONE} onValueChange={(v) => setRows(rows.map((r, j) => (j === i ? { ...r, [c.key]: v === NONE ? '' : v } : r)))}>
                  <SelectTrigger aria-label={t(`fields.${f.key}.columns.${c.key}`)}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>{tp('choose')}</SelectItem>
                    {(c.options ?? []).map((code) => <SelectItem key={code} value={code}>{option(f, code)}</SelectItem>)}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  key={c.key}
                  aria-label={t(`fields.${f.key}.columns.${c.key}`)}
                  placeholder={t(`fields.${f.key}.columns.${c.key}`)}
                  maxLength={c.max_length}
                  value={row[c.key] ?? ''}
                  onChange={(e) => setRows(rows.map((r, j) => (j === i ? { ...r, [c.key]: e.target.value } : r)))}
                />
              )
            )}
            <Button type="button" variant="ghost" size="icon" aria-label={tp('removeRow')} onClick={() => setRows(rows.filter((_, j) => j !== i))}>
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" disabled={rows.length >= maxRows} onClick={() => setRows([...rows, {}])}>
          <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
          {tp('addRow')}
        </Button>
      </div>
    )
  }

  const groups = defs.groups.filter((g) => g.scope === scope)
  return (
    <div className="space-y-6">
      {groups.map((g, index) => {
        const fields = defs.fields.filter((f) => f.group === g.key && f.scope === scope && !exclude.includes(f.key))
        // A long form is easier in sections: the first is open, and any section with an answer or a problem is open too
        const needsAttention = fields.some((f) => value[f.key] !== undefined || errors?.[f.key])
        if (fields.length === 0) return null
        return (
          <details key={g.key} open={index === 0 || needsAttention} className="group rounded-lg border">
            <summary className="flex cursor-pointer select-none items-center justify-between px-3 py-2 text-sm font-semibold">
              {t(`groups.${g.key}`)}
              <span className="text-xs font-normal text-muted-foreground">{fields.length}</span>
            </summary>
            <div className="space-y-4 border-t p-3">
              {fields.map((f) => (
                <div key={f.key} className="space-y-1.5">
                  <Label>{t(`fields.${f.key}.label`)}</Label>
                  {control(f)}
                  {errors?.[f.key] && <p role="alert" className="text-xs text-red-600">{errors[f.key]}</p>}
                </div>
              ))}
            </div>
          </details>
        )
      })}
    </div>
  )
}
