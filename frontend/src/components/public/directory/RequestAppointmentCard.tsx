'use client'

import Link from 'next/link'
import { useEffect, useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { identityError } from '@/components/identity/identityUtils'
import { AddProfileForm } from '@/components/patient-portal/AddProfileForm'
import {
  isoDateFromToday,
  isUnauthorized,
  portalButton,
  portalButtonOutline,
  portalErrorBox,
  portalInput,
  portalLabel,
} from '@/components/patient-portal/portalUtils'
import { patientPortalApi } from '@/lib/api/patientPortal'
import { usePortalMe, useRequestAppointment } from '@/lib/hooks/usePatientPortal'
import { REQUEST_WINDOWS, type RequestWindow } from '@/types/appointmentRequest'

const REASON_MAX = 300

interface Props {
  slug: string
  /** Who receives the details: the clinic name, or the practitioner's name when there is none */
  clinicName: string
  practitionerName: string
}

/** Ask this practitioner for an appointment with a verified phone (patient portal sign-in). */
export function RequestAppointmentCard({ slug, clinicName, practitionerName }: Props) {
  const t = useTranslations('patientPortalUi.requestAppointment')
  // sessionStorage only exists in the browser: decide after mount
  const [ready, setReady] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSignedIn(patientPortalApi.hasSession())
    setReady(true)
  }, [])

  const shell = (children: React.ReactNode) => (
    <div className="space-y-4 rounded-lg border border-emerald-200 bg-card p-5 dark:border-emerald-900">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('title')}</h2>
      {children}
    </div>
  )

  if (!ready) return shell(<div className="h-24" aria-busy="true" />)

  if (!signedIn) {
    return shell(
      <>
        <p className="text-base text-gray-700 dark:text-gray-300">{t('signInBody', { name: practitionerName })}</p>
        <Link href={`/patient?next=${encodeURIComponent(`/practitioners/${slug}`)}`} className={`${portalButton} block text-center`}>
          {t('signInButton')}
        </Link>
      </>
    )
  }

  return shell(
    <SignedInForm
      slug={slug}
      clinicName={clinicName}
      practitionerName={practitionerName}
      onSignedOut={() => setSignedIn(false)}
    />
  )
}

