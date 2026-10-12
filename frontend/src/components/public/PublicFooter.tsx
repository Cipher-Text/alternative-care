import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { getContactInfo } from '@/lib/contactInfo'

const columns = [
  {
    title: 'colDirectory',
    links: [
      { key: 'navArticles', href: '/articles' },
      { key: 'navInstitutions', href: '/institutions' },
    ],
  },
  {
    title: 'colProduct',
    links: [
      { key: 'navPractitioners', href: '/for-practitioners' },
      { key: 'navPricing', href: '/pricing' },
      { key: 'signIn', href: '/login' },
    ],
  },
  {
    title: 'colCompany',
    links: [
      { key: 'navAbout', href: '/about' },
      { key: 'navContact', href: '/contact' },
      { key: 'navFaq', href: '/faq' },
      { key: 'navRefundPolicy', href: '/refund-policy' },
    ],
  },
  {
    title: 'colLegal',
    links: [
      { key: 'privacy', href: '/privacy' },
      { key: 'terms', href: '/terms' },
      { key: 'disclaimer', href: '/disclaimer' },
    ],
  },
] as const

export function PublicFooter({ directoryLaunched = false }: { directoryLaunched?: boolean }) {
  const t = useTranslations('publicShellUi')
  const facebook = getContactInfo().facebook
  const directoryLinks = directoryLaunched
    ? [{ key: 'navFindPractitioner', href: '/practitioners' } as const, ...columns[0].links]
    : columns[0].links
  const cols = [{ ...columns[0], links: directoryLinks }, ...columns.slice(1)]
  return (
    <footer className="border-t border-gray-200 dark:border-slate-800 bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          <div className="col-span-2 md:col-span-1">
            <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              AltCare
            </span>
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
              {t('footerTagline')}
            </p>
          </div>

          {cols.map((column) => (
            <div key={t(column.title)}>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {t(column.title)}
              </h3>
              <ul className="mt-3 space-y-2">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                      {t(link.key)}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 pt-6 border-t border-gray-200 dark:border-slate-800 text-sm text-gray-500 dark:text-gray-400">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>{t('rights', { year: new Date().getFullYear() })}</span>
            {facebook && (
              <a href={facebook} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 hover:text-gray-900 dark:hover:text-white">
                Facebook
              </a>
            )}
          </div>
        </div>
      </div>
    </footer>
  )
}
