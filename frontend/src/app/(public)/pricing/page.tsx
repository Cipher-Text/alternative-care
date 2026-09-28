import Link from 'next/link'
import { Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const plans = [
  {
    name: 'Free',
    tagline: 'For solo practitioners getting started',
    features: [
      'Patient records & appointments',
      'Prescription builder',
      'Global medicine & symptom library',
    ],
  },
  {
    name: 'Plus',
    tagline: 'For growing clinics',
    features: [
      'Everything in Free',
      'Payments & invoicing',
      'SMS/email integrations',
    ],
    highlighted: true,
  },
  {
    name: 'Pro',
    tagline: 'For established practices',
    features: [
      'Everything in Plus',
      'AI-assisted lookups (coming soon)',
      'Priority support',
    ],
  },
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Pricing</h1>
        <p className="mt-3 text-gray-600 dark:text-gray-400">
          Plans are tailored to your clinic during onboarding. Sign in to see what&apos;s
          available for your account, or get started to talk to us.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.name} className={plan.highlighted ? 'border-emerald-500 shadow-md' : ''}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                {plan.highlighted && <Badge>Popular</Badge>}
              </div>
              <CardDescription>{plan.tagline}</CardDescription>
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
                <Link href="/login">Get Started</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
