import { getTranslations } from 'next-intl/server'
import { ExternalLink, Mail, MessageCircle } from 'lucide-react'
import { ContactForm } from '@/components/public/ContactForm'
import { getContactInfo } from '@/lib/contactInfo'
import { CONTACT_TOPICS, type ContactTopic } from '@/types/contact'

type SearchParams = Record<string, string | string[] | undefined>

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? ''
}

/** Server-rendered so the heading, intro and direct channels are in the HTML for search engines. */
export default async function ContactPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const [t, params] = await Promise.all([getTranslations('publicContactUi'), searchParams])
  const info = getContactInfo()

  const rawTopic = first(params.topic)
  const topic = (CONTACT_TOPICS as string[]).includes(rawTopic) ? (rawTopic as ContactTopic) : 'general'
  const practitioner = first(params.practitioner).toLowerCase().replace(/[^a-z0-9-]/g, '').slice(0, 80)
  const hasChannels = Boolean(info.email || info.whatsapp || info.facebook)

  const link = 'inline-flex items-center gap-2 text-sm font-medium text-emerald-700 hover:underline dark:text-emerald-400'

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-4 text-gray-700 dark:text-gray-300">{t('intro')}</p>

      {hasChannels && (
        <section className="mt-8" aria-labelledby="contact-channels">
          <h2 id="contact-channels" className="text-lg font-semibold text-gray-900 dark:text-white">{t('channelsTitle')}</h2>
          <ul className="mt-3 flex flex-col gap-3">
            {info.email && (
              <li>
                <a href={`mailto:${info.email}`} className={link}>
                  <Mail className="h-4 w-4" aria-hidden="true" />
                  {t('emailLink', { email: info.email })}
                </a>
              </li>
            )}
            {info.whatsapp && (
              <li>
                <a
                  href={`https://wa.me/${info.whatsapp}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
                >
                  <MessageCircle className="h-4 w-4" aria-hidden="true" />
                  {t('whatsappButton')}
                </a>
              </li>
            )}
            {info.facebook && (
              <li>
                <a href={info.facebook} target="_blank" rel="noopener noreferrer" className={link}>
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                  {t('facebookLink')}
                </a>
              </li>
            )}
          </ul>
        </section>
      )}

      <section className="mt-10 rounded-lg border border-gray-200 bg-card p-5 dark:border-slate-800 sm:p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{t('formTitle')}</h2>
        <ContactForm initialTopic={topic} practitioner={practitioner || undefined} />
      </section>
    </div>
  )
}
