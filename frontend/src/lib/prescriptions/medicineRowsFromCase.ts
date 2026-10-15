// Turns what a doctor recorded in a visit's case details (homeopathy, Ayurveda, Unani) into the first medicine rows of a
// prescription, so the medicine is not typed twice. Pure on purpose: no imports, so it can be tested without the app.

export interface RxRow {
  medicine_name: string
  dosage: string
  frequency: string
  duration: null
  quantity: null
  instructions: string | null
  display_order: number
}

type Answers = Record<string, unknown>

/** `label(key, code)` is the option's label in the user's language; `label(key)` is the field's label. */
export type CaseLabel = (key: string, code?: string) => string

const text = (v: unknown): string => (typeof v === 'string' ? v.trim() : '')

function row(name: string, dosage = '', frequency = '', instructions: string | null = null): Omit<RxRow, 'display_order'> {
  return { medicine_name: name, dosage, frequency, duration: null, quantity: null, instructions }
}

/** The medicines the case details name, as prescription rows. Dosage and frequency are filled only where the form recorded
 * something that means them; the doctor completes the rest (an unfinished row is flagged by the prescription form). */
export function medicineRowsFromCase(system: string, data: Answers, label: CaseLabel): RxRow[] {
  const rows: Omit<RxRow, 'display_order'>[] = []

  if (system === 'homeopathy') {
    const prescribed = Array.isArray(data.prescribed) ? (data.prescribed as Answers[]) : []
    for (const item of prescribed) {
      const name = text(item.name)
      if (!name) continue
      const potency = text(item.potency)
      rows.push(row(potency ? `${name} ${potency}` : name))
    }
    // The older single-remedy entry, when the medicines list was not used
    if (rows.length === 0 && text(data.remedy)) {
      const potency = typeof data.potency === 'string' ? label('potency', data.potency) : ''
      const form = typeof data.dose_form === 'string' ? label('dose_form', data.dose_form) : ''
      const repetition = typeof data.repetition === 'string' ? label('repetition', data.repetition) : ''
      rows.push(row(potency ? `${text(data.remedy)} ${potency}` : text(data.remedy), form, repetition))
    }
  } else if (system === 'unani') {
    if (text(data.ilaj_dawa_drug)) {
      rows.push(row(text(data.ilaj_dawa_drug), typeof data.drug_form === 'string' ? label('drug_form', data.drug_form) : ''))
    }
  } else if (system === 'ayurveda') {
    if (text(data.formulation)) {
      const anupana = typeof data.anupana === 'string' ? `${label('anupana')}: ${label('anupana', data.anupana)}` : null
      rows.push(row(text(data.formulation), '', '', anupana))
    }
  }

  return rows.map((r, i) => ({ ...r, display_order: i }))
}
