import Link from 'next/link'
import { getLocale, getTranslations } from 'next-intl/server'
import { Button } from '@/components/ui/button'
import type { PublicPlan, PublicPlansResponse } from '@/types/plans'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function fetchPlans(): Promise<PublicPlan[] | null> {
  try {
    const res = await fetch(`${API_BASE}/plans`, { next: { revalidate: 300 } })
    if (!res.ok) return null
    return ((await res.json()) as PublicPlansResponse).plans
  } catch {
    return null
  }
}

interface Item {
  id: string
  link?: { href: string; label: string }
}

interface Group {
  key: string
  items: Item[]
}

// One source for the questions: the page and the FAQPage JSON-LD are both built from this.
const GROUPS: Group[] = [
  { key: 'start', items: [{ id: 'start' }, { id: 'free', link: { href: '/pricing', label: 'pricingLink' } }] },
  { key: 'plans', items: [{ id: 'list' }, { id: 'prices' }, { id: 'saving' }, { id: 'enterprise' }] },
  { key: 'paying', items: [{ id: 'how' }, { id: 'renew' }, { id: 'remind' }, { id: 'receipt' }, { id: 'who' }] },
  { key: 'ends', items: [{ id: 'end' }, { id: 'delete' }, { id: 'renew' }, { id: 'lower' }, { id: 'clinic' }] },
  { key: 'credits', items: [{ id: 'allowance' }, { id: 'packs' }, { id: 'expire' }, { id: 'provider' }] },
  { key: 'facebook', items: [{ id: 'what' }, { id: 'howMany' }, { id: 'approve' }] },
  {
    key: 'safety',
    items: [
      { id: 'privacy', link: { href: '/privacy', label: 'privacyLink' } },
      { id: 'med', link: { href: '/disclaimer', label: 'medLink' } },
      { id: 'report', link: { href: '/contact', label: 'reportLink' } },
    ],
  },
]

export default async function FaqPage() {
  const t = await getTranslations('publicHelpUi.faq')
  const locale = await getLocale()
  const plans = await fetchPlans()

  const money = (amount: number, currency: string) =>
    `${currency === 'BDT' ? '৳' : `${currency} `}${amount.toLocaleString('en-US')}`

  // Prices and the yearly saving come from the live plan data; null means "say nothing specific".
  const paid = (plans ?? []).filter((p) => p.price_monthly !== null && Number(p.price_monthly) > 0)
  const priceLines = paid.map((p) => {
    const name = (locale === 'bn' && p.name_bn) || p.name_en
    const monthly = money(Number(p.price_monthly), p.currency)
    return p.price_yearly !== null && Number(p.price_yearly) > 0
      ? t('groups.plans.pricesLineYearly', { name, monthly, yearly: money(Number(p.price_yearly), p.currency) })
      : t('groups.plans.pricesLine', { name, monthly })
  })
  const freeMonths = paid
    .filter((p) => p.price_yearly !== null && Number(p.price_yearly) > 0)
    .map((p) => Math.round(12 - Number(p.price_yearly) / Number(p.price_monthly)))
  const months = freeMonths.length ? Math.min(...freeMonths) : 0

  const answerFor = (group: string, id: string): string | null => {
    if (group === 'plans' && id === 'prices') {
      return priceLines.length
        ? t('groups.plans.pricesA', { lines: priceLines.join('; ') })
        : t('groups.plans.pricesFallback')
    }
    if (group === 'plans' && id === 'saving') {
      return months >= 1 ? t('groups.plans.savingA', { months }) : null
    }
    return t(`groups.${group}.${id}A`)
  }

  const groups = GROUPS.map((g) => ({
    key: g.key,
    title: t(`groups.${g.key}.title`),
    items: g.items.flatMap((item) => {
      const answer = answerFor(g.key, item.id)
      return answer === null
        ? []
        : [{ ...item, question: t(`groups.${g.key}.${item.id}Q`), answer }]
    }),
  }))

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: groups.flatMap((g) =>
      g.items.map((i) => ({
        '@type': 'Question',
        name: i.question,
        acceptedAnswer: { '@type': 'Answer', text: i.answer },
      }))
    ),
  }

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
      <script
        type="application/ld+json"
        // Escape "<" so the data can never terminate the script tag.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }}
      />
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">{t('subtitle')}</p>

      {groups.map((g) => (
        <section key={g.key} className="mt-10">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{g.title}</h2>
          <div className="mt-3 divide-y divide-gray-200 dark:divide-slate-800 border-y border-gray-200 dark:border-slate-800">
            {g.items.map((item) => (
              <details key={item.id} className="group py-3">
                <summary className="cursor-pointer list-none font-medium text-gray-900 dark:text-white marker:hidden [&::-webkit-details-marker]:hidden">
                  {item.question}
                </summary>
                <p className="mt-2 text-gray-700 dark:text-gray-300">{item.answer}</p>
                {item.link && (
                  <p className="mt-2 text-sm">
                    <Link className="underline" href={item.link.href}>
                      {t(`groups.${g.key}.${item.link.label}`)}
                    </Link>
                  </p>
                )}
              </details>
            ))}
          </div>
        </section>
      ))}

      <section className="mt-12 rounded-lg border border-gray-200 dark:border-slate-800 p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t('helpTitle')}</h2>
        <p className="mt-2 text-gray-700 dark:text-gray-300">{t('helpBody')}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/contact?topic=billing">{t('helpContact')}</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/refund-policy">{t('helpRefund')}</Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
