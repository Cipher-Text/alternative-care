'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAddDiagnosis } from '@/lib/hooks/useHealth'
import { localToday } from '@/components/health/localDate'

/** Record a diagnosis on the patient's history (name, optional ICD code, date). */
export function AddDiagnosisDialog({ patientId, onClose }: { patientId: string; onClose: () => void }) {
  const t = useTranslations('patientDiagnosisUi')
  const add = useAddDiagnosis(patientId)
  const [description, setDescription] = useState('')
  const [icd, setIcd] = useState('')
  const [date, setDate] = useState(localToday())

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!description.trim()) return
    try {
      await add.mutateAsync({ description: description.trim(), icd_code: icd.trim() || undefined, diagnosed_at: date })
      onClose()
    } catch {
      // the hook shows the error
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>{t('title')}</DialogTitle>
            <DialogDescription>{t('description')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="dx-description">{t('name')}</Label>
            <Input id="dx-description" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={500} autoFocus required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="dx-icd">{t('icd')}</Label>
              <Input id="dx-icd" value={icd} onChange={(e) => setIcd(e.target.value)} maxLength={20} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dx-date">{t('date')}</Label>
              <Input id="dx-date" type="date" max={localToday()} value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>{t('cancel')}</Button>
            <Button type="submit" disabled={!description.trim() || add.isLoading}>
              {add.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
