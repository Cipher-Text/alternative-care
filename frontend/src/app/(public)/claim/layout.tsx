import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { getTranslations } from 'next-intl/server'

// A page the clinic hands out by code: not for search engines, not in the sitemap or navigation.
export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('identityUi.claim')
  return { title: t('metaTitle'), robots: { index: false, follow: false } }
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
