'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { BookOpenCheck, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { usePatientCase, useSavePatientCase } from '@/lib/hooks/useCaseTaking'
import type { CaseData } from '@/types/caseTaking'
import { CaseForm } from './CaseForm'
import { CaseSummary } from './CaseSummary'

/** One system's patient-level case profile (constitution, generals, mind, history). Doctors only. */
export function PatientCaseCard({ patientId, system }: { patientId: string; system: string }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  const { data: record } = usePatientCase(patientId, system)
  const [open, setOpen] = useState(false)
  const title = t('title')

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BookOpenCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              {tp('profileTitle', { system: title })}
            </CardTitle>
            <CardDescription>{tp('profileDescription')}</CardDescription>
          </div>
          {record && <Button type="button" variant="outline" onClick={() => setOpen(true)}>{tp('edit')}</Button>}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {record && !record.exists && <p className="text-sm text-muted-foreground">{tp('empty')}</p>}
        {record?.exists && <CaseSummary system={system} scope="patient" data={record.data} />}
        <Badge variant="outline">{tp('draftNote')}</Badge>
      </CardContent>
      {open && record && <PatientCaseDialog patientId={patientId} system={system} initial={record.data} onClose={() => setOpen(false)} />}
    </Card>
  )
}

function PatientCaseDialog({ patientId, system, initial, onClose }: { patientId: string; system: string; initial: CaseData; onClose: () => void }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  const save = useSavePatientCase(patientId, system)
  const [data, setData] = useState<CaseData>(initial)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setErrors({})
    try {
      await save.mutateAsync(data)
      onClose()
    } catch (error) {
      setErrors(fieldErrors(error))
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{tp('profileTitle', { system: t('title') })}</DialogTitle>
          <DialogDescription>{tp('profileDescription')}</DialogDescription>
        </DialogHeader>
        <form className="space-y-6" onSubmit={submit} noValidate>
          <CaseForm system={system} scope="patient" value={data} onChange={setData} errors={errors} />
          <DialogFooter className="gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>{tp('cancel')}</Button>
            <Button type="submit" disabled={save.isLoading}>
              {save.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {save.isLoading ? tp('saving') : tp('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

/** The field -> reason map from a 422 `invalid_case_data`, or empty. */
export function fieldErrors(error: unknown): Record<string, string> {
  const detail = (error as { response?: { data?: { detail?: { errors?: Record<string, string> } } } })?.response?.data?.detail
  return detail?.errors ?? {}
}

