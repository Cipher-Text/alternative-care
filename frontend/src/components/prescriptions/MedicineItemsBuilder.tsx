'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { MedicineAutocomplete } from '@/components/medicines/MedicineAutocomplete'
import type { PrescriptionItemCreate } from '@/types/prescription'
import type { MedicineSearchResult } from '@/types/medicine'
import { PlusCircle, Trash2 } from 'lucide-react'

interface MedicineItemsBuilderProps {
  items: PrescriptionItemCreate[]
  onChange: (items: PrescriptionItemCreate[]) => void
  prescriptionId?: string
  isEdit?: boolean
}

export const blankMedicineRow = (displayOrder = 0): PrescriptionItemCreate => ({
  medicine_name: '',
  dosage: '',
  frequency: '',
  duration: null,
  quantity: null,
  instructions: null,
  display_order: displayOrder,
})

/** A row is complete when the three required cells are filled in. */
export const isRowComplete = (item: PrescriptionItemCreate) =>
  Boolean(item.medicine_name?.trim() && item.dosage.trim() && item.frequency.trim())

/** A row somebody has started typing in (so it must not be silently dropped when it is unfinished). */
export const isRowStarted = (item: PrescriptionItemCreate) =>
  Boolean(item.medicine_name?.trim() || item.dosage.trim() || item.frequency.trim() || item.duration || item.quantity || item.instructions)

// The columns of one row on a wide screen: number, medicine, dosage, frequency, duration, quantity, instructions, remove
const ROW_GRID = 'xl:grid-cols-[2rem_minmax(13rem,2.2fr)_minmax(7rem,1fr)_minmax(8rem,1.2fr)_minmax(6rem,0.9fr)_5rem_minmax(9rem,1.6fr)_2.5rem]'

/**
 * The medicines of a prescription as rows you type into: no pop-up. "Add new row" adds a blank one under the last; the
 * medicine cell searches the medicine database as you type, or keeps what you typed when it is not in the database.
 * Dosage guidance from the database fills the dosage cell when it is empty.
 */
export function MedicineItemsBuilder({ items, onChange }: MedicineItemsBuilderProps) {
  const t = useTranslations('rxItemsUi')
  // Rows have no id of their own; a stable key per row keeps each medicine box's text with its row when a row above is removed
  const [rowKeys, setRowKeys] = useState<string[]>(() => items.map(() => crypto.randomUUID()))
  const [focusKey, setFocusKey] = useState<string | null>(null)

  const update = (index: number, patch: Partial<PrescriptionItemCreate>) =>
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)))

  const addRow = () => {
    const key = crypto.randomUUID()
    setRowKeys((keys) => [...keys, key])
    setFocusKey(key)
    onChange([...items, blankMedicineRow(items.length)])
  }

  const removeRow = (index: number) => {
    setRowKeys((keys) => keys.filter((_, i) => i !== index))
    onChange(items.filter((_, i) => i !== index).map((item, i) => ({ ...item, display_order: i })))
  }

  const pick = (index: number, medicine: MedicineSearchResult) =>
    update(index, {
      medicine_name: medicine.potency ? `${medicine.name_en} ${medicine.potency}` : medicine.name_en,
      // Guidance fills an empty dosage; it never overwrites what the doctor already typed
      dosage: items[index].dosage.trim() ? items[index].dosage : medicine.dosage_guidance_en || '',
    })

  return (
    <div className="space-y-3">
      {items.length > 0 && (
        <div className="hidden gap-2 px-1 text-xs font-medium text-muted-foreground xl:grid xl:[grid-template-columns:var(--cols)]" style={{ '--cols': '2rem minmax(13rem,2.2fr) minmax(7rem,1fr) minmax(8rem,1.2fr) minmax(6rem,0.9fr) 5rem minmax(9rem,1.6fr) 2.5rem' } as React.CSSProperties}>
          <span>#</span>
          <span>{t('colMedicine')} *</span>
          <span>{t('colDosage')} *</span>
          <span>{t('colFrequency')} *</span>
          <span>{t('colDuration')}</span>
          <span>{t('colQty')}</span>
          <span>{t('colInstructions')}</span>
          <span />
        </div>
      )}

      {items.map((item, index) => {
        const started = isRowStarted(item)
        const missing = (value: string | null | undefined) => started && !(value ?? '').trim()
        const key = rowKeys[index] ?? String(index)
        return (
          <div key={key} className={`grid grid-cols-2 items-start gap-2 rounded-lg border p-3 md:grid-cols-4 xl:border-0 xl:p-0 ${ROW_GRID}`}>
            <span className="col-span-full text-sm font-medium text-muted-foreground xl:col-span-1 xl:pt-2">{index + 1}</span>

            <div className="col-span-full space-y-1 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colMedicine')} *</Label>
              <MedicineAutocomplete
                defaultValue={item.medicine_name ?? ''}
                placeholder={t('autocompletePlaceholder')}
                autoFocus={focusKey === key}
                invalid={missing(item.medicine_name)}
                formatSelected={(m) => (m.potency ? `${m.name_en} ${m.potency}` : m.name_en)}
                onTextChange={(text) => update(index, { medicine_name: text })}
                onSelect={(medicine) => pick(index, medicine)}
              />
            </div>

            <div className="space-y-1 md:col-span-2 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colDosage')} *</Label>
              <Input aria-label={t('colDosage')} aria-invalid={missing(item.dosage) || undefined} placeholder={t('dosagePlaceholder')} value={item.dosage} onChange={(e) => update(index, { dosage: e.target.value })} />
            </div>

            <div className="space-y-1 md:col-span-2 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colFrequency')} *</Label>
              <Input aria-label={t('colFrequency')} aria-invalid={missing(item.frequency) || undefined} placeholder={t('frequencyPlaceholder')} value={item.frequency} onChange={(e) => update(index, { frequency: e.target.value })} />
            </div>

            <div className="space-y-1 md:col-span-2 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colDuration')}</Label>
              <Input aria-label={t('colDuration')} placeholder={t('durationPlaceholder')} value={item.duration ?? ''} onChange={(e) => update(index, { duration: e.target.value || null })} />
            </div>

            <div className="space-y-1 md:col-span-2 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colQty')}</Label>
              <Input
                aria-label={t('colQty')}
                type="number"
                min={0}
                placeholder={t('quantityPlaceholder')}
                value={item.quantity ?? ''}
                onChange={(e) => update(index, { quantity: e.target.value ? Number(e.target.value) : null })}
              />
            </div>

            <div className="col-span-full space-y-1 xl:col-span-1">
              <Label className="text-xs xl:sr-only">{t('colInstructions')}</Label>
              <Input
                aria-label={t('colInstructions')}
                placeholder={t('instructionsPlaceholder')}
                value={item.instructions ?? ''}
                onChange={(e) => update(index, { instructions: e.target.value || null })}
                // Enter in the last cell of the last row starts the next row, so a long prescription can be typed without the mouse
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    if (index === items.length - 1 && isRowComplete(item)) addRow()
                  }
                }}
              />
            </div>

            <Button type="button" variant="ghost" size="icon" className="col-span-full justify-self-end xl:col-span-1 xl:justify-self-auto" aria-label={t('deleteAria')} onClick={() => removeRow(index)}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        )
      })}

      {items.length === 0 && <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">{t('noMedicines')}</p>}

      <Button type="button" onClick={addRow} variant="outline" className="w-full">
        <PlusCircle className="mr-2 h-4 w-4" />
        {t('addRow')}
      </Button>
    </div>
  )
}
