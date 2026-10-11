import Link from 'next/link'
import { getLocale, getTranslations } from 'next-intl/server'
import { Play } from 'lucide-react'
import { ARTICLE_DISCIPLINES, type PublicArticleItem } from '@/types/article'
import { fetchPublicArticles, formatPublicDate, pickLocalized, youtubeThumb } from '@/lib/api/publicArticles'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 12
const KINDS = ['article', 'video'] as const

type SearchParams = Promise<{ kind?: string; discipline?: string; page?: string }>

function href(params: { kind?: string; discipline?: string; page?: number }) {
  const qs = new URLSearchParams()
  if (params.kind) qs.set('kind', params.kind)
  if (params.discipline) qs.set('discipline', params.discipline)
  if (params.page && params.page > 1) qs.set('page', String(params.page))
  const s = qs.toString()
  return s ? `/articles?${s}` : '/articles'
}

export default async function ArticlesPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams
  const kind = KINDS.find((k) => k === sp.kind)
  const discipline = ARTICLE_DISCIPLINES.find((d) => d === sp.discipline)
  const page = Math.max(1, Math.floor(Number(sp.page)) || 1)

  const [locale, t] = await Promise.all([getLocale(), getTranslations('publicContentUi')])
  const fetched = await fetchPublicArticles({
    kind,
    discipline,
    limit: PAGE_SIZE + 1,
    offset: (page - 1) * PAGE_SIZE,
  })
  const hasNext = fetched.length > PAGE_SIZE
  const items = fetched.slice(0, PAGE_SIZE)
  const filtered = Boolean(kind || discipline)

  const chip = (active: boolean) =>
    cn(
      'rounded-full border px-3 py-1 text-sm transition-colors',
      active
        ? 'border-emerald-600 bg-emerald-600 text-white'
        : 'border-gray-300 text-gray-700 hover:border-emerald-600 dark:border-slate-700 dark:text-gray-300'
    )

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>

      <div className="mt-8 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('filterKind')}:</span>
          <Link href={href({ discipline })} className={chip(!kind)}>{t('kindAll')}</Link>
          <Link href={href({ kind: 'article', discipline })} className={chip(kind === 'article')}>{t('kindArticle')}</Link>
          <Link href={href({ kind: 'video', discipline })} className={chip(kind === 'video')}>{t('kindVideo')}</Link>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('filterDiscipline')}:</span>
          <Link href={href({ kind })} className={chip(!discipline)}>{t('disciplineAll')}</Link>
          {ARTICLE_DISCIPLINES.map((d) => (
            <Link key={d} href={href({ kind, discipline: d })} className={chip(discipline === d)}>
              {t(`discipline_${d}`)}
            </Link>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        <div className="mt-12 rounded-lg border border-dashed border-gray-300 p-12 text-center dark:border-slate-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {filtered || page > 1 ? t('emptyFiltered') : t('emptyTitle')}
          </h2>
          {!filtered && page === 1 && (
            <p className="mt-2 text-gray-600 dark:text-gray-400">{t('emptyBody')}</p>
          )}
          {(filtered || page > 1) && (
            <Link href="/articles" className="mt-4 inline-block text-emerald-700 underline dark:text-emerald-400">
              {t('clearFilters')}
            </Link>
          )}
        </div>
      ) : (
        <ul className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <ArticleCard key={item.slug} item={item} locale={locale} t={t} />
          ))}
        </ul>
      )}

      {(page > 1 || hasNext) && (
        <nav aria-label={t('pagination')} className="mt-10 flex items-center justify-between">
          {page > 1 ? (
            <Link href={href({ kind, discipline, page: page - 1 })} className={chip(false)} rel="prev">
              {t('previous')}
            </Link>
          ) : (
            <span />
          )}
          <span className="text-sm text-gray-500 dark:text-gray-400">{t('pageLabel', { page })}</span>
          {hasNext ? (
            <Link href={href({ kind, discipline, page: page + 1 })} className={chip(false)} rel="next">
              {t('next')}
            </Link>
          ) : (
            <span />
          )}
        </nav>
      )}
    </div>
  )
}

function ArticleCard({
  item,
  locale,
  t,
}: {
  item: PublicArticleItem
  locale: string
  t: Awaited<ReturnType<typeof getTranslations>>
}) {
  const title = pickLocalized(locale, item.title_en, item.title_bn) ?? t('untitled')
  const summary = pickLocalized(locale, item.summary_en, item.summary_bn)
  const isVideo = item.kind === 'video' && item.youtube_id
  return (
    <li className="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-card dark:border-slate-800">
      {isVideo && (
        <Link href={`/articles/${item.slug}`} className="relative block aspect-video bg-black" tabIndex={-1} aria-hidden="true">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={youtubeThumb(item.youtube_id!)} alt="" loading="lazy" className="h-full w-full object-cover" />
          <span className="absolute inset-0 flex items-center justify-center bg-black/20">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600 text-white">
              <Play className="h-5 w-5 translate-x-0.5" fill="currentColor" />
            </span>
          </span>
        </Link>
      )}
      <div className="flex flex-1 flex-col p-5">
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            {t(`discipline_${item.discipline}`)}
          </span>
          <span className="rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-300">
            {t(`evidence_${item.evidence_label}`)}
          </span>
          {isVideo && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-700 dark:bg-slate-800 dark:text-gray-300">
              {t('video')}
            </span>
          )}
        </div>
        <h2 className="mt-3 text-lg font-semibold text-gray-900 dark:text-white">
          <Link href={`/articles/${item.slug}`} className="hover:text-emerald-700 dark:hover:text-emerald-400">
            {title}
          </Link>
        </h2>
        {summary && <p className="mt-2 line-clamp-3 text-sm text-gray-600 dark:text-gray-400">{summary}</p>}
        <p className="mt-auto pt-4 text-xs text-gray-500 dark:text-gray-400">
          {t('by', { author: item.author_name })}
          {item.published_at && <> · {formatPublicDate(item.published_at, locale)}</>}
        </p>
      </div>
    </li>
  )
}
