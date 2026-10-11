import type { PublicArticle, PublicArticleItem } from '@/types/article'

/** Server-side fetchers for the public reading pages (plain fetch so Next can cache and revalidate). */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function fetchPublicArticles(params: {
  kind?: string
  discipline?: string
  limit: number
  offset: number
}): Promise<PublicArticleItem[]> {
  const qs = new URLSearchParams()
  if (params.kind) qs.set('kind', params.kind)
  if (params.discipline) qs.set('discipline', params.discipline)
  qs.set('limit', String(params.limit))
  qs.set('offset', String(params.offset))
  try {
    const res = await fetch(`${API_BASE}/public/articles?${qs}`, { next: { revalidate: 300 } })
    if (!res.ok) return []
    return (await res.json()) as PublicArticleItem[]
  } catch {
    return []
  }
}

/** Returns null when the article does not exist (or is unpublished). Throws on other failures. */
export async function fetchPublicArticle(slug: string): Promise<PublicArticle | null> {
  const res = await fetch(`${API_BASE}/public/articles/${encodeURIComponent(slug)}`, { next: { revalidate: 300 } })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Failed to load article (${res.status})`)
  return (await res.json()) as PublicArticle
}

export function youtubeThumb(id: string): string {
  return `https://i.ytimg.com/vi/${id}/hqdefault.jpg`
}

export function pickLocalized(locale: string, en: string | null, bn: string | null): string | null {
  const first = locale === 'bn' ? bn : en
  const second = locale === 'bn' ? en : bn
  return first?.trim() ? first : second?.trim() ? second : null
}

export function formatPublicDate(value: string | null, locale: string): string {
  if (!value) return ''
  return new Intl.DateTimeFormat(locale === 'bn' ? 'bn-BD' : 'en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(value))
}
