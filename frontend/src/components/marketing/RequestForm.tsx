'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useCreateFacebookRequest } from '@/lib/hooks/useMarketing'

const MAX = 1000

/** Rendered only when the summary says `can_request`; the server re-checks every rule anyway. */
export function RequestForm() {
  const t = useTranslations('marketingUi.form')
  const [note, setNote] = useState('')
  const create = useCreateFacebookRequest()

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    create.mutate(note.trim() || undefined, { onSuccess: () => setNote('') })
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{t('title')}</CardTitle>
        <p className="text-sm text-muted-foreground">{t('intro')}</p>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="fb-note">{t('noteLabel')}</Label>
            <Textarea
              id="fb-note"
              rows={4}
              maxLength={MAX}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={t('notePlaceholder')}
            />
            <p className="text-xs text-muted-foreground">{t('noteCount', { count: note.length, max: MAX })}</p>
          </div>
          <Button type="submit" className="h-10" disabled={create.isLoading}>
            {create.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('submit')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
