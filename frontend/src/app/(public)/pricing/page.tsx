'use client'

import Link from 'next/link'
import { Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePublicPlans } from '@/lib/hooks/usePlans'
import type { CatalogItem, PublicPlan } from '@/types/plans'

// Shown only if the plans API cannot be reached, so the page never renders empty.
const FALLBACK_PLANS: Array<{ key: string; name: string; tagline: string; features: string[] }> = [
  {
    key: 'free',
    name: 'Free',
    tagline: 'For solo practitioners getting started',
    features: ['Patient records & appointments', 'Prescription builder', 'Medicine & symptom library'],
  },
  {
    key: 'plus',
    name: 'Plus',
    tagline: 'For growing clinics',
    features: ['Everything in Free', 'Payments & invoicing', 'SMS/email integrations'],
  },
  {
    key: 'pro',
    name: 'Pro',
    tagline: 'For established practices',
    features: ['Everything in Plus', 'AI-assisted lookups (coming soon)', 'Priority support'],
  },
]

const CORE_FEATURES = ['Patient records & appointments', 'Prescription builder', 'Medicine & symptom library']

/** Turn a plan's entitlements into human-readable bullet points, in catalog order. */
function featureLines(plan: PublicPlan, catalog: CatalogItem[]): string[] {
  const lines = [...CORE_FEATURES]
  for (const item of catalog) {
    const value = plan.entitlements.find((e) => e.key === item.key)
    if (!value) continue
    if (item.kind === 'feature') {
      if (value.enabled) lines.push(item.label_en)
    } else if (value.limit === null) {
      lines.push(`${item.label_en}: unlimited`)
    } else if (value.limit > 0) {
      lines.push(`${item.label_en}: ${value.limit.toLocaleString()}`)
    }
  }
  return lines
}

function priceText(plan: PublicPlan): { main: string; sub?: string } {
  if (plan.price_monthly === null) return { main: 'Contact us' }
  const monthly = Number(plan.price_monthly)
  const main = monthly === 0 ? 'Free' : `${plan.currency} ${monthly.toLocaleString()}/month`
  const sub =
    plan.price_yearly !== null && monthly > 0
      ? `or ${plan.currency} ${Number(plan.price_yearly).toLocaleString()}/year`
      : undefined
  return { main, sub }
}

export default function PricingPage() {
  const { data } = usePublicPlans()

  const cards = data
    ? data.plans.map((plan, index) => ({
        key: plan.key,
        name: plan.name_en,
        tagline: plan.description_en ?? '',
        price: priceText(plan),
        features: featureLines(plan, data.catalog),
        highlighted: index === 1,
      }))
    : FALLBACK_PLANS.map((plan, index) => ({
        key: plan.key,
        name: plan.name,
        tagline: plan.tagline,
        price: { main: 'Contact us' } as { main: string; sub?: string },
        features: plan.features,
        highlighted: index === 1,
      }))

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Pricing</h1>
        <p className="mt-3 text-gray-600 dark:text-gray-400">
          Every account starts on Free while we review it. Pick the plan you are interested in and
          tell us more during sign-up, or sign in to see what is available for your account.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {cards.map((plan) => (
          <Card key={plan.key} className={plan.highlighted ? 'border-emerald-500 shadow-md' : ''}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                {plan.highlighted && <Badge>Popular</Badge>}
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
                <Link href={`/register?plan=${plan.key}`}>Get Started</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
