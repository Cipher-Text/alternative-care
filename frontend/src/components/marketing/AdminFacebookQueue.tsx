'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { Copy, ExternalLink, Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { Pager, serverPage, usePager } from '@/components/shared/Pager'
import { useDateFormat } from '@/lib/i18n/date'
import {
  useAdminFacebookQueue,
  useDraftFacebookPost,
  useMarkFacebookPosted,
  useRejectFacebookRequest,
} from '@/lib/hooks/useMarketing'
import { CommentDialog } from './CommentDialog'
import { FbStatusBadge } from './FbStatusBadge'
import { PostLink } from './PostLink'
import type { AdminFacebookRequest, FbStatus } from '@/types/marketing'

const PAGE_SIZE = 20
const MIN_DRAFT = 20
const TABS: Record<string, FbStatus[]> = {
  needsDraft: ['requested'],
  waiting: ['drafted'],
  ready: ['approved'],
  posted: ['posted'],
  closed: ['rejected', 'cancelled'],
}
type TabKey = keyof typeof TABS

/** Mirrors the server rule: https, and a Facebook host (facebook.com, fb.com, fb.watch and subdomains). */
export function isFacebookPostUrl(value: string): boolean {
  try {
    const u = new URL(value.trim())
    if (u.protocol !== 'https:') return false
    const host = u.hostname.toLowerCase()
    return ['facebook.com', 'fb.com', 'fb.watch'].some((d) => host === d || host.endsWith(`.${d}`))
  } catch {
    return false
  }
}

function CopyButton({ text }: { text: string }) {
  const t = useTranslations('marketingUi.admin')
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(t('copied'))
    } catch {
      toast.error(t('copyFailed'))
    }
  }
  return (
    <Button type="button" variant="outline" size="sm" className="h-10 sm:h-8" onClick={copy}>
      <Copy className="mr-2 h-4 w-4" aria-hidden="true" />
      {t('copy')}
    </Button>
  )
}

