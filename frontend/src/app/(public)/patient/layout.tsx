import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { getTranslations } from 'next-intl/server'

// A personal page: not for search engines, not in the sitemap.
export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('patientPortalUi')
  return { title: t('metaTitle'), robots: { index: false, follow: false } }
}

export default function Layout({ children }: { children: ReactNode }) {
  return children
}
