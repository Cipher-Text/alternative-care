import Link from 'next/link'
import { getTranslations } from 'next-intl/server'

const SECTIONS = [1, 2, 3, 4, 5, 6] as const

export default async function VerificationPage() {
  const t = await getTranslations('publicPractitionersUi.verification')
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-6 text-gray-700 dark:text-gray-300">{t('intro')}</p>

      {SECTIONS.map((n) => (
        <section key={n} className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t(`s${n}Title`)}</h2>
          <p className="mt-2 text-gray-700 dark:text-gray-300">{t(`s${n}Body`)}</p>
          {n === 6 && (
            <p className="mt-2">
              <Link href="/about" className="text-emerald-700 underline dark:text-emerald-400">{t('contactLink')}</Link>
            </p>
          )}
        </section>
      ))}

      <p className="mt-10">
        <Link href="/practitioners" className="rounded-md bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700">
          {t('browseLink')}
        </Link>
      </p>
    </div>
  )
}
