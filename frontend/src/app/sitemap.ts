import type { MetadataRoute } from 'next'

const PUBLIC_PATHS = ['/', '/about', '/for-practitioners', '/pricing', '/institutions', '/privacy', '/terms', '/disclaimer']

export default function sitemap(): MetadataRoute.Sitemap {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')
  return PUBLIC_PATHS.map((path) => ({ url: `${base}${path === '/' ? '' : path}` }))
}
