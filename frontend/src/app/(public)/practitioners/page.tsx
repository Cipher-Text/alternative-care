import type { Metadata } from 'next'
import Link from 'next/link'
import { getLocale, getTranslations } from 'next-intl/server'
import { MapPin } from 'lucide-react'
import type { PublicPractitionerItem } from '@/types/directory'
import { fetchPractitioners } from '@/lib/api/publicDirectory'
import { pickLocalized } from '@/lib/api/publicArticles'
import { DIRECTORY_DISCIPLINES, formatFee, isDirectoryDiscipline } from '@/lib/directoryFormat'
import { VerifiedBadge } from '@/components/public/directory/VerifiedBadge'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 12

type SearchParams = Promise<{ discipline?: string; q?: string; page?: string }>

function href(params: { discipline?: string; q?: string; page?: number }) {
  const qs = new URLSearchParams()
  if (params.discipline) qs.set('discipline', params.discipline)
  if (params.q) qs.set('q', params.q)
  if (params.page && params.page > 1) qs.set('page', String(params.page))
  const s = qs.toString()
  return s ? `/practitioners?${s}` : '/practitioners'
}

function parse(sp: Awaited<SearchParams>) {
  const discipline = DIRECTORY_DISCIPLINES.find((d) => d === sp.discipline)
  const q = (sp.q ?? '').trim().slice(0, 80) || undefined
  const page = Math.max(1, Math.floor(Number(sp.page)) || 1)
  return { discipline, q, page }
}

export async function generateMetadata({ searchParams }: { searchParams: SearchParams }): Promise<Metadata> {
  const { discipline, q, page } = parse(await searchParams)
  const [t, list] = await Promise.all([getTranslations('publicMetaUi.directory'), fetchPractitioners({ limit: 1 })])
  return {
    title: t('title'),
    description: t('description'),
    alternates: { canonical: '/practitioners' },
    // Teaser (not launched) and filtered/search/paged views should not be indexed.
    robots: !list.launched || q || discipline || page > 1 ? { index: false, follow: true } : undefined,
  }
}

export default async function PractitionersPage({ searchParams }: { searchParams: SearchParams }) {
  const { discipline, q, page } = parse(await searchParams)
  const [locale, t] = await Promise.all([getLocale(), getTranslations('publicPractitionersUi')])
  const data = await fetchPractitioners({
    discipline,
    q,
    limit: PAGE_SIZE + 1,
    offset: (page - 1) * PAGE_SIZE,
  })

  if (!data.launched) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('teaserTitle')}</h1>
        <p className="mt-4 text-gray-600 dark:text-gray-400">{t('teaserBody')}</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/articles" className="rounded-md bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700">
            {t('teaserArticles')}
          </Link>
          <Link href="/for-practitioners" className="rounded-md border border-emerald-600 px-5 py-2.5 text-sm font-semibold text-emerald-700 hover:bg-emerald-50 dark:text-emerald-300 dark:hover:bg-emerald-950">
            {t('teaserListed')}
          </Link>
        </div>
        <p className="mt-6 text-sm">
          <Link href="/verification" className="text-emerald-700 underline dark:text-emerald-400">{t('verifiedHelp')}</Link>
        </p>
      </div>
    )
  }

  const hasNext = data.items.length > PAGE_SIZE
  const items = data.items.slice(0, PAGE_SIZE)
  const filtered = Boolean(discipline || q)

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

      <form action="/practitioners" method="get" role="search" className="mt-6 flex max-w-xl gap-2">
        {discipline && <input type="hidden" name="discipline" value={discipline} />}
        <label htmlFor="dir-q" className="sr-only">{t('searchLabel')}</label>
        <input id="dir-q" name="q" defaultValue={q} maxLength={80} placeholder={t('searchPlaceholder')} className="block w-full rounded-md border border-gray-300 bg-background px-3 py-2 text-sm dark:border-slate-700" />
        <button type="submit" className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">{t('searchButton')}</button>
      </form>

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('filterDiscipline')}:</span>
        <Link href={href({ q })} className={chip(!discipline)}>{t('disciplineAll')}</Link>
        {DIRECTORY_DISCIPLINES.map((d) => (
          <Link key={d} href={href({ q, discipline: d })} className={chip(discipline === d)}>
            {t(`discipline_${d}`)}
          </Link>
        ))}
      </div>

      {items.length === 0 ? (
        <div className="mt-12 rounded-lg border border-dashed border-gray-300 p-12 text-center dark:border-slate-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('emptyFiltered')}</h2>
          {(filtered || page > 1) && (
            <Link href="/practitioners" className="mt-4 inline-block text-emerald-700 underline dark:text-emerald-400">
              {t('clearFilters')}
            </Link>
          )}
        </div>
      ) : (
        <ul className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <PractitionerCard key={item.slug} item={item} locale={locale} t={t} />
          ))}
        </ul>
      )}

      {(page > 1 || hasNext) && (
        <nav aria-label={t('pagination')} className="mt-10 flex items-center justify-between">
          {page > 1 ? (
            <Link href={href({ q, discipline, page: page - 1 })} className={chip(false)} rel="prev">{t('previous')}</Link>
          ) : (
            <span />
          )}
          <span className="text-sm text-gray-500 dark:text-gray-400">{t('pageLabel', { page })}</span>
          {hasNext ? (
            <Link href={href({ q, discipline, page: page + 1 })} className={chip(false)} rel="next">{t('next')}</Link>
          ) : (
            <span />
          )}
        </nav>
      )}
    </div>
  )
}

function languageLabel(code: string, t: Awaited<ReturnType<typeof getTranslations>>): string {
  return code === 'en' || code === 'bn' ? t(`lang_${code}`) : code
}

function PractitionerCard({
  item,
  locale,
  t,
}: {
  item: PublicPractitionerItem
  locale: string
  t: Awaited<ReturnType<typeof getTranslations>>
}) {
  const headline = pickLocalized(locale, item.headline_en, item.headline_bn)
  const district = pickLocalized(locale, item.district_en, item.district_bn)
  return (
    <li className="flex flex-col rounded-lg border border-gray-200 bg-card p-5 dark:border-slate-800">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          <Link href={`/practitioners/${item.slug}`} className="hover:text-emerald-700 dark:hover:text-emerald-400">
            {item.display_name}
          </Link>
        </h2>
        <VerifiedBadge />
      </div>
      {item.clinic_name && <p className="text-sm text-gray-600 dark:text-gray-400">{item.clinic_name}</p>}
      {headline && <p className="mt-2 line-clamp-2 text-sm text-gray-700 dark:text-gray-300">{headline}</p>}

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {item.disciplines.map((d) => (
          <span key={d} className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            {isDirectoryDiscipline(d) ? t(`discipline_${d}`) : d}
          </span>
        ))}
      </div>

      <div className="mt-3 space-y-1 text-sm text-gray-600 dark:text-gray-400">
        {district && (
          <p className="flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            {district}
          </p>
        )}
        {item.languages.length > 0 && <p>{item.languages.map((l) => languageLabel(l, t)).join(', ')}</p>}
        {item.years_of_experience != null && <p>{t('experienceYears', { count: item.years_of_experience })}</p>}
        {item.fee_bdt != null && <p>{t('fee', { amount: formatFee(item.fee_bdt) })}</p>}
        <p>{t(`availability_${item.availability}`)}</p>
      </div>

      <Link href={`/practitioners/${item.slug}`} className="mt-auto pt-4 text-sm font-semibold text-emerald-700 hover:underline dark:text-emerald-400">
        {t('viewProfile')}
      </Link>
    </li>
  )
}
