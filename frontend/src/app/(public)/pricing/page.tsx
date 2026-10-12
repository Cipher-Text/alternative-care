'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
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

type Period = 'monthly' | 'yearly'

/** Percentage saved by paying yearly instead of 12 months; 0 when there is no saving or no yearly price. */
function yearlySavingPercent(plan: PublicPlan): number {
  if (plan.price_monthly === null || plan.price_yearly === null) return 0
  const monthly = Number(plan.price_monthly)
  if (monthly <= 0) return 0
  const percent = Math.round((1 - Number(plan.price_yearly) / (monthly * 12)) * 100)
  return percent > 0 ? percent : 0
}

function priceText(plan: PublicPlan, period: Period, t: T): { main: string; sub?: string } {
  if (plan.price_monthly === null) return { main: t('contactUs') }
  const monthly = Number(plan.price_monthly)
  if (monthly === 0) return { main: t('free') }

  const perMonth = t('perMonth', { currency: plan.currency, amount: monthly.toLocaleString() })
  if (period === 'monthly') return { main: perMonth }

  // Yearly view: show the yearly price, and what it works out to per month
  if (plan.price_yearly === null) return { main: perMonth, sub: t('noYearlyPrice') }
  const yearly = Number(plan.price_yearly)
  const saving = yearlySavingPercent(plan)
  const equivalent = t('perMonthEquivalent', {
    currency: plan.currency,
    amount: Math.round(yearly / 12).toLocaleString(),
  })
  return {
    main: t('perYear', { currency: plan.currency, amount: yearly.toLocaleString() }),
    sub: saving > 0 ? `${equivalent} · ${t('savePercent', { percent: saving })}` : equivalent,
  }
}

export default function PricingPage() {
  const t = useTranslations('publicInfoUi.pricing')
  const locale = useLocale()
  const { data } = usePublicPlans()
  const [period, setPeriod] = useState<Period>('monthly')
  const bestSaving = data ? Math.max(0, ...data.plans.map(yearlySavingPercent)) : 0

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
    {
      key: 'enterprise',
      name: t('fallbackEnterpriseName'),
      tagline: t('fallbackEnterpriseTagline'),
      features: [t('fallbackEnterpriseFeature1'), t('fallbackEnterpriseFeature2'), t('fallbackEnterpriseFeature3')],
    },
  ]

  const cards = data
    ? data.plans.map((plan, index) => ({
        key: plan.key,
        name: pick(locale, plan.name_en, plan.name_bn),
        tagline: pick(locale, plan.description_en ?? '', plan.description_bn),
        price: priceText(plan, period, t),
        features: featureLines(plan, data.catalog, t, locale),
        highlighted: index === 1,
        contactOnly: plan.price_monthly === null,
      }))
    : fallbackPlans.map((plan, index) => ({
        key: plan.key,
        name: plan.name,
        tagline: plan.tagline,
        price: { main: t('contactUs') } as { main: string; sub?: string },
        features: plan.features,
        highlighted: index === 1,
        contactOnly: plan.key === 'enterprise',
      }))

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-3 text-gray-600 dark:text-gray-400">
          {t('intro')}
        </p>

        {data && (
          <div className="mt-8 flex justify-center">
            <div
              role="group"
              aria-label={t('billingPeriod')}
              className="inline-flex items-center rounded-full border border-gray-200 dark:border-slate-700 p-1 bg-background"
            >
              {(['monthly', 'yearly'] as const).map((option) => (
                <button
                  key={option}
                  type="button"
                  aria-pressed={period === option}
                  onClick={() => setPeriod(option)}
                  className={cn(
                    'rounded-full px-5 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500',
                    period === option
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  )}
                >
                  {option === 'monthly' ? t('billingMonthly') : t('billingYearly')}
                  {option === 'yearly' && bestSaving > 0 && (
                    <span
                      className={cn(
                        'ml-2 rounded-full px-2 py-0.5 text-xs',
                        period === 'yearly' ? 'bg-white/20' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                      )}
                    >
                      {t('saveUpTo', { percent: bestSaving })}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
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
                {plan.contactOnly ? (
                  <Link href="/contact?topic=enterprise">{t('talkToUs')}</Link>
                ) : (
                  <Link href={`/register?plan=${plan.key}`}>{t('getStarted')}</Link>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
        {t.rich('billingHelp', {
          faq: () => <Link href="/faq" className="text-emerald-700 underline dark:text-emerald-400">{t('billingHelpFaq')}</Link>,
          refund: () => <Link href="/refund-policy" className="text-emerald-700 underline dark:text-emerald-400">{t('billingHelpRefund')}</Link>,
        })}
      </p>
    </div>
  )
}
