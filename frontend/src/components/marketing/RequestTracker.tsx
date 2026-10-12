'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Check, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import {
  useApproveFacebookRequest,
  useCancelFacebookRequest,
  useRequestFacebookChanges,
} from '@/lib/hooks/useMarketing'
import { CommentDialog } from './CommentDialog'
import { FbStatusBadge } from './FbStatusBadge'
import { PostLink } from './PostLink'
import type { FacebookRequest, FbStatus } from '@/types/marketing'

const STEPS = ['requested', 'drafted', 'approved', 'posted'] as const

function Steps({ status }: { status: FbStatus }) {
  const t = useTranslations('marketingUi.steps')
  const current = Math.max(0, STEPS.indexOf(status as (typeof STEPS)[number]))
  return (
    <ol className="grid grid-cols-4 gap-2" aria-label={t('label')}>
      {STEPS.map((s, i) => {
        const done = i < current || status === 'posted'
        const active = i === current && status !== 'posted'
        return (
          <li key={s} aria-current={active ? 'step' : undefined} className="flex flex-col items-center gap-1 text-center">
            <span
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border text-sm font-semibold',
                done && 'border-emerald-600 bg-emerald-600 text-white',
                active && 'border-primary bg-primary text-primary-foreground',
                !done && !active && 'text-muted-foreground'
              )}
            >
              {done ? <Check className="h-4 w-4" aria-hidden="true" /> : i + 1}
            </span>
            <span className={cn('text-xs', active ? 'font-semibold' : 'text-muted-foreground')}>{t(s)}</span>
          </li>
        )
      })}
    </ol>
  )
}

/** The clinic's one open request: where it is, and what the doctor can do next. */
export function RequestTracker({ request }: { request: FacebookRequest }) {
  const t = useTranslations('marketingUi.tracker')
  const [changesOpen, setChangesOpen] = useState(false)
  const approve = useApproveFacebookRequest()
  const cancel = useCancelFacebookRequest()
  const changes = useRequestFacebookChanges()
  const busy = approve.isLoading || cancel.isLoading || changes.isLoading

  const cancelButton = (
    <Button
      variant="outline"
      className="h-10"
      disabled={busy}
      onClick={() => { if (window.confirm(t('cancelConfirm'))) cancel.mutate(request.id) }}
    >
      {t('cancel')}
    </Button>
  )

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-wrap items-center gap-2 text-lg">
          {t('title')}
          <FbStatusBadge status={request.status} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <Steps status={request.status} />

        {request.status === 'requested' && (
          <div className="space-y-3">
            <p className="text-sm font-medium">{t('requestedText')}</p>
            {request.doctor_comment && (
              <div className="rounded-lg border bg-muted/40 p-3 text-sm">
                <p className="text-xs font-medium text-muted-foreground">{t('yourComment')}</p>
                <p className="whitespace-pre-wrap">{request.doctor_comment}</p>
              </div>
            )}
            {cancelButton}
          </div>
        )}

        {request.status === 'drafted' && (
          <div className="space-y-4">
            <div role="note" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-100">
              {t('nothingPosted')}
            </div>
            <p className="text-sm text-muted-foreground">{t('draftIntro')}</p>
            <blockquote className="whitespace-pre-wrap rounded-lg border-l-4 border-emerald-500 bg-muted/40 p-4 text-sm">
              {request.draft_text}
            </blockquote>
            <div className="flex flex-wrap gap-2">
              <Button className="h-10" disabled={busy} onClick={() => approve.mutate(request.id)}>
                {approve.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                {t('approve')}
              </Button>
              <Button variant="outline" className="h-10" disabled={busy} onClick={() => setChangesOpen(true)}>
                {t('askChanges')}
              </Button>
              {cancelButton}
            </div>
            <CommentDialog
              open={changesOpen}
              onClose={() => setChangesOpen(false)}
              title={t('changesTitle')}
              description={t('changesDescription')}
              label={t('changesLabel')}
              confirmLabel={t('changesSend')}
              pending={changes.isLoading}
              onSubmit={(comment) => changes.mutateAsync({ id: request.id, comment })}
            />
          </div>
        )}

        {request.status === 'approved' && (
          <div className="space-y-3">
            <p className="text-sm font-medium">{t('approvedText')}</p>
            <blockquote className="whitespace-pre-wrap rounded-lg border-l-4 border-emerald-500 bg-muted/40 p-4 text-sm">
              {request.approved_text}
            </blockquote>
          </div>
        )}

        {request.status === 'posted' && (
          <div className="space-y-3">
            <p className="text-sm font-medium">{t('postedText')}</p>
            {request.post_url && <PostLink url={request.post_url} />}
          </div>
        )}

        {request.status === 'rejected' && (
          <div className="space-y-1 text-sm">
            <p className="font-medium">{t('rejectedText')}</p>
            {request.reject_reason && <p className="whitespace-pre-wrap text-muted-foreground">{request.reject_reason}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
