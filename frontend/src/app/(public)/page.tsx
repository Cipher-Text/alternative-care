'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import {
  Pill,
  Stethoscope,
  Leaf,
  Sprout,
  FlaskConical,
  ArrowRight,
  ShieldCheck,
  Users2,
  CalendarClock,
  HeartHandshake,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { getPostLoginPath } from '@/lib/auth/redirects'
import { usePublicStats } from '@/lib/hooks/usePublicCatalog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const disciplines = [
  { value: 'homeopathy', icon: FlaskConical },
  { value: 'ayurveda', icon: Leaf },
  { value: 'unani', icon: Sprout },
  { value: 'herbal', icon: Stethoscope },
] as const

// A number is only shown once it is big enough to be a point in our favour; a small figure does
// more harm than good. Never invent or round up — these are live counts.
const STAT_MINIMUMS = {
  practitioners: 10,
  clinics: 10,
  medicines: 100,
  symptoms: 50,
  institutions: 50,
} as const

const STAT_LABEL_KEYS = {
  practitioners: 'statPractitioners',
  clinics: 'statClinics',
  medicines: 'statMedicines',
  symptoms: 'statSymptoms',
  institutions: 'statInstitutions',
} as const

export default function HomePage() {
  const t = useTranslations('publicHomeUi')
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)
  const { data: stats } = usePublicStats()

  useEffect(() => {
    if (hasHydrated && isAuthenticated && user) {
      router.replace(getPostLoginPath(user))
    }
  }, [hasHydrated, isAuthenticated, user, router])

  // Authenticated users are redirected above — avoid flashing marketing
  // content before that effect runs.
  if (!hasHydrated || (isAuthenticated && user)) {
    return null
  }

  const shownStats = stats
    ? (Object.keys(STAT_MINIMUMS) as Array<keyof typeof STAT_MINIMUMS>).filter(
        (key) => stats[key] >= STAT_MINIMUMS[key]
      )
    : []

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50 to-transparent dark:from-emerald-950/20 dark:to-transparent" />
        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-20 sm:py-28 text-center">
          <Badge variant="outline" className="mb-4">
            {t('heroBadge')}
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white">
            {t('heroTitle')}
          </h1>
          <p className="mt-6 text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            {t('heroSubtitle')}
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/register">
                {t('getStarted')} <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/pricing">{t('seePricing')}</Link>
            </Button>
            <Button asChild size="lg" variant="ghost">
              <Link href="/login">{t('signIn')}</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Live numbers, only the ones worth showing */}
      {shownStats.length >= 2 && stats && (
        <section className="border-y border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/50">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 flex flex-wrap justify-center gap-x-12 gap-y-6 text-center">
            {shownStats.map((key) => (
              <div key={key}>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats[key]}+</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t(STAT_LABEL_KEYS[key])}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Two doors */}
      <section className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-10">
          {t('doorsTitle')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-emerald-200 dark:border-emerald-900">
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center mb-2">
                <Pill className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
              </div>
              <CardTitle>{t('doorPractitionerTitle')}</CardTitle>
              <CardDescription>{t('doorPractitionerDesc')}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link href="/for-practitioners">
                  {t('doorPractitionerCta')} <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-2">
                <HeartHandshake className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              </div>
              <CardTitle className="flex items-center gap-2">
                {t('doorPatientTitle')}
                <Badge variant="secondary">{t('comingSoon')}</Badge>
              </CardTitle>
              <CardDescription>{t('doorPatientDesc')}</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Disciplines */}
      <section className="bg-gray-50 dark:bg-slate-900/50 border-y border-gray-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{t('disciplinesTitle')}</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">{t('disciplinesSubtitle')}</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {disciplines.map((d) => (
              <Card key={d.value} className="h-full">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center mb-2">
                    <d.icon className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
                  </div>
                  <CardTitle className="text-lg">{t(`disciplines.${d.value}.label`)}</CardTitle>
                  <CardDescription>{t(`disciplines.${d.value}.description`)}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{t('ctaTitle')}</h2>
        <p className="mt-4 text-gray-600 dark:text-gray-400">{t('ctaSubtitle')}</p>
        <div className="mt-8 grid gap-4 text-left sm:grid-cols-3">
          {[
            { icon: Users2, title: 'featurePatientsTitle', desc: 'featurePatientsDesc' },
            { icon: CalendarClock, title: 'featureAppointmentsTitle', desc: 'featureAppointmentsDesc' },
            { icon: ShieldCheck, title: 'featureSecurityTitle', desc: 'featureSecurityDesc' },
          ].map((f) => (
            <div key={f.title} className="flex items-start gap-3">
              <f.icon className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">{t(f.title)}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t(f.desc)}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-10">
          <Button asChild size="lg">
            <Link href="/register">
              {t('getStarted')} <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