function QueueItem({ item }: { item: AdminFacebookRequest }) {
  const t = useTranslations('marketingUi.admin')
  const { fmt } = useDateFormat()
  const draft = useDraftFacebookPost()
  const reject = useRejectFacebookRequest()
  const posted = useMarkFacebookPosted()
  const [text, setText] = useState(item.draft_text ?? '')
  const [url, setUrl] = useState('')
  const [rejectOpen, setRejectOpen] = useState(false)

  const canDraft = item.status === 'requested' || item.status === 'drafted'
  const draftValid = text.trim().length >= MIN_DRAFT
  const urlValid = isFacebookPostUrl(url)
  const busy = draft.isLoading || reject.isLoading || posted.isLoading

  return (
    <li className="space-y-4 rounded-lg border p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold">{item.tenant_name}</p>
          <p className="text-sm text-muted-foreground">
            {t('requestedBy', { name: item.requester_name, date: fmt(item.created_at, 'MMM d, yyyy') })}
          </p>
        </div>
        <FbStatusBadge status={item.status} />
      </div>

      <div className="space-y-2 text-sm">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{t('doctorNote')}</p>
          <p className="whitespace-pre-wrap">{item.doctor_note || t('noNote')}</p>
        </div>
        {item.doctor_comment && (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3 dark:border-amber-700 dark:bg-amber-950/30">
            <p className="text-xs font-medium">{t('doctorComment')}</p>
            <p className="whitespace-pre-wrap">{item.doctor_comment}</p>
          </div>
        )}
        {item.status === 'rejected' && item.reject_reason && (
          <div>
            <p className="text-xs font-medium text-muted-foreground">{t('rejectReason')}</p>
            <p className="whitespace-pre-wrap">{item.reject_reason}</p>
          </div>
        )}
        {item.profile_path ? (
          <Link
            href={item.profile_path}
            target="_blank"
            rel="noopener"
            className="inline-flex items-center gap-1 font-medium text-emerald-700 underline underline-offset-2 dark:text-emerald-400"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            {t('profileLink')}
          </Link>
        ) : (
          <p className="text-amber-700 dark:text-amber-300">{t('profileNotLive')}</p>
        )}
      </div>

      {canDraft && (
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor={`draft-${item.id}`}>{t('draftLabel')}</Label>
            <Textarea
              id={`draft-${item.id}`}
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              aria-invalid={text.length > 0 && !draftValid}
            />
            <p className="text-xs text-muted-foreground">{t('draftHint', { min: MIN_DRAFT })}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              className="h-10"
              disabled={!draftValid || busy}
              onClick={() => draft.mutate({ id: item.id, text: text.trim() })}
            >
              {draft.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('saveDraft')}
            </Button>
            <Button variant="outline" className="h-10" disabled={busy} onClick={() => setRejectOpen(true)}>
              {t('reject')}
            </Button>
          </div>
          <CommentDialog
            open={rejectOpen}
            onClose={() => setRejectOpen(false)}
            title={t('rejectTitle')}
            description={t('rejectDescription')}
            label={t('rejectLabel')}
            confirmLabel={t('rejectConfirm')}
            destructive
            pending={reject.isLoading}
            onSubmit={(reason) => reject.mutateAsync({ id: item.id, reason })}
          />
        </div>
      )}

      {item.status === 'approved' && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium">{t('approvedText')}</p>
            {item.approved_text && <CopyButton text={item.approved_text} />}
          </div>
          <blockquote className="whitespace-pre-wrap rounded-lg border-l-4 border-emerald-500 bg-muted/40 p-4 text-sm">
            {item.approved_text}
          </blockquote>
          <div className="space-y-1.5">
            <Label htmlFor={`url-${item.id}`}>{t('postUrlLabel')}</Label>
            <Input
              id={`url-${item.id}`}
              type="url"
              inputMode="url"
              placeholder="https://www.facebook.com/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              aria-invalid={url.length > 0 && !urlValid}
            />
            {url.length > 0 && !urlValid && (
              <p role="alert" className="text-xs text-red-600">{t('postUrlInvalid')}</p>
            )}
          </div>
          <Button
            className="h-10"
            disabled={!urlValid || busy}
            onClick={() => posted.mutate({ id: item.id, url: url.trim() })}
          >
            {posted.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('markPosted')}
          </Button>
        </div>
      )}

      {item.status === 'posted' && item.post_url && <PostLink url={item.post_url} />}
    </li>
  )
}

export function AdminFacebookQueue() {
  const t = useTranslations('marketingUi.admin')
  const [tab, setTab] = useState<TabKey>('needsDraft')
  const pager = usePager(PAGE_SIZE, tab)
  const queue = useAdminFacebookQueue(TABS[tab], pager.offset, PAGE_SIZE + 1)
  const { items, hasNext } = serverPage(queue.data, PAGE_SIZE)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('queueTitle')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={tab} onValueChange={(v) => setTab(v)}>
          <TabsList className="flex h-auto flex-wrap justify-start">
            {Object.keys(TABS).map((k) => (
              <TabsTrigger key={k} value={k}>{t(`tabs.${k}`)}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {queue.isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
          </div>
        ) : queue.error ? (
          <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
        ) : items.length === 0 && pager.page === 1 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{t('empty')}</p>
        ) : (
          <>
            <ul className="space-y-4">
              {items.map((item) => (
                // keyed by id + status so local editor state resets when a request moves on
                <QueueItem key={`${item.id}:${item.status}`} item={item} />
              ))}
            </ul>
            <Pager
              page={pager.page}
              pageSize={PAGE_SIZE}
              count={items.length}
              hasNext={hasNext}
              onPageChange={pager.setPage}
              isLoading={queue.isFetching}
              noun="requests"
            />
          </>
        )}
      </CardContent>
    </Card>
  )
}
