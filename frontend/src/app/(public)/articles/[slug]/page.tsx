import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getLocale, getTranslations } from 'next-intl/server'
import { AlertTriangle, ArrowLeft, Stethoscope } from 'lucide-react'
import { fetchPublicArticle, formatPublicDate, pickLocalized, youtubeThumb } from '@/lib/api/publicArticles'
import { ArticleMarkdown } from '@/components/public/ArticleMarkdown'
import { YouTubeFacade } from '@/components/public/YouTubeFacade'

function isPast(value: string | null): boolean {
  return !!value && new Date(value).getTime() < Date.now()
}

type Params = Promise<{ slug: string }>

const SITE = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params
  const article = await fetchPublicArticle(slug).catch(() => null)
  if (!article) return {}
  const locale = await getLocale()
  const t = await getTranslations('publicContentUi')
  const title = pickLocalized(locale, article.title_en, article.title_bn) ?? t('untitled')
  const description = pickLocalized(locale, article.summary_en, article.summary_bn) ?? undefined
  const image = article.kind === 'video' && article.youtube_id ? youtubeThumb(article.youtube_id) : undefined
  return {
    title,
    description,
    alternates: { canonical: `/articles/${article.slug}` },
    openGraph: {
      type: 'article',
      title,
      description,
      publishedTime: article.published_at ?? undefined,
      authors: [article.author_name],
      images: image ? [image] : undefined,
    },
  }
}

export default async function ArticlePage({ params }: { params: Params }) {
  const { slug } = await params
  const article = await fetchPublicArticle(slug)
  if (!article) notFound()

  const [locale, t] = await Promise.all([getLocale(), getTranslations('publicContentUi')])
  const title = pickLocalized(locale, article.title_en, article.title_bn) ?? t('untitled')
  const summary = pickLocalized(locale, article.summary_en, article.summary_bn)
  const body = pickLocalized(locale, article.body_en, article.body_bn)
  const isVideo = article.kind === 'video' && !!article.youtube_id
  const overdue = isPast(article.review_due_at)

  const url = `${SITE}/articles/${article.slug}`
  const jsonLd = isVideo
    ? {
        '@context': 'https://schema.org',
        '@type': 'VideoObject',
        name: title,
        description: summary ?? title,
        thumbnailUrl: youtubeThumb(article.youtube_id!),
        uploadDate: article.published_at ?? undefined,
        embedUrl: `https://www.youtube-nocookie.com/embed/${article.youtube_id}`,
        url,
      }
    : {
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: title,
        description: summary ?? undefined,
        datePublished: article.published_at ?? undefined,
        dateModified: article.reviewed_at ?? article.published_at ?? undefined,
        author: { '@type': 'Person', name: article.author_name },
        mainEntityOfPage: url,
      }

  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <script
        type="application/ld+json"
        // Escape "<" so article text can never terminate the script tag.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }}
      />
      <Link
        href="/articles"
        className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-emerald-700 dark:text-gray-400"
      >
        <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
        {t('breadcrumbBack')}
      </Link>

      <div className="mt-6 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
          {t(`discipline_${article.discipline}`)}
        </span>
        <span className="rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-300">
          {t(`evidence_${article.evidence_label}`)}
        </span>
      </div>

      <h1 className="mt-4 text-3xl font-bold text-gray-900 dark:text-white">{title}</h1>
      {summary && <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">{summary}</p>}
      <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
        {t('by', { author: article.author_name })}
        {article.published_at && <> · {t('published', { date: formatPublicDate(article.published_at, locale) })}</>}
      </p>

      {isVideo && (
        <div className="mt-6">
          <YouTubeFacade videoId={article.youtube_id!} title={title} />
        </div>
      )}

      <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
        <p className="font-semibold">{t('evidenceLabel')}: {t(`evidence_${article.evidence_label}`)}</p>
        <p className="mt-1">{t(`evidenceExplain_${article.evidence_label}`)}</p>
      </div>

      {overdue && (
        <div role="note" className="mt-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{t('overdueNotice')}</p>
        </div>
      )}

      {body && (
        <div className="mt-6">
          <ArticleMarkdown source={body} />
        </div>
      )}

      <div className="mt-10 space-y-1 border-t border-gray-200 pt-4 text-sm text-gray-600 dark:border-slate-800 dark:text-gray-400">
        <p>
          {article.reviewer_display && article.reviewed_at
            ? t('reviewedBy', { reviewer: article.reviewer_display, date: formatPublicDate(article.reviewed_at, locale) })
            : t('notYetReviewed')}
        </p>
        {article.review_due_at && <p>{t('nextReviewDue', { date: formatPublicDate(article.review_due_at, locale) })}</p>}
      </div>

      <div className="mt-6 flex gap-3 rounded-lg border border-gray-200 p-4 text-sm dark:border-slate-800">
        <Stethoscope className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
        <div>
          <p className="font-semibold text-gray-900 dark:text-white">{t('seeDoctorTitle')}</p>
          <p className="mt-1 text-gray-600 dark:text-gray-400">{t('seeDoctorBody')}</p>
        </div>
      </div>

      <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
        {t('disclaimer')}{' '}
        <Link href="/disclaimer" className="text-emerald-700 underline dark:text-emerald-400">
          {t('disclaimerLink')}
        </Link>
      </p>
    </article>
  )
}
