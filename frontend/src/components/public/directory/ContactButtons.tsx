'use client'

import { Phone, MessageCircle } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { recordContactEvent } from '@/lib/api/publicDirectory'

/** Call / WhatsApp links. The tap is counted in the background and never delays the link. */
export function ContactButtons({
  slug,
  telHref,
  whatsappHref,
}: {
  slug: string
  telHref: string | null
  whatsappHref: string | null
}) {
  const t = useTranslations('publicPractitionersUi')
  if (!telHref && !whatsappHref) return null
  const base =
    'inline-flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition-colors'
  return (
    <div className="flex flex-wrap gap-3">
      {telHref && (
        <a
          href={telHref}
          onClick={() => recordContactEvent(slug, 'call')}
          className={`${base} bg-emerald-600 text-white hover:bg-emerald-700`}
        >
          <Phone className="h-4 w-4" aria-hidden="true" />
          {t('call')}
        </a>
      )}
      {whatsappHref && (
        <a
          href={whatsappHref}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => recordContactEvent(slug, 'whatsapp')}
          className={`${base} border border-emerald-600 text-emerald-700 hover:bg-emerald-50 dark:text-emerald-300 dark:hover:bg-emerald-950`}
        >
          <MessageCircle className="h-4 w-4" aria-hidden="true" />
          {t('whatsapp')}
        </a>
      )}
    </div>
  )
}
