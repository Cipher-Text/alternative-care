'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  description: string
  label: string
  confirmLabel: string
  destructive?: boolean
  pending: boolean
  /** Resolves when the server accepted it; the dialog then closes. A rejection keeps it open. */
  onSubmit: (text: string) => Promise<unknown>
}

const MIN = 3
const MAX = 1000

/** A dialog with one required text field (≥3 chars): the doctor's change request and staff's reject reason. */
export function CommentDialog({
  open, onClose, title, description, label, confirmLabel, destructive, pending, onSubmit,
}: Props) {
  const t = useTranslations('marketingUi.dialog')
  const [text, setText] = useState('')
  const valid = text.trim().length >= MIN

  const close = () => {
    setText('')
    onClose()
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!valid || pending) return
    try {
      await onSubmit(text.trim())
      close()
    } catch {
      /* the mutation already showed the server's message */
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) close() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} noValidate className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="comment-text">{label}</Label>
            <Textarea
              id="comment-text"
              rows={4}
              maxLength={MAX}
              value={text}
              onChange={(e) => setText(e.target.value)}
              aria-invalid={text.length > 0 && !valid}
            />
            <p className="text-xs text-muted-foreground">{t('minHint', { min: MIN })}</p>
          </div>
          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" className="h-10" onClick={close}>
              {t('back')}
            </Button>
            <Button
              type="submit"
              variant={destructive ? 'destructive' : 'default'}
              className="h-10"
              disabled={!valid || pending}
            >
              {pending && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {confirmLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
