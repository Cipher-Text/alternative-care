'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import {
  Search,
  Pill,
  Stethoscope,
  GraduationCap,
  Leaf,
  Sprout,
  FlaskConical,
  ArrowRight,
  ShieldCheck,
  Users2,
  CalendarClock,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { getPostLoginPath } from '@/lib/auth/redirects'
import { usePublicMedicines, usePublicSymptoms, usePublicInstitutions } from '@/lib/hooks/usePublicCatalog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const disciplines = [
  { value: 'homeopathy', icon: FlaskConical },
  { value: 'ayurveda', icon: Leaf },
  { value: 'unani', icon: Sprout },
  { value: 'herbal', icon: Stethoscope },
] as const

function isDiscipline(value: string): value is (typeof disciplines)[number]['value'] {
  return disciplines.some((d) => d.value === value)
}

function formatCount(count: number, cap: number) {
  return count >= cap ? `${count}+` : `${count}`
}

export default function HomePage() {
  const t = useTranslations('publicHomeUi')
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  const [query, setQuery] = useState('')

  useEffect(() => {
    if (hasHydrated && isAuthenticated && user) {
      router.replace(getPostLoginPath(user))
    }
  }, [hasHydrated, isAuthenticated, user, router])

  const medicinesCap = 200
  const symptomsCap = 200
  const institutionsCap = 500
  const { data: medicines } = usePublicMedicines({ limit: medicinesCap })
  const { data: symptoms } = usePublicSymptoms({ limit: symptomsCap })
  const { data: institutions } = usePublicInstitutions({ limit: institutionsCap })

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const term = query.trim()
    router.push(term ? `/knowledge/medicines?q=${encodeURIComponent(term)}` : '/knowledge/medicines')
  }

  // Authenticated users are redirected above — avoid flashing marketing
  // content before that effect runs.
  if (!hasHydrated || (isAuthenticated && user)) {
    return null
  }

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50 to-transparent dark:from-emerald-950/20 dark:to-transparent" />
        <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-20 sm:py-28 text-center">
          <Badge variant="outline" className="mb-4">
            {t('heroBadge')}
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white">
            {t('heroTitle')}
          </h1>
          <p className="mt-6 text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            {t('heroSubtitle')}
          </p>

          <form onSubmit={handleSearch} className="mt-10 max-w-xl mx-auto flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label={t('searchAria')}
                placeholder={t('searchPlaceholder')}
                className="pl-9 h-11"
              />
            </div>
            <Button type="submit" size="lg" className="h-11">
              {t('searchButton')}
            </Button>
          </form>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button asChild variant="outline">
              <Link href="/institutions">
                {t('browseInstitutions')} <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/for-practitioners">{t('forPractitioners')}</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/50">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {medicines ? formatCount(medicines.length, medicinesCap) : '—'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('statMedicines')}</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {symptoms ? formatCount(symptoms.length, symptomsCap) : '—'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('statSymptoms')}</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {institutions ? formatCount(institutions.length, institutionsCap) : '—'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t('statInstitutions')}</p>
          </div>
        </div>
      </section>

      {/* Disciplines */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{t('disciplinesTitle')}</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {t('disciplinesSubtitle')}
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {disciplines.map((d) => (
            <Link key={d.value} href={`/knowledge/medicines?system=${d.value}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center mb-2">
                    <d.icon className="h-5 w-5 text-emerald-600 dark:text-emerald-300" />
                  </div>
                  <CardTitle className="text-lg">{t(`disciplines.${d.value}.label`)}</CardTitle>
                  <CardDescription>{t(`disciplines.${d.value}.description`)}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Institutions preview */}
      {institutions && institutions.length > 0 && (
        <section className="bg-gray-50 dark:bg-slate-900/50 border-y border-gray-200 dark:border-slate-800">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
            <div className="flex items-center justify-between mb-10">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {t('institutionsTitle')}
                </h2>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  {t('institutionsSubtitle')}
                </p>
              </div>
              <Button asChild variant="outline" className="hidden sm:inline-flex">
                <Link href="/institutions">
                  {t('viewAll')} <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {institutions.slice(0, 6).map((institution) => (
                <Card key={institution.id}>
                  <CardHeader>
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                        <GraduationCap className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                      </div>
                      <div>
                        <CardTitle className="text-base leading-snug">
                          {institution.name_en}
                        </CardTitle>
                        {institution.location && (
                          <CardDescription>{institution.location}</CardDescription>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {institution.disciplines.map((d) => (
                        <Badge key={d} variant="secondary" className="capitalize text-xs">
                          {isDiscipline(d) ? t(`disciplines.${d}.label`) : d}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <div className="mt-8 text-center sm:hidden">
              <Button asChild variant="outline">
                <Link href="/institutions">
                  {t('viewAllInstitutions')} <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>
      )}

      {/* For practitioners CTA */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              {t('ctaTitle')}
            </h2>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              {t('ctaSubtitle')}
            </p>
            <div className="mt-6 space-y-4">
              <div className="flex items-start gap-3">
                <Users2 className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{t('featurePatientsTitle')}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('featurePatientsDesc')}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CalendarClock className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {t('featureAppointmentsTitle')}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('featureAppointmentsDesc')}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {t('featureSecurityTitle')}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('featureSecurityDesc')}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-8">
              <Button asChild size="lg">
                <Link href="/register">
                  {t('getStarted')} <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
          <Card className="p-2">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-4">
                <Pill className="h-5 w-5 text-emerald-600" />
                <p className="font-semibold text-gray-900 dark:text-white">
                  {t('builtForEvery')}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {disciplines.map((d) => (
                  <div
                    key={d.value}
                    className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-slate-700 p-3"
                  >
                    <d.icon className="h-4 w-4 text-emerald-600 dark:text-emerald-300 shrink-0" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {t(`disciplines.${d.value}.label`)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
