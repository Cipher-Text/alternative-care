import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getLocale, getTranslations } from 'next-intl/server'
import { ArrowLeft, BadgeCheck, MapPin, Stethoscope } from 'lucide-react'
import { fetchPractitioner, isDirectoryLaunched } from '@/lib/api/publicDirectory'
import { pickLocalized } from '@/lib/api/publicArticles'
import { formatFee, isDirectoryDiscipline, telHref, whatsappDigits } from '@/lib/directoryFormat'
import { VerifiedBadge } from '@/components/public/directory/VerifiedBadge'
import { ContactButtons } from '@/components/public/directory/ContactButtons'
import { RequestForm } from '@/components/public/directory/RequestForm'
import { RequestAppointmentCard } from '@/components/public/directory/RequestAppointmentCard'

type Params = Promise<{ slug: string }>

const SITE = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params
  const [p, launched] = await Promise.all([fetchPractitioner(slug).catch(() => null), isDirectoryLaunched()])
  if (!p) return {}
  const [locale, t] = await Promise.all([getLocale(), getTranslations('publicPractitionersUi')])
  const discipline = p.disciplines[0]
  const disciplineLabel = discipline && isDirectoryDiscipline(discipline) ? t(`discipline_${discipline}`) : discipline ?? ''
  const district = pickLocalized(locale, p.district_en, p.district_bn)
  const title = district
    ? t('metaTitle', { name: p.display_name, discipline: disciplineLabel, district })
    : t('metaTitleNoDistrict', { name: p.display_name, discipline: disciplineLabel })
  const description =
    pickLocalized(locale, p.headline_en, p.headline_bn) ??
    pickLocalized(locale, p.bio_en, p.bio_bn)?.slice(0, 160) ??
    t('metaDescriptionFallback', { name: p.display_name, discipline: disciplineLabel })
  return {
    title,
    description,
    alternates: { canonical: `/practitioners/${p.slug}` },
    robots: launched ? undefined : { index: false, follow: true },
    openGraph: {
      type: 'profile',
      title,
      description,
      images: p.logo_url ? [p.logo_url] : undefined,
    },
  }
}

