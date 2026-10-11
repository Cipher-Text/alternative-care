import Link from 'next/link'
import { getTranslations } from 'next-intl/server'
import {
  ArrowRight,
  Users2,
  CalendarClock,
  FileText,
  CreditCard,
  Pill,
  ShieldCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const features = [
  { icon: Users2, key: 'patients' },
  { icon: CalendarClock, key: 'appointments' },
  { icon: FileText, key: 'prescriptions' },
  { icon: Pill, key: 'medicines' },
  { icon: CreditCard, key: 'payments' },
  { icon: ShieldCheck, key: 'security' },
] as const

export default async function ForPractitionersPage() {
  const t = await getTranslations('publicInfoUi.practitioners')
  return (
    <div>
      <section className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          {t('title')}
        </h1>
        <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
          {t('intro')}
        </p>
        <div className="mt-8">
          <Button asChild size="lg">
            <Link href="/register">
              {t('getStarted')} <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card key={feature.key}>
              <CardHeader>
                <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center mb-2">
                  <feature.icon className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
                </div>
                <CardTitle className="text-lg">{t(`${feature.key}Title`)}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600 dark:text-gray-400">
                {t(`${feature.key}Body`)}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