function SignedInForm({ slug, clinicName, practitionerName, onSignedOut }: Props & { onSignedOut: () => void }) {
  const t = useTranslations('patientPortalUi.requestAppointment')
  const me = usePortalMe(true)
  const request = useRequestAppointment()
  const [adding, setAdding] = useState(false)
  const [profileId, setProfileId] = useState('')
  const [date, setDate] = useState('')
  const [window_, setWindow] = useState<RequestWindow>('any')
  const [reason, setReason] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)

  useEffect(() => {
    if (me.error && isUnauthorized(me.error)) onSignedOut()
  }, [me.error, onSignedOut])

  const profiles = me.data?.profiles ?? []
  const hasSelf = profiles.some((p) => p.relationship === 'self')
  const selected = profiles.find((p) => p.id === profileId) ?? profiles[0]
  const min = isoDateFromToday(0)
  const max = isoDateFromToday(60)

  function message(err: unknown): string {
    const { code, status } = identityError(err)
    switch (code) {
      case 'request_in_progress': return t('errors.requestInProgress')
      case 'too_many_open_requests': return t('errors.tooManyOpen')
      case 'date_out_of_range': return t('errors.dateOutOfRange')
      case 'not_accepting_requests': return t('errors.notAccepting')
    }
    if (status === 404) return t('errors.notAvailable')
    if (status === 429) return t('errors.tooMany')
    return t('errors.generic')
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!selected) return
    if (!date || date < min || date > max) return setError(t('errors.dateOutOfRange'))
    if (!consent) return setError(t('errors.consent'))
    setError(null)
    try {
      await request.mutateAsync({
        practitioner_slug: slug,
        profile_id: selected.id,
        preferred_date: date,
        preferred_window: window_,
        reason: reason.trim() || null,
        consent: true,
      })
      setSent(true)
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut()
      setError(message(err))
    }
  }

  if (sent) {
    return (
      <div role="status" className="space-y-3 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-base text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
        <p>{t('sent')}</p>
        <Link href="/patient" className="inline-block font-medium underline">{t('seeRequests')}</Link>
      </div>
    )
  }

  if (me.isLoading) return <div className="h-24 animate-pulse rounded-md bg-muted" aria-busy="true" />
  if (me.isError) {
    return (
      <div role="alert" className={portalErrorBox}>
        <p>{t('loadFailed')}</p>
        <button type="button" className={`${portalButtonOutline} mt-2`} onClick={() => void me.refetch()}>{t('retry')}</button>
      </div>
    )
  }

  if (profiles.length === 0 || adding) {
    return (
      <div className="space-y-3">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">{profiles.length === 0 ? t('addYourselfTitle') : t('addChildTitle')}</h3>
        {profiles.length === 0 && <p className="text-base text-gray-600 dark:text-gray-400">{t('addYourselfBody')}</p>}
        <AddProfileForm
          hasSelf={hasSelf}
          idPrefix="req-add"
          onAdded={(p) => { setProfileId(p.id); setAdding(false) }}
          onCancel={profiles.length > 0 ? () => setAdding(false) : undefined}
          onSignedOut={onSignedOut}
        />
      </div>
    )
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      <p className="text-base text-gray-600 dark:text-gray-400">{t('intro', { name: practitionerName })}</p>

      <div>
        <label htmlFor="req-person" className={portalLabel}>{t('person')}</label>
        <select id="req-person" className={portalInput} value={selected?.id ?? ''} onChange={(e) => setProfileId(e.target.value)} disabled={request.isLoading}>
          {profiles.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}
        </select>
        <button type="button" className="mt-1 min-h-11 text-base text-emerald-700 underline dark:text-emerald-400" onClick={() => setAdding(true)}>
          {hasSelf ? t('addChild') : t('addPerson')}
        </button>
      </div>

      <div>
        <label htmlFor="req-date" className={portalLabel}>{t('date')}</label>
        <input id="req-date" type="date" className={portalInput} min={min} max={max} value={date} onChange={(e) => setDate(e.target.value)} disabled={request.isLoading} />
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('dateHint')}</p>
      </div>

      <fieldset>
        <legend className={portalLabel}>{t('window')}</legend>
        <div className="mt-1 grid grid-cols-2 gap-2">
          {REQUEST_WINDOWS.map((w) => (
            <label key={w} className={`flex min-h-11 items-center gap-2 rounded-md border px-3 text-base ${window_ === w ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40' : 'border-gray-300 dark:border-slate-700'}`}>
              <input type="radio" name="req-window" checked={window_ === w} onChange={() => setWindow(w)} disabled={request.isLoading} />
              {t(`windows.${w}`)}
            </label>
          ))}
        </div>
      </fieldset>

      <div>
        <label htmlFor="req-reason" className={portalLabel}>{t('reason')}</label>
        <textarea id="req-reason" rows={3} maxLength={REASON_MAX} className={portalInput} value={reason} onChange={(e) => setReason(e.target.value)} disabled={request.isLoading} aria-describedby="req-reason-note" />
        <p id="req-reason-note" className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {t('reasonNote')} {t('reasonCount', { count: reason.length, max: REASON_MAX })}
        </p>
      </div>

      <label className="flex items-start gap-2 text-base text-gray-800 dark:text-gray-200">
        <input type="checkbox" className="mt-1.5 h-5 w-5 shrink-0" checked={consent} onChange={(e) => setConsent(e.target.checked)} disabled={request.isLoading} />
        <span>
          {t('consent', { clinic: clinicName })}{' '}
          <Link href="/privacy" className="text-emerald-700 underline dark:text-emerald-400">{t('privacy')}</Link>
        </span>
      </label>

      {error && <p role="alert" className={portalErrorBox}>{error}</p>}

      <button type="submit" className={portalButton} disabled={request.isLoading}>{request.isLoading ? t('sending') : t('submit')}</button>
    </form>
  )
}