export default async function PractitionerPage({ params }: { params: Params }) {
  const { slug } = await params
  const p = await fetchPractitioner(slug)
  if (!p) notFound()

  const [locale, t, tc] = await Promise.all([getLocale(), getTranslations('publicPractitionersUi'), getTranslations('publicContactUi')])
  const tr = await getTranslations('patientPortalUi.requestAppointment')
  const headline = pickLocalized(locale, p.headline_en, p.headline_bn)
  const bio = pickLocalized(locale, p.bio_en, p.bio_bn)
  const district = pickLocalized(locale, p.district_en, p.district_bn)
  const upazila = pickLocalized(locale, p.upazila_en, p.upazila_bn)
  const division = pickLocalized(locale, p.division_en, p.division_bn)
  const disciplineLabel = (d: string) => (isDirectoryDiscipline(d) ? t(`discipline_${d}`) : d)
  const addressParts = [p.address_line_1, p.address_line_2, p.landmark, upazila, district, division].filter(
    (v): v is string => !!v && v.trim() !== ''
  )
  const hasCoords = p.latitude != null && p.longitude != null
  const wa = p.whatsapp ? whatsappDigits(p.whatsapp) : null
  const clinic = p.clinic_name ?? p.display_name

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Physician',
    name: p.display_name,
    url: `${SITE}/practitioners/${p.slug}`,
    medicalSpecialty: p.disciplines.map(disciplineLabel),
    description: headline ?? undefined,
    telephone: p.phone ?? undefined,
    address: {
      '@type': 'PostalAddress',
      streetAddress: [p.address_line_1, p.address_line_2].filter(Boolean).join(', ') || undefined,
      addressLocality: p.district_en ?? undefined,
      addressRegion: p.division_en ?? undefined,
      addressCountry: 'BD',
    },
  }

  const row = (label: string, value: string) => (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-900 dark:text-gray-100">{value}</dd>
    </div>
  )

  return (
    <article className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }}
      />
      <Link href="/practitioners" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-emerald-700 dark:text-gray-400">
        <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
        {t('breadcrumbBack')}
      </Link>

      <div className="mt-6 grid gap-8 lg:grid-cols-3">
        <div className="space-y-8 lg:col-span-2">
          <header>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{p.display_name}</h1>
              <VerifiedBadge />
            </div>
            {p.clinic_name && <p className="mt-1 text-gray-600 dark:text-gray-400">{p.clinic_name}</p>}
            {p.registration_body && (
              <p className="mt-2 flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                <BadgeCheck className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                {t('registeredWith', { body: p.registration_body })}
              </p>
            )}
            {headline && <p className="mt-3 text-lg text-gray-700 dark:text-gray-300">{headline}</p>}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              {p.disciplines.map((d) => (
                <span key={d} className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  {disciplineLabel(d)}
                </span>
              ))}
            </div>
          </header>

          {bio && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('about')}</h2>
              <p className="mt-2 whitespace-pre-line text-gray-700 dark:text-gray-300">{bio}</p>
            </section>
          )}

          <section>
            <dl className="grid gap-4 sm:grid-cols-2">
              {p.years_of_experience != null && row(t('experience'), t('experienceYears', { count: p.years_of_experience }))}
              {p.languages.length > 0 &&
                row(t('languages'), p.languages.map((l) => (l === 'en' || l === 'bn' ? t(`lang_${l}`) : l)).join(', '))}
              {row(t('availability'), t(`availability_${p.availability}`))}
              {p.consultation_hours && row(t('hours'), p.consultation_hours)}
              {p.fee_bdt != null && row(t('fees'), t('fee', { amount: formatFee(p.fee_bdt) }))}
              {p.follow_up_fee_bdt != null && row(t('fees'), t('followUpFee', { amount: formatFee(p.follow_up_fee_bdt) }))}
            </dl>
          </section>

          {p.degrees.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('qualifications')}</h2>
              <ul className="mt-2 space-y-2">
                {p.degrees.map((d, i) => (
                  <li key={i} className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-medium text-gray-900 dark:text-white">{d.degree_name}</span>
                    {' · '}
                    {t('degreeLine', { institution: d.institution_name, year: d.completion_year })}
                    {d.is_verified && (
                      <span className="ml-2 inline-flex items-center gap-1 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                        <BadgeCheck className="h-3.5 w-3.5" aria-hidden="true" />
                        {t('degreeVerified')}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {addressParts.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('address')}</h2>
              <p className="mt-2 flex gap-2 text-gray-700 dark:text-gray-300">
                <MapPin className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{addressParts.join(', ')}</span>
              </p>
              {hasCoords && (
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${p.latitude},${p.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-sm text-emerald-700 underline dark:text-emerald-400"
                >
                  {t('directions')}
                </a>
              )}
            </section>
          )}

          <div className="flex gap-3 rounded-lg border border-gray-200 p-4 text-sm dark:border-slate-800">
            <Stethoscope className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" />
            <p className="text-gray-600 dark:text-gray-400">
              {t('disclaimer')}{' '}
              <Link href="/disclaimer" className="text-emerald-700 underline dark:text-emerald-400">{t('disclaimerLink')}</Link>
            </p>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            <Link href={`/contact?topic=report_profile&practitioner=${encodeURIComponent(p.slug)}`} className="underline hover:text-gray-700 dark:hover:text-gray-200">
              {tc('reportProfile')}
            </Link>
          </p>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <div className="space-y-4 rounded-lg border border-gray-200 bg-card p-5 dark:border-slate-800">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('contactTitle')}</h2>
            <ContactButtons slug={p.slug} telHref={p.phone ? telHref(p.phone) : null} whatsappHref={wa ? `https://wa.me/${wa}` : null} />
            <p className="text-xs text-gray-600 dark:text-gray-400">{t('urgentNote')}</p>
          </div>
          {p.accepts_requests && (
            <>
              <RequestAppointmentCard slug={p.slug} clinicName={clinic} practitionerName={p.display_name} />
              <div className="rounded-lg border border-gray-200 bg-card p-5 dark:border-slate-800">
                <RequestForm slug={p.slug} clinicName={clinic} title={tr('callBackTitle')} />
              </div>
            </>
          )}
        </aside>
      </div>
    </article>
  )
}
