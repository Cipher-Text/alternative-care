'use client'

import { use, useMemo, useState } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { ArrowLeft, ChevronDown, ChevronUp, Loader2, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useDateFormat } from '@/lib/i18n/date'
import { useAuthStore } from '@/store/authStore'
import { identityError } from '@/components/identity/identityUtils'
import { useSharedRecords } from '@/lib/hooks/useSharing'
import type { SharedDiagnosis, SharedPrescription } from '@/types/sharing'

/** Read-only, on screen only: no edit, copy, export or print. Opening it is logged and the patient can see it. */
export default function SharedRecordsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const t = useTranslations('sharingUi')
  const { fmt } = useDateFormat()
  const isDoctor = useAuthStore((s) => s.user?.role) === 'doctor'
  const { data, isLoading, isError, error, refetch } = useSharedRecords(id, isDoctor)

  const prescriptions = useMemo(
    () => [...(data?.prescriptions ?? [])].sort((a, b) => b.date.localeCompare(a.date)),
    [data?.prescriptions]
  )
  const diagnoses = useMemo(
    () => [...(data?.diagnoses ?? [])].sort((a, b) => b.diagnosed_at.localeCompare(a.diagnosed_at)),
    [data?.diagnoses]
  )
  const active = (data?.shares ?? []).filter((s) => s.status === 'active')

  const back = (
    <Link href={`/patients/${id}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:underline">
      <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      {t('page.back')}
    </Link>
  )

  if (!isDoctor) {
    return (
      <div className="space-y-4">
        {back}
        <p role="status" className="text-base">{t('page.doctorsOnly')}</p>
      </div>
    )
  }

  const notLinked = isError && identityError(error).status === 404

  return (
    <div className="space-y-6">
      {back}
      <h1 className="text-2xl font-bold">{t('page.title')}</h1>

      {isLoading && <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label={t('page.loading')} />}
      {notLinked && <p role="alert" className="text-base">{t('page.notLinked')}</p>}
      {isError && !notLinked && (
        <div role="alert" className="flex flex-wrap items-center gap-3 text-base">
          <span>{t('page.loadFailed')}</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>{t('page.retry')}</Button>
        </div>
      )}

      {data && (
        <>
          {active.map((s) => (
            <div key={s.share_id} role="note" className="flex items-start gap-3 rounded-lg border-2 border-amber-300 bg-amber-50 p-4 text-base font-medium text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
              <span>{t('page.banner', { clinic: s.clinic_name, date: fmt(s.expires_at, 'MMM d, yyyy') })}</span>
            </div>
          ))}

          {prescriptions.length === 0 && diagnoses.length === 0 ? (
            <p className="rounded-lg border border-dashed p-4 text-base text-muted-foreground">{t('page.empty')}</p>
          ) : (
            <>
              <section className="space-y-3" aria-labelledby="sr-rx">
                <h2 id="sr-rx" className="text-lg font-semibold">{t('page.prescriptions')}</h2>
                {prescriptions.length === 0 && <p className="text-sm text-muted-foreground">{t('page.prescriptionsEmpty')}</p>}
                {prescriptions.map((p, i) => <PrescriptionCard key={`${p.source_clinic}-${p.date}-${i}`} p={p} />)}
              </section>

              <section className="space-y-3" aria-labelledby="sr-dx">
                <h2 id="sr-dx" className="text-lg font-semibold">{t('page.diagnoses')}</h2>
                {diagnoses.length === 0 && <p className="text-sm text-muted-foreground">{t('page.diagnosesEmpty')}</p>}
                {diagnoses.map((d, i) => <DiagnosisCard key={`${d.source_clinic}-${d.diagnosed_at}-${i}`} d={d} />)}
              </section>
            </>
          )}
        </>
      )}
    </div>
  )
}

function PrescriptionCard({ p }: { p: SharedPrescription }) {
  const t = useTranslations('sharingUi.page')
  const { fmt } = useDateFormat()
  const [open, setOpen] = useState(false)
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="space-y-0.5">
            <p className="font-medium">{fmt(p.date, 'MMM d, yyyy')}</p>
            <p className="text-sm text-muted-foreground">{t('source', { clinic: p.source_clinic })} · {t('sharedUntil', { date: fmt(p.shared_until, 'MMM d, yyyy') })}</p>
            {p.doctor_name && <p className="text-sm">{t('doctor', { name: p.doctor_name })}</p>}
            {p.diagnosis && <p className="text-sm"><span className="font-medium">{t('diagnosis')}:</span> {p.diagnosis}</p>}
          </div>
          <Button variant="outline" size="sm" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
            {open ? <ChevronUp className="mr-1 h-4 w-4" aria-hidden="true" /> : <ChevronDown className="mr-1 h-4 w-4" aria-hidden="true" />}
            {open ? t('collapse') : t('expand')}
          </Button>
        </div>
        {open && (
          <div className="space-y-3 border-t pt-3">
            {p.advice && <p className="text-sm whitespace-pre-line"><span className="font-medium">{t('advice')}:</span> {p.advice}</p>}
            <p className="text-sm font-medium">{t('medicines')}</p>
            {p.items.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t('noMedicines')}</p>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('medicine')}</TableHead>
                      <TableHead>{t('dosage')}</TableHead>
                      <TableHead>{t('frequency')}</TableHead>
                      <TableHead>{t('duration')}</TableHead>
                      <TableHead>{t('instructions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {p.items.map((it, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{it.medicine}</TableCell>
                        <TableCell>{it.dosage}</TableCell>
                        <TableCell>{it.frequency}</TableCell>
                        <TableCell>{it.duration ?? ''}</TableCell>
                        <TableCell>{it.instructions ?? ''}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DiagnosisCard({ d }: { d: SharedDiagnosis }) {
  const t = useTranslations('sharingUi.page')
  const { fmt } = useDateFormat()
  return (
    <Card>
      <CardContent className="space-y-1 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-medium">{d.description}</p>
          <Badge variant={d.is_active ? 'default' : 'outline'}>{d.is_active ? t('active') : t('inactive')}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {d.icd_code ? `${t('icd', { code: d.icd_code })} · ` : ''}{t('diagnosedOn', { date: fmt(d.diagnosed_at, 'MMM d, yyyy') })}
        </p>
        <p className="text-sm text-muted-foreground">{t('source', { clinic: d.source_clinic })} · {t('sharedUntil', { date: fmt(d.shared_until, 'MMM d, yyyy') })}</p>
      </CardContent>
    </Card>
  )
}
