'use client'

import { ExternalLink } from 'lucide-react'
import { useTranslations } from 'next-intl'

/** Opens the Facebook post in a new tab. Only rendered with a URL the server stored. */
export function PostLink({ url }: { url: string }) {
  const t = useTranslations('marketingUi')
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 underline underline-offset-2 hover:text-emerald-800 dark:text-emerald-400"
    >
      <ExternalLink className="h-4 w-4" aria-hidden="true" />
      {t('viewPost')}
    </a>
  )
}
