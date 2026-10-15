export type CaseScope = 'patient' | 'visit'
export type CaseFieldType = 'one' | 'many' | 'text' | 'quantity' | 'table'

/** One field of a case-taking form. Labels are translations (caseTakingUi.<system>), not part of this. */
export interface CaseFieldDef {
  key: string
  group: string
  scope: CaseScope
  type: CaseFieldType
  options?: string[]
  units?: string[]
  columns?: CaseFieldDef[]
  max_length?: number
  /** Tables: how many rows the form allows */
  max_rows?: number
}

export interface CaseDefinitions {
  system: string
  schema_version: number
  groups: { key: string; scope: CaseScope }[]
  fields: CaseFieldDef[]
}

export type CaseValue = string | string[] | { value: number; unit: string } | Record<string, string>[]
export type CaseData = Record<string, CaseValue>

export interface CaseRecord {
  system: string
  data: CaseData
  schema_version: number
  exists: boolean
  updated_at: string | null
  patient_id: string
  visit_id?: string | null
}
