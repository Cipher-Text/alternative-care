'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { AlertTriangle, ArrowLeft, Eye, Loader2, Pencil } from 'lucide-react'
import {
  useArticle,
  useCreateArticle,
  useDeleteArticle,
  usePublishArticle,
  useReturnArticle,
  useSubmitArticle,
  useUnpublishArticle,
  useUpdateArticle,
} from '@/lib/hooks/useArticles'
import { useAuthStore } from '@/store/authStore'
import { useDateFormat } from '@/lib/i18n/date'
import { ArticleStatusBadge, OverdueBadge } from '@/components/content/ArticleStatusBadge'
import { MarkdownPreview } from '@/components/content/MarkdownPreview'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ARTICLE_DISCIPLINES,
  EVIDENCE_LABELS,
  type Article,
  type ArticleDiscipline,
  type ArticleInput,
  type ArticleKind,
  type EvidenceLabel,
} from '@/types/article'

interface FormState {
  kind: ArticleKind
  discipline: ArticleDiscipline
  evidence_label: EvidenceLabel
  title_en: string
  title_bn: string
  summary_en: string
  summary_bn: string
  body_en: string
  body_bn: string
  video_url: string
  slug: string
}

const EMPTY: FormState = {
  kind: 'article',
  discipline: 'general',
  evidence_label: 'general_info',
  title_en: '',
  title_bn: '',
  summary_en: '',
  summary_bn: '',
  body_en: '',
  body_bn: '',
  video_url: '',
  slug: '',
}

function fromArticle(a: Article): FormState {
  return {
    kind: a.kind,
    discipline: a.discipline,
    evidence_label: a.evidence_label,
    title_en: a.title_en ?? '',
    title_bn: a.title_bn ?? '',
    summary_en: a.summary_en ?? '',
    summary_bn: a.summary_bn ?? '',
    body_en: a.body_en ?? '',
    body_bn: a.body_bn ?? '',
    video_url: a.youtube_id ? `https://www.youtube.com/watch?v=${a.youtube_id}` : '',
    slug: a.slug,
  }
}

/** Pull the 11-character video id out of a YouTube link (or accept a bare id). */
export function parseYoutubeId(input: string): string | null {
  const value = input.trim()
  if (/^[\w-]{11}$/.test(value)) return value
  try {
    const url = new URL(value)
    const host = url.hostname.replace(/^www\.|^m\./, '')
    let id: string | null = null
    if (host === 'youtu.be') id = url.pathname.split('/')[1] ?? null
    else if (host === 'youtube.com' || host === 'youtube-nocookie.com') {
      const [, first, second] = url.pathname.split('/')
      if (url.pathname === '/watch') id = url.searchParams.get('v')
      else if (['embed', 'shorts', 'live', 'v'].includes(first)) id = second ?? null
    }
    return id && /^[\w-]{11}$/.test(id) ? id : null
  } catch {
    return null
  }
}

function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}

export function ArticleEditor({ articleId }: { articleId?: string }) {
  const t = useTranslations('contentAdminUi')
  const { data: article, isLoading, isError } = useArticle(articleId)

  if (articleId && isLoading) {
    return <div className="h-64 animate-pulse rounded-lg bg-muted" aria-busy="true" />
  }
  if (articleId && (isError || !article)) {
    return (
      <div className="space-y-4">
        <p role="alert" className="text-red-600">{t('notFound')}</p>
        <Button asChild variant="outline">
          <Link href="/content"><ArrowLeft className="mr-2 h-4 w-4" /> {t('backToList')}</Link>
        </Button>
      </div>
    )
  }
  // Remount on server updates (status change, save) so the form re-initialises from the saved article
  return <EditorForm key={article ? `${article.id}-${article.updated_at}` : 'new'} article={article} />
}

