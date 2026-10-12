import type { MetadataRoute } from 'next'
import { fetchPublicArticles } from '@/lib/api/publicArticles'
import { fetchPractitionerSlugs } from '@/lib/api/publicDirectory'

const PUBLIC_PATHS = ['/', '/about', '/for-practitioners', '/pricing', '/institutions', '/articles', '/verification', '/privacy', '/terms', '/disclaimer']

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')
  const routes: MetadataRoute.Sitemap = PUBLIC_PATHS.map((path) => ({ url: `${base}${path === '/' ? '' : path}` }))

  // fetchPublicArticles swallows API failures and returns [], leaving only the static routes.
  const articles: Awaited<ReturnType<typeof fetchPublicArticles>> = []
  for (let offset = 0; offset < 5000; offset += 200) {
    const batch = await fetchPublicArticles({ limit: 200, offset })
    articles.push(...batch)
    if (batch.length < 200) break
  }
  // Returns [] until the directory launches (and on failure), so nothing thin is advertised.
  const slugs = await fetchPractitionerSlugs()
  const directory: MetadataRoute.Sitemap = slugs.length
    ? [{ url: `${base}/practitioners` }, ...slugs.map((slug) => ({ url: `${base}/practitioners/${slug}` }))]
    : []
  return [
    ...routes,
    ...directory,
    ...articles.map((a) => ({
      url: `${base}/articles/${a.slug}`,
      lastModified: a.published_at ? new Date(a.published_at) : undefined,
    })),
  ]
}
