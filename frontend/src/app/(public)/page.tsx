'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
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
  {
    value: 'homeopathy',
    label: 'Homeopathy',
    icon: FlaskConical,
    description: 'Remedies, potencies, and repertory guidance.',
  },
  {
    value: 'ayurveda',
    label: 'Ayurveda',
    icon: Leaf,
    description: 'Classical formulations and herbal preparations.',
  },
  {
    value: 'unani',
    label: 'Unani',
    icon: Sprout,
    description: 'Traditional Unani-Tibb medicines and practice.',
  },
  {
    value: 'herbal',
    label: 'Herbal',
    icon: Stethoscope,
    description: 'Plant-based remedies used across disciplines.',
  },
] as const

function formatCount(count: number, cap: number) {
  return count >= cap ? `${count}+` : `${count}`
}

export default function HomePage() {
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
            Homeopathy · Ayurveda · Unani · Herbal
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white">
            The alternative medicine platform for clinics and patients alike
          </h1>
          <p className="mt-6 text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            AltCare runs the clinic — patients, appointments, prescriptions, and payments — and
            hosts an open directory of medicines, symptoms, and institutions across all four
            disciplines.
          </p>

          <form onSubmit={handleSearch} className="mt-10 max-w-xl mx-auto flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search medicines, e.g. Arnica, Ashwagandha..."
                className="pl-9 h-11"
              />
            </div>
            <Button type="submit" size="lg" className="h-11">
              Search
            </Button>
          </form>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button asChild variant="outline">
              <Link href="/institutions">
                Browse Institutions <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/for-practitioners">For Practitioners</Link>
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
            <p className="text-sm text-gray-500 dark:text-gray-400">Medicines cataloged</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {symptoms ? formatCount(symptoms.length, symptomsCap) : '—'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Symptoms indexed</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {institutions ? formatCount(institutions.length, institutionsCap) : '—'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Institutions listed</p>
          </div>
        </div>
      </section>

      {/* Disciplines */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Browse by discipline</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Every medicine and institution is tagged to the disciplines it serves.
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
                  <CardTitle className="text-lg">{d.label}</CardTitle>
                  <CardDescription>{d.description}</CardDescription>
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
                  Institutions directory
                </h2>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Colleges and institutes teaching alternative medicine in Bangladesh.
                </p>
              </div>
              <Button asChild variant="outline" className="hidden sm:inline-flex">
                <Link href="/institutions">
                  View all <ArrowRight className="ml-2 h-4 w-4" />
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
                          {d}
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
                  View all institutions <ArrowRight className="ml-2 h-4 w-4" />
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
              Run your clinic on AltCare
            </h2>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              Patients, appointments, prescriptions, payments, and your own medicine library — one
              system built for Homeopathy, Ayurveda, Unani, and Herbal practices.
            </p>
            <div className="mt-6 space-y-4">
              <div className="flex items-start gap-3">
                <Users2 className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Patient records</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Full history, tags, and diagnoses in one place.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CalendarClock className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Appointments &amp; prescriptions
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Scheduling, visit notes, and a prescription builder with autocomplete.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Multi-tenant security
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Row-level isolation keeps every clinic&apos;s data separate.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-8">
              <Button asChild size="lg">
                <Link href="/login">
                  Get Started <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
          <Card className="p-2">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-4">
                <Pill className="h-5 w-5 text-emerald-600" />
                <p className="font-semibold text-gray-900 dark:text-white">
                  Built for every discipline
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
                      {d.label}
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
