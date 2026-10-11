import { getTranslations } from 'next-intl/server'

const SECTION_COUNTS = { privacy: 6, terms: 6, disclaimer: 4 } as const

export type LegalKind = keyof typeof SECTION_COUNTS

/** Shared layout for the privacy policy, terms of use and medical disclaimer. */
export async function LegalPage({ kind }: { kind: LegalKind }) {
  const t = await getTranslations(`publicLegalUi.${kind}`)
  const tc = await getTranslations('publicLegalUi')
  const email = process.env.NEXT_PUBLIC_CONTACT_EMAIL

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t('updated')}</p>
      <p className="mt-6 text-gray-700 dark:text-gray-300">{t('intro')}</p>

      {Array.from({ length: SECTION_COUNTS[kind] }, (_, i) => i + 1).map((n) => (
        <section key={n} className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t(`s${n}Title`)}</h2>
          <p className="mt-2 text-gray-700 dark:text-gray-300">{t(`s${n}Body`)}</p>
        </section>
      ))}

      {email && (
        <section className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{tc('contactTitle')}</h2>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            {tc('contactBody')}
            <a className="underline" href={`mailto:${email}`}>
              {email}
            </a>
          </p>
        </section>
      )}

      <p className="mt-12 text-xs text-muted-foreground">{tc('draftNote')}</p>
    </div>
  )
}
