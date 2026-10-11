'use client'

import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePublicPlans } from '@/lib/hooks/usePlans'
import type { CatalogItem, PublicPlan } from '@/types/plans'

type T = ReturnType<typeof useTranslations>

/** Name/description pick the Bengali field when the locale is bn and the API supplied one. */
function pick(locale: string, en: string, bn: string | null | undefined): string {
  return locale === 'bn' && bn ? bn : en
}

/** Turn a plan's entitlements into human-readable bullet points, in catalog order. */
function featureLines(plan: PublicPlan, catalog: CatalogItem[], t: T, locale: string): string[] {
  const lines = [t('coreRecords'), t('coreBuilder'), t('coreLibrary')]
  for (const item of catalog) {
    const value = plan.entitlements.find((e) => e.key === item.key)
    if (!value) continue
    const label = pick(locale, item.label_en, item.label_bn)
    if (item.kind === 'feature') {
      if (value.enabled) lines.push(label)
    } else if (value.limit === null) {
      lines.push(t('unlimited', { label }))
    } else if (value.limit > 0) {
      lines.push(t('limited', { label, value: value.limit.toLocaleString() }))
    }
  }
  return lines
}

function priceText(plan: PublicPlan, t: T): { main: string; sub?: string } {
  if (plan.price_monthly === null) return { main: t('contactUs') }
  const monthly = Number(plan.price_monthly)
  const main =
    monthly === 0
      ? t('free')
      : t('perMonth', { currency: plan.currency, amount: monthly.toLocaleString() })
  const sub =
    plan.price_yearly !== null && monthly > 0
      ? t('perYear', { currency: plan.currency, amount: Number(plan.price_yearly).toLocaleString() })
      : undefined
  return { main, sub }
}

export default function PricingPage() {
  const t = useTranslations('publicInfoUi.pricing')
  const locale = useLocale()
  const { data } = usePublicPlans()

  // Shown only if the plans API cannot be reached, so the page never renders empty.
  const fallbackPlans = [
    {
      key: 'free',
      name: t('fallbackFreeName'),
      tagline: t('fallbackFreeTagline'),
      features: [t('coreRecords'), t('coreBuilder'), t('coreLibrary')],
    },
    {
      key: 'plus',
      name: t('fallbackPlusName'),
      tagline: t('fallbackPlusTagline'),
      features: [t('fallbackPlusFeature1'), t('fallbackPlusFeature2'), t('fallbackPlusFeature3')],
    },
    {
      key: 'pro',
      name: t('fallbackProName'),
      tagline: t('fallbackProTagline'),
      features: [t('fallbackProFeature1'), t('fallbackProFeature2'), t('fallbackProFeature3')],
    },
  ]

  const cards = data
    ? data.plans.map((plan, index) => ({
        key: plan.key,
        name: pick(locale, plan.name_en, plan.name_bn),
        tagline: pick(locale, plan.description_en ?? '', plan.description_bn),
        price: priceText(plan, t),
        features: featureLines(plan, data.catalog, t, locale),
        highlighted: index === 1,
      }))
    : fallbackPlans.map((plan, index) => ({
        key: plan.key,
        name: plan.name,
        tagline: plan.tagline,
        price: { main: t('contactUs') } as { main: string; sub?: string },
        features: plan.features,
        highlighted: index === 1,
      }))

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-3 text-gray-600 dark:text-gray-400">
          {t('intro')}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {cards.map((plan) => (
          <Card key={plan.key} className={plan.highlighted ? 'border-emerald-500 shadow-md' : ''}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                {plan.highlighted && <Badge>{t('popular')}</Badge>}
              </div>
              <CardDescription>{plan.tagline}</CardDescription>
              <div className="pt-2">
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{plan.price.main}</p>
                {plan.price.sub && <p className="text-xs text-muted-foreground">{plan.price.sub}</p>}
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                    <span className="text-gray-600 dark:text-gray-400">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button asChild className="w-full mt-6" variant={plan.highlighted ? 'default' : 'outline'}>
                <Link href={`/register?plan=${plan.key}`}>{t('getStarted')}</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
