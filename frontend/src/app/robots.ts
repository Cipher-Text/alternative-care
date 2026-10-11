import type { MetadataRoute } from 'next'

// The marketing pages are indexable; everything behind sign-in is not.
const PRIVATE_PATHS = [
  '/login', '/register', '/forgot-password', '/reset-password', '/verify-email',
  '/dashboard', '/patients', '/appointments', '/prescriptions', '/payments', '/medicines',
  '/symptoms', '/pharmacies', '/content', '/profile', '/settings', '/admin',
]

export default function robots(): MetadataRoute.Robots {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')
  return {
    rules: { userAgent: '*', allow: '/', disallow: PRIVATE_PATHS },
    sitemap: `${base}/sitemap.xml`,
  }
}
