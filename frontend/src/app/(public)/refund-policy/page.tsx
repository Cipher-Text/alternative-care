// DRAFT policy text: needs owner/legal review before launch (refund terms are defaults, not decisions)
import Link from 'next/link'
import { getLocale, getTranslations } from 'next-intl/server'

const LAST_UPDATED = '2026-10-13'
const SECTIONS = [1, 2, 3, 4, 5, 6] as const

export default async function RefundPolicyPage() {
  const t = await getTranslations('publicHelpUi.refund')
  const tc = await getTranslations('publicLegalUi')
  const locale = await getLocale()
  const date = new Intl.DateTimeFormat(locale === 'bn' ? 'bn-BD' : 'en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${LAST_UPDATED}T00:00:00Z`))

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t('updated', { date })}</p>
      <p className="mt-6 text-gray-700 dark:text-gray-300">{t('intro')}</p>

      {SECTIONS.map((n) => (
        <section key={n} className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t(`s${n}Title`)}</h2>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            {t(`s${n}Body`)}
            {n === 6 && (
              <Link className="underline" href="/contact?topic=billing">
                {t('s6Link')}
              </Link>
            )}
          </p>
        </section>
      ))}

      <p className="mt-12 text-xs text-muted-foreground">{tc('draftNote')}</p>
    </div>
  )
}
