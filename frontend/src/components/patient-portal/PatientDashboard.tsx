'use client'

import { useEffect, useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useDateFormat } from '@/lib/i18n/date'
import { patientPortalApi } from '@/lib/api/patientPortal'
import { identityError } from '@/components/identity/identityUtils'
import { AddPersonCard, MyRequests } from './AppointmentRequests'
import {
  useActivatePortalCode,
  usePortalMe,
  usePortalRecords,
  useRevokePortalLink,
} from '@/lib/hooks/usePatientPortal'
import type {
  PortalAppointment,
  PortalClinic,
  PortalPrescription,
  PortalProfile,
  PortalReceipt,
} from '@/types/patientPortal'
import {
  formatAmount,
  isUnauthorized,
  localDate,
  portalButton,
  portalButtonOutline,
  portalErrorBox,
  portalInput,
  portalLabel,
} from './portalUtils'

type Section = 'appointments' | 'prescriptions' | 'receipts'
const SECTIONS: Section[] = ['appointments', 'prescriptions', 'receipts']
const card = 'rounded-lg border border-gray-200 p-4 dark:border-slate-800'

export function PatientDashboard({ onSignedOut }: { onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('patientPortalUi')
  const me = usePortalMe(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [section, setSection] = useState<Section>('appointments')

  useEffect(() => {
    if (me.error && isUnauthorized(me.error)) onSignedOut(true)
  }, [me.error, onSignedOut])

  const profiles = me.data?.profiles ?? []
  const profile = profiles.find((p) => p.id === selectedId) ?? profiles[0]

  return (
    <div className="mx-auto w-full max-w-2xl space-y-5 px-4 py-6 sm:py-10">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('dashboard.title')}</h1>
          {me.data && <p className="text-base text-gray-600 dark:text-gray-400">{t('dashboard.signedInAs', { phone: me.data.phone_masked })}</p>}
        </div>
        <button type="button" className={portalButtonOutline} onClick={() => onSignedOut(false)}>{t('dashboard.signOut')}</button>
      </header>

      {me.isLoading && <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label={t('dashboard.loading')} />}
      {me.isError && !isUnauthorized(me.error) && (
        <div role="alert" className={portalErrorBox}>
          <p>{t('dashboard.loadFailed')}</p>
          <button type="button" className={`${portalButtonOutline} mt-2`} onClick={() => void me.refetch()}>{t('dashboard.retry')}</button>
        </div>
      )}

      {me.data && profiles.length === 0 && (
        <p className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-base text-gray-800 dark:border-slate-800 dark:bg-slate-900 dark:text-gray-200">{t('dashboard.noProfiles')}</p>
      )}

      {profiles.length > 1 && (
        <div role="tablist" aria-label={t('dashboard.profilesLabel')} className="flex flex-wrap gap-2">
          {profiles.map((p) => (
            <button
              key={p.id}
              type="button"
              role="tab"
              aria-selected={p.id === profile?.id}
              onClick={() => setSelectedId(p.id)}
              className={`min-h-11 rounded-full border px-4 py-2 text-base ${p.id === profile?.id ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-gray-300 dark:border-slate-700'}`}
            >
              {p.display_name}
              {p.is_dependent && <span className="ml-1 text-sm opacity-80">({t('dashboard.dependent')})</span>}
            </button>
          ))}
        </div>
      )}

      {profile && (
        <>
          <ProfileSummary profile={profile} onSignedOut={onSignedOut} />
          <div role="tablist" aria-label={t('records.label')} className="flex gap-2 overflow-x-auto">
            {SECTIONS.map((s) => (
              <button
                key={s}
                type="button"
                role="tab"
                aria-selected={section === s}
                onClick={() => setSection(s)}
                className={`min-h-11 shrink-0 rounded-md border px-4 py-2 text-base ${section === s ? 'border-emerald-600 bg-emerald-50 font-semibold text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200' : 'border-gray-300 dark:border-slate-700'}`}
              >
                {t(`records.${s}.tab`)}
              </button>
            ))}
          </div>
          <Records profileId={profile.id} section={section} onSignedOut={onSignedOut} />
        </>
      )}

      {me.data && <MyRequests onSignedOut={onSignedOut} />}
      {me.data && <AddPersonCard onSignedOut={onSignedOut} />}
      {me.data && <ActivateCard onSignedOut={onSignedOut} />}
    </div>
  )
}

function ProfileSummary({ profile, onSignedOut }: { profile: PortalProfile; onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('patientPortalUi')
  const { fmt } = useDateFormat()
  const revoke = useRevokePortalLink()
  const [target, setTarget] = useState<PortalClinic | null>(null)
  const [error, setError] = useState<string | null>(null)

  const doRevoke = async () => {
    if (!target) return
    try {
      await revoke.mutateAsync(target.link_id)
      setTarget(null)
      setError(null)
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      setError(t('clinics.removeFailed'))
    }
  }

  return (
    <section className={`${card} space-y-3`}>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {profile.display_name}
        {profile.is_dependent && <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-sm font-normal dark:bg-slate-800">{t('dashboard.dependent')}</span>}
      </h2>
      {profile.clinics.length > 0 && <h3 className="text-base font-medium text-gray-700 dark:text-gray-300">{t('clinics.heading')}</h3>}
      <ul className="space-y-2">
        {profile.clinics.map((c) => (
          <li key={c.link_id} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-gray-50 p-3 dark:bg-slate-900">
            <span>
              <span className="block text-base font-medium">{c.clinic_name}</span>
              <span className="block text-sm text-gray-500 dark:text-gray-400">{t('clinics.since', { date: fmt(c.linked_at, 'MMM d, yyyy') })}</span>
            </span>
            <button type="button" className={`${portalButtonOutline} py-2`} onClick={() => { setError(null); setTarget(c) }}>{t('clinics.remove')}</button>
          </li>
        ))}
      </ul>

      <Dialog open={!!target} onOpenChange={(o) => { if (!o && !revoke.isLoading) setTarget(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('clinics.removeTitle', { clinic: target?.clinic_name ?? '' })}</DialogTitle>
            <DialogDescription>{t('clinics.removeBody')}</DialogDescription>
          </DialogHeader>
          {error && <p role="alert" className={portalErrorBox}>{error}</p>}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setTarget(null)} disabled={revoke.isLoading}>{t('clinics.cancel')}</Button>
            <Button variant="destructive" onClick={doRevoke} disabled={revoke.isLoading}>
              {revoke.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('clinics.confirmRemove')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  )
}

function Records({ profileId, section, onSignedOut }: { profileId: string; section: Section; onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('patientPortalUi.records')
  const records = usePortalRecords(profileId)

  useEffect(() => {
    if (records.error && isUnauthorized(records.error)) onSignedOut(true)
  }, [records.error, onSignedOut])

  if (records.isLoading) return <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label={t('loading')} />
  if (records.isError) {
    return (
      <div role="alert" className={portalErrorBox}>
        <p>{t('loadFailed')}</p>
        <button type="button" className={`${portalButtonOutline} mt-2`} onClick={() => void records.refetch()}>{t('retry')}</button>
      </div>
    )
  }
  if (!records.data) return null
  if (section === 'appointments') return <Appointments items={records.data.appointments} />
  if (section === 'prescriptions') return <Prescriptions items={records.data.prescriptions} onSignedOut={onSignedOut} />
  return <Receipts items={records.data.receipts} />
}

function Empty({ text }: { text: string }) {
  return <p className="rounded-lg border border-dashed border-gray-300 p-4 text-base text-gray-600 dark:border-slate-700 dark:text-gray-400">{text}</p>
}

const STATUSES = ['scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']
const STATUS_STYLE: Record<string, string> = {
  completed: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200',
  cancelled: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
  no_show: 'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200',
}

function Appointments({ items }: { items: PortalAppointment[] }) {
  const t = useTranslations('patientPortalUi.records.appointments')
  const { fmt } = useDateFormat()
  const [now] = useState(() => Date.now())
  if (items.length === 0) return <Empty text={t('empty')} />
  const at = (a: PortalAppointment) => localDate(a.date, a.time).getTime()
  const upcoming = items.filter((a) => at(a) >= now).sort((a, b) => at(a) - at(b))
  const past = items.filter((a) => at(a) < now).sort((a, b) => at(b) - at(a))

  const row = (a: PortalAppointment, i: number) => (
    <li key={`${a.date}-${a.time}-${i}`} className={`${card} space-y-1`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-base font-semibold">{fmt(localDate(a.date, a.time), 'EEE, MMM d, yyyy')} · {fmt(localDate(a.date, a.time), 'h:mm a')}</p>
        <span className={`rounded-full px-2.5 py-0.5 text-sm ${STATUS_STYLE[a.status] ?? 'bg-gray-100 text-gray-900 dark:bg-slate-800 dark:text-gray-200'}`}>
          {STATUSES.includes(a.status) ? t(`status.${a.status}`) : a.status.replace(/_/g, ' ')}
        </span>
      </div>
      <p className="text-base">{a.clinic_name}{a.doctor_name ? ` · ${a.doctor_name}` : ''}</p>
      {a.reason && <p className="text-sm text-gray-600 dark:text-gray-400">{t('reason', { reason: a.reason })}</p>}
    </li>
  )

  return (
    <div className="space-y-4">
      {upcoming.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">{t('upcoming')}</h3>
          <ul className="space-y-2">{upcoming.map(row)}</ul>
        </div>
      )}
      {past.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">{t('past')}</h3>
          <ul className="space-y-2">{past.map(row)}</ul>
        </div>
      )}
    </div>
  )
}

function Prescriptions({ items, onSignedOut }: { items: PortalPrescription[]; onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('patientPortalUi.records.prescriptions')
  const { fmt } = useDateFormat()
  const [open, setOpen] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)
  const [pdfError, setPdfError] = useState<string | null>(null)
  if (items.length === 0) return <Empty text={t('empty')} />

  async function download(p: PortalPrescription) {
    setPdfError(null)
    setDownloading(p.id)
    try {
      const blob = await patientPortalApi.prescriptionPdf(p.link_id, p.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `prescription-${p.date}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      setPdfError(identityError(err).status === 503 ? t('pdfUnavailable') : t('pdfFailed'))
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="space-y-2">
      {pdfError && <p role="alert" className={portalErrorBox}>{pdfError}</p>}
      <ul className="space-y-2">
        {items.map((p) => {
          const expanded = open === p.id
          return (
            <li key={p.id} className={card}>
              <button type="button" className="flex min-h-11 w-full items-start justify-between gap-3 text-left" aria-expanded={expanded} onClick={() => setOpen(expanded ? null : p.id)}>
                <span>
                  <span className="block text-base font-semibold">{fmt(localDate(p.date), 'MMM d, yyyy')} · {p.clinic_name}</span>
                  <span className="block text-sm text-gray-600 dark:text-gray-400">{p.doctor_name ?? t('noDoctor')}</span>
                  {p.diagnosis && <span className="block text-base">{p.diagnosis}</span>}
                </span>
                <span className="shrink-0 text-sm text-emerald-700 dark:text-emerald-400">{expanded ? t('hide') : t('show')}</span>
              </button>
              {expanded && (
                <div className="mt-3 space-y-3 border-t border-gray-200 pt-3 dark:border-slate-800">
                  {p.advice && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{t('advice')}</p>
                      <p className="whitespace-pre-line text-base">{p.advice}</p>
                    </div>
                  )}
                  {p.items.length === 0 ? (
                    <p className="text-base text-gray-600 dark:text-gray-400">{t('noMedicines')}</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[28rem] text-left text-base">
                        <thead>
                          <tr className="border-b border-gray-200 text-sm text-gray-600 dark:border-slate-800 dark:text-gray-400">
                            <th className="py-1 pr-2 font-medium">{t('medicine')}</th>
                            <th className="py-1 pr-2 font-medium">{t('dosage')}</th>
                            <th className="py-1 pr-2 font-medium">{t('frequency')}</th>
                            <th className="py-1 font-medium">{t('duration')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {p.items.map((it, i) => (
                            <tr key={i} className="border-b border-gray-100 align-top dark:border-slate-900">
                              <td className="py-2 pr-2 font-medium">{it.medicine}{it.instructions && <span className="block text-sm font-normal text-gray-600 dark:text-gray-400">{it.instructions}</span>}</td>
                              <td className="py-2 pr-2">{it.dosage}</td>
                              <td className="py-2 pr-2">{it.frequency}</td>
                              <td className="py-2">{it.duration ?? ''}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <button type="button" className={portalButtonOutline} disabled={downloading === p.id} onClick={() => void download(p)}>
                    {downloading === p.id ? t('downloading') : t('downloadPdf')}
                  </button>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function Receipts({ items }: { items: PortalReceipt[] }) {
  const t = useTranslations('patientPortalUi.records.receipts')
  const { fmt } = useDateFormat()
  if (items.length === 0) return <Empty text={t('empty')} />
  return (
    <ul className="space-y-2">
      {items.map((r, i) => (
        <li key={`${r.invoice_number ?? ''}-${r.date}-${i}`} className={`${card} space-y-1`}>
          <div className="flex items-baseline justify-between gap-2">
            <p className="text-base font-semibold">{fmt(localDate(r.date), 'MMM d, yyyy')} · {r.clinic_name}</p>
            <p className="text-lg font-bold">{r.currency === 'BDT' ? '৳' : `${r.currency} `}{formatAmount(r.amount)}</p>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('method', { method: r.method.replace(/_/g, ' ') })}
            {r.invoice_number ? ` · ${t('invoice', { number: r.invoice_number })}` : ''}
          </p>
          {r.description && <p className="text-sm text-gray-600 dark:text-gray-400">{r.description}</p>}
        </li>
      ))}
    </ul>
  )
}

function ActivateCard({ onSignedOut }: { onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('patientPortalUi.activate')
  const activate = useActivatePortalCode()
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [added, setAdded] = useState<string | null>(null)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!code.trim()) return setError(t('errors.required'))
    setError(null)
    setAdded(null)
    try {
      const clinic = await activate.mutateAsync(code.trim().toUpperCase())
      setAdded(clinic.clinic_name)
      setCode('')
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      const { code: c, status } = identityError(err)
      if (c === 'invalid_portal_code') setError(t('errors.invalid'))
      else if (c === 'profile_not_visible') setError(t('errors.notVisible'))
      else if (status === 429) setError(t('errors.tooMany'))
      else setError(t('errors.generic'))
    }
  }

  return (
    <section className={card}>
      <form onSubmit={submit} noValidate className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('title')}</h2>
        <p className="text-base text-gray-600 dark:text-gray-400">{t('body')}</p>
        <div>
          <label htmlFor="portal-code" className={portalLabel}>{t('label')}</label>
          <input id="portal-code" autoCapitalize="characters" autoComplete="off" spellCheck={false} className={`${portalInput} font-mono uppercase tracking-widest`} placeholder="ABCD-EFGH" maxLength={12} value={code} onChange={(e) => setCode(e.target.value)} disabled={activate.isLoading} />
        </div>
        {error && <p role="alert" className={portalErrorBox}>{error}</p>}
        {added && <p role="status" className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-base text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">{t('added', { clinic: added })}</p>}
        <button type="submit" className={portalButton} disabled={activate.isLoading}>{activate.isLoading ? t('adding') : t('add')}</button>
      </form>
    </section>
  )
}