function EditorForm({ article }: { article?: Article }) {
  const t = useTranslations('contentAdminUi')
  const router = useRouter()
  const { fmt } = useDateFormat()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const [form, setForm] = useState<FormState>(article ? fromArticle(article) : EMPTY)
  const [preview, setPreview] = useState(false)
  const [lang, setLang] = useState<'en' | 'bn'>('en')
  const [publishOpen, setPublishOpen] = useState(false)
  const [returnOpen, setReturnOpen] = useState(false)
  const [reviewer, setReviewer] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [note, setNote] = useState('')

  const create = useCreateArticle()
  const update = useUpdateArticle()
  const remove = useDeleteArticle()
  const submit = useSubmitArticle()
  const publish = usePublishArticle()
  const returnIt = useReturnArticle()
  const unpublish = useUnpublishArticle()

  const status = article?.status
  const isAuthor = !article || article.author_id === user?.id
  const canEdit = !article || isAdmin || (isAuthor && status === 'draft')
  const busy =
    create.isLoading || update.isLoading || remove.isLoading || submit.isLoading ||
    publish.isLoading || returnIt.isLoading || unpublish.isLoading

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }))

  const videoId = form.kind === 'video' ? parseYoutubeId(form.video_url) : null

  const missing = [
    !(form.title_en.trim() || form.title_bn.trim()) && t('missing.title'),
    !(form.summary_en.trim() || form.summary_bn.trim()) && t('missing.summary'),
    form.kind === 'article' && !(form.body_en.trim() || form.body_bn.trim()) && t('missing.body'),
    form.kind === 'video' && !videoId && t('missing.video'),
  ].filter(Boolean) as string[]

  const payload = (): ArticleInput => {
    const data: ArticleInput = {
      kind: form.kind,
      discipline: form.discipline,
      evidence_label: form.evidence_label,
      title_en: form.title_en,
      title_bn: form.title_bn,
      summary_en: form.summary_en,
      summary_bn: form.summary_bn,
      body_en: form.body_en,
      body_bn: form.body_bn,
      video_url: form.kind === 'video' ? form.video_url : '',
    }
    // The address is optional; leave it out unless the author typed a new one
    const slug = form.slug.trim()
    if (slug && slug !== article?.slug) data.slug = slug
    return data
  }

  const save = async () => {
    try {
      if (article) await update.mutateAsync({ id: article.id, data: payload() })
      else {
        const created = await create.mutateAsync(payload())
        router.replace(`/content/${created.id}`)
      }
    } catch {
      /* the mutation's onError already showed the reason */
    }
  }

  const submitForReview = async () => {
    if (!article) return
    try {
      if (canEdit) await update.mutateAsync({ id: article.id, data: payload() })
      await submit.mutateAsync(article.id)
    } catch {
      /* toast already shown */
    }
  }

  const doPublish = async () => {
    if (!article) return
    try {
      await publish.mutateAsync({
        id: article.id,
        data: { reviewer_display: reviewer.trim(), ...(dueAt ? { review_due_at: dueAt } : {}) },
      })
      setPublishOpen(false)
    } catch {
      /* toast already shown */
    }
  }

  const doReturn = async () => {
    if (!article) return
    try {
      await returnIt.mutateAsync({ id: article.id, note: note.trim() })
      setReturnOpen(false)
      setNote('')
    } catch {
      /* toast already shown */
    }
  }

  const doDelete = async () => {
    if (!article || !window.confirm(t('confirmDelete'))) return
    try {
      await remove.mutateAsync(article.id)
      router.replace('/content')
    } catch {
      /* toast already shown */
    }
  }

  const guidance = (
    <Card className="border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/30">
      <CardContent className="flex gap-3 p-4">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" aria-hidden="true" />
        <div className="space-y-1 text-sm text-amber-950 dark:text-amber-100">
          <p className="font-semibold">{t('guidance.title')}</p>
          <ul className="list-disc space-y-0.5 pl-5">
            <li>{t('guidance.noDosing')}</li>
            <li>{t('guidance.evidence')}</li>
            <li>{t('guidance.review')}</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )

  const renderLang = (l: 'en' | 'bn') => {
    const body = form[`body_${l}`]
    return (
      <div className="space-y-4">
        <Field id={`title_${l}`} label={t('fields.title')}>
          <Input
            id={`title_${l}`}
            lang={l}
            maxLength={300}
            value={form[`title_${l}`]}
            onChange={(e) => set(`title_${l}`, e.target.value)}
          />
        </Field>
        <Field id={`summary_${l}`} label={t('fields.summary')} hint={t('fields.summaryHint')}>
          <Textarea
            id={`summary_${l}`}
            lang={l}
            rows={3}
            value={form[`summary_${l}`]}
            onChange={(e) => set(`summary_${l}`, e.target.value)}
          />
        </Field>
        {form.kind === 'article' && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <Label htmlFor={`body_${l}`}>{t('fields.body')}</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPreview((p) => !p)}
                aria-pressed={preview}
              >
                {preview ? <Pencil className="mr-1.5 h-4 w-4" /> : <Eye className="mr-1.5 h-4 w-4" />}
                {preview ? t('fields.edit') : t('fields.preview')}
              </Button>
            </div>
            {preview ? (
              <div lang={l} className="min-h-[200px] rounded-md border bg-background p-4">
                {body.trim() ? <MarkdownPreview source={body} /> : (
                  <p className="text-muted-foreground">{t('fields.previewEmpty')}</p>
                )}
              </div>
            ) : (
              <Textarea
                id={`body_${l}`}
                lang={l}
                rows={16}
                className="font-mono text-sm"
                value={body}
                onChange={(e) => set(`body_${l}`, e.target.value)}
              />
            )}
            <p className="text-sm text-muted-foreground">{t('fields.bodyHint')}</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Button asChild variant="ghost" size="sm" className="-ml-3">
            <Link href="/content"><ArrowLeft className="mr-1.5 h-4 w-4" /> {t('backToList')}</Link>
          </Button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {article ? t('editTitle') : t('newTitle')}
          </h1>
          {article && (
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <ArticleStatusBadge status={article.status} />
              {article.review_overdue && <OverdueBadge />}
              {isAdmin && <span>{t('byAuthor', { name: article.author_name })}</span>}
              {article.published_at && <span>{t('publishedOn', { date: fmt(article.published_at, 'MMM d, yyyy') })}</span>}
            </div>
          )}
        </div>
      </div>

      {guidance}

      {article?.review_note && status === 'draft' && (
        <Card role="alert" className="border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/30">
          <CardContent className="space-y-1 p-4 text-red-950 dark:text-red-100">
            <p className="font-semibold">{t('returnedTitle')}</p>
            <p className="whitespace-pre-wrap">{article.review_note}</p>
          </CardContent>
        </Card>
      )}

      {article && status === 'published' && (
        <Card>
          <CardContent className="space-y-1 p-4 text-sm">
            <p>
              <span className="font-medium">{t('reviewedBy')}:</span> {article.reviewer_display}
              {article.reviewed_at && <> ({fmt(article.reviewed_at, 'MMM d, yyyy')})</>}
            </p>
            {article.review_due_at && (
              <p>
                <span className="font-medium">{t('reviewDue')}:</span> {fmt(article.review_due_at, 'MMM d, yyyy')}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {!canEdit && (
        <p className="rounded-md border bg-muted p-3 text-sm">
          {status === 'in_review' ? t('readOnlyInReview') : t('readOnlyPublished')}
        </p>
      )}

      <fieldset disabled={!canEdit || busy} className="space-y-6 min-w-0">
        <Card>
          <CardContent className="grid gap-4 p-4 sm:grid-cols-2">
            <Field id="kind" label={t('fields.kind')}>
              <Select value={form.kind} onValueChange={(v) => set('kind', v as ArticleKind)} disabled={!canEdit}>
                <SelectTrigger id="kind"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="article">{t('kind.article')}</SelectItem>
                  <SelectItem value="video">{t('kind.video')}</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field id="discipline" label={t('fields.discipline')}>
              <Select value={form.discipline} onValueChange={(v) => set('discipline', v as ArticleDiscipline)} disabled={!canEdit}>
                <SelectTrigger id="discipline"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {ARTICLE_DISCIPLINES.map((d) => (
                    <SelectItem key={d} value={d}>{t(`discipline.${d}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <div className="sm:col-span-2">
              <Field id="evidence" label={t('fields.evidence')} hint={t(`evidenceMeaning.${form.evidence_label}`)}>
                <Select value={form.evidence_label} onValueChange={(v) => set('evidence_label', v as EvidenceLabel)} disabled={!canEdit}>
                  <SelectTrigger id="evidence"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {EVIDENCE_LABELS.map((e) => (
                      <SelectItem key={e} value={e}>{t(`evidence.${e}`)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            </div>
            {form.kind === 'video' && (
              <div className="space-y-3 sm:col-span-2">
                <Field id="video_url" label={t('fields.youtube')} hint={t('fields.youtubeHint')}>
                  <Input
                    id="video_url"
                    inputMode="url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={form.video_url}
                    onChange={(e) => set('video_url', e.target.value)}
                  />
                </Field>
                {form.video_url.trim() && !videoId && (
                  <p role="alert" className="text-sm text-red-600">{t('fields.youtubeInvalid')}</p>
                )}
                {videoId && (
                  <div className="aspect-video w-full max-w-xl overflow-hidden rounded-lg border">
                    <iframe
                      src={`https://www.youtube-nocookie.com/embed/${videoId}`}
                      title={t('fields.videoPreview')}
                      loading="lazy"
                      className="h-full w-full"
                      allow="encrypted-media; picture-in-picture"
                      referrerPolicy="strict-origin-when-cross-origin"
                      allowFullScreen
                    />
                  </div>
                )}
              </div>
            )}
            <div className="sm:col-span-2">
              <Field id="slug" label={t('fields.slug')} hint={t('fields.slugHint')}>
                <Input
                  id="slug"
                  value={form.slug}
                  placeholder="my-article-title"
                  pattern="[a-z0-9]+(-[a-z0-9]+)*"
                  onChange={(e) => set('slug', e.target.value.toLowerCase())}
                />
              </Field>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <Tabs value={lang} onValueChange={(v) => setLang(v as 'en' | 'bn')}>
              <TabsList>
                <TabsTrigger value="en">{t('tabEn')}</TabsTrigger>
                <TabsTrigger value="bn">{t('tabBn')}</TabsTrigger>
              </TabsList>
              <p className="mt-3 text-sm text-muted-foreground">{t('oneLanguageEnough')}</p>
              <TabsContent value="en" className="mt-4">{renderLang('en')}</TabsContent>
              <TabsContent value="bn" className="mt-4">{renderLang('bn')}</TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </fieldset>

      {/* Workflow action bar */}
      <div className="sticky bottom-0 -mx-1 flex flex-wrap items-center gap-2 border-t bg-background/95 px-1 py-3 backdrop-blur">
        {canEdit && (
          <Button onClick={save} disabled={busy} className="h-10">
            {(create.isLoading || update.isLoading) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t('actions.saveDraft')}
          </Button>
        )}
        {article && status === 'draft' && canEdit && (
          <Button variant="secondary" onClick={submitForReview} disabled={busy || missing.length > 0} className="h-10">
            {t('actions.submit')}
          </Button>
        )}
        {article && isAdmin && status === 'in_review' && (
          <>
            <Button onClick={() => setPublishOpen(true)} disabled={busy} className="h-10">
              {t('actions.publish')}
            </Button>
            <Button variant="outline" onClick={() => setReturnOpen(true)} disabled={busy} className="h-10">
              {t('actions.returnToAuthor')}
            </Button>
          </>
        )}
        {article && isAdmin && status === 'published' && (
          <Button variant="outline" onClick={() => unpublish.mutate(article.id)} disabled={busy} className="h-10">
            {t('actions.unpublish')}
          </Button>
        )}
        {article && status === 'draft' && canEdit && (
          <Button variant="destructive" onClick={doDelete} disabled={busy} className="h-10 sm:ml-auto">
            {t('actions.delete')}
          </Button>
        )}
      </div>
      {article && status === 'draft' && canEdit && missing.length > 0 && (
        <p className="text-sm text-muted-foreground">{t('missing.prefix', { items: missing.join(', ') })}</p>
      )}

      <Dialog open={publishOpen} onOpenChange={setPublishOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t('publishDialog.title')}</DialogTitle>
            <DialogDescription>{t('publishDialog.description')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Field id="reviewer" label={t('publishDialog.reviewer')} hint={t('publishDialog.reviewerHint')}>
              <Input
                id="reviewer"
                value={reviewer}
                maxLength={255}
                placeholder="Dr. A. Rahman, BHMS"
                onChange={(e) => setReviewer(e.target.value)}
              />
            </Field>
            <Field id="due" label={t('publishDialog.dueAt')} hint={t('publishDialog.dueAtHint')}>
              <Input id="due" type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
            </Field>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPublishOpen(false)}>{t('actions.cancel')}</Button>
            <Button onClick={doPublish} disabled={reviewer.trim().length < 2 || publish.isLoading}>
              {t('actions.publish')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={returnOpen} onOpenChange={setReturnOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t('returnDialog.title')}</DialogTitle>
            <DialogDescription>{t('returnDialog.description')}</DialogDescription>
          </DialogHeader>
          <Field id="note" label={t('returnDialog.note')}>
            <Textarea id="note" rows={4} maxLength={2000} value={note} onChange={(e) => setNote(e.target.value)} />
          </Field>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReturnOpen(false)}>{t('actions.cancel')}</Button>
            <Button onClick={doReturn} disabled={note.trim().length < 3 || returnIt.isLoading}>
              {t('actions.returnToAuthor')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
