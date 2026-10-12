'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useSaveVisitCase, useVisitCase } from '@/lib/hooks/useCaseTaking'
import { errorMessage } from '@/lib/apiErrors'
import type { CaseData } from '@/types/caseTaking'
import { CaseForm } from './CaseForm'
import { fieldErrors } from './PatientCaseCard'
import { CaseSummary } from './CaseSummary'

/** One system's details for one visit, loaded when opened, with an edit form for doctors. */
export function VisitCaseDetails({ visitId, system, canEdit }: { visitId: string; system: string; canEdit: boolean }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  const [shown, setShown] = useState(false)
  const [editing, setEditing] = useState(false)
  const { data: record, isLoading } = useVisitCase(visitId, system, shown)

  return (
    <div className="space-y-2">
      <Button type="button" variant="link" className="h-auto p-0 text-sm" onClick={() => setShown((s) => !s)}>
        {shown ? tp('hideDetails') : tp('viewDetails', { system: t('title') })}
      </Button>
      {shown && isLoading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" aria-hidden="true" />}
      {shown && record && (
        <div className="space-y-2 rounded-md bg-muted/40 p-3">
          {record.exists ? <CaseSummary system={system} scope="visit" data={record.data} /> : <p className="text-sm text-muted-foreground">{tp('noDetails', { system: t('title') })}</p>}
          {canEdit && <Button type="button" variant="outline" size="sm" onClick={() => setEditing(true)}>{tp('edit')}</Button>}
        </div>
      )}
      {editing && record && <VisitCaseDialog visitId={visitId} system={system} initial={record.data} onClose={() => setEditing(false)} />}
    </div>
  )
}

function VisitCaseDialog({ visitId, system, initial, onClose }: { visitId: string; system: string; initial: CaseData; onClose: () => void }) {
  const t = useTranslations(`caseTakingUi.${system}`)
  const tp = useTranslations('caseTakingUi.panel')
  const save = useSaveVisitCase()
  const [data, setData] = useState<CaseData>(initial)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setErrors({})
    try {
      await save.mutateAsync({ visitId, system, data })
      toast.success(tp('saved'))
      onClose()
    } catch (error) {
      setErrors(fieldErrors(error))
      toast.error(errorMessage(error, tp('saveFailed')))
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{tp('visitTitle', { system: t('title') })}</DialogTitle>
          <DialogDescription>{tp('draftNote')}</DialogDescription>
        </DialogHeader>
        <form className="space-y-6" onSubmit={submit} noValidate>
          <CaseForm system={system} scope="visit" value={data} onChange={setData} errors={errors} />
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
