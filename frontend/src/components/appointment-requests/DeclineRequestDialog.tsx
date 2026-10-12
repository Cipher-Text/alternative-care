'use client'

import { useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { identityError } from '@/components/identity/identityUtils'
import { useDeclineAppointmentRequest, useRefreshAppointmentRequests } from '@/lib/hooks/useAppointmentRequests'
import type { ClinicRequest } from '@/types/appointmentRequest'

const MIN = 3
const MAX = 500

interface Props {
  request: ClinicRequest | null
  onClose: () => void
}

/** Decline with a reason the patient will read. */
export function DeclineRequestDialog({ request, onClose }: Props) {
  return (
    <Dialog open={!!request} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent>{request && <DeclineForm key={request.id} request={request} onClose={onClose} />}</DialogContent>
    </Dialog>
  )
}

function DeclineForm({ request, onClose }: { request: ClinicRequest; onClose: () => void }) {
  const t = useTranslations('appointmentRequestsUi.decline')
  const decline = useDeclineAppointmentRequest()
  const refresh = useRefreshAppointmentRequests()
  const [reason, setReason] = useState('')
  const [notify, setNotify] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const valid = reason.trim().length >= MIN

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!valid) return setError(t('errors.reason', { min: MIN }))
    setError(null)
    try {
      await decline.mutateAsync({ id: request.id, reason: reason.trim(), notifySms: notify })
      toast.success(t('done'))
      onClose()
    } catch (err) {
      if (identityError(err).code === 'not_open') {
        toast.error(t('errors.notOpen'))
        refresh()
        return onClose()
      }
      setError(t('errors.generic'))
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{t('title')}</DialogTitle>
        <DialogDescription>{t('description', { name: request.requester.display_name })}</DialogDescription>
      </DialogHeader>
      <form onSubmit={submit} noValidate className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="dc-reason">{t('reason')}</Label>
          <Textarea id="dc-reason" rows={4} maxLength={MAX} value={reason} onChange={(e) => setReason(e.target.value)} aria-invalid={reason.length > 0 && !valid} disabled={decline.isLoading} />
          <p className="text-xs text-muted-foreground">{t('reasonHint', { min: MIN })}</p>
        </div>
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1" checked={notify} onChange={(e) => setNotify(e.target.checked)} disabled={decline.isLoading} />
          <span>
            {t('notify')}
            <span className="block text-muted-foreground">{t('notifyNote')}</span>
          </span>
        </label>
        {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">{error}</p>}
        <DialogFooter className="gap-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={decline.isLoading}>{t('back')}</Button>
          <Button type="submit" variant="destructive" disabled={decline.isLoading || !valid}>
            {decline.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('submit')}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
