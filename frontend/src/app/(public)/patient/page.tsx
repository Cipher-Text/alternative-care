'use client'

import { useEffect, useState, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { patientPortalApi } from '@/lib/api/patientPortal'
import { identityError, normalizeBdPhone } from '@/components/identity/identityUtils'
import { PatientDashboard } from '@/components/patient-portal/PatientDashboard'
import {
  portalButton,
  portalButtonOutline,
  portalErrorBox,
  portalInput,
  portalLabel,
  safeNextPath,
} from '@/components/patient-portal/portalUtils'
import { usePortalSignOut } from '@/lib/hooks/usePatientPortal'
import type { VerifyRequestResponse } from '@/types/identity'

export default function PatientPortalPage() {
  // sessionStorage is not available while server-rendering: decide after mount
  const [ready, setReady] = useState(false)
  const [signedIn, setSignedIn] = useState(false)
  const [expired, setExpired] = useState(false)
  // where to go after signing in (only a same-origin relative path is ever accepted)
  const [next, setNext] = useState<string | null>(null)
  const router = useRouter()
  const signOut = usePortalSignOut()

  useEffect(() => {
    // sessionStorage only exists in the browser, so this cannot be a lazy initial state (hydration mismatch)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSignedIn(patientPortalApi.hasSession())
    setNext(safeNextPath(new URLSearchParams(window.location.search).get('next')))
    setReady(true)
  }, [])

  const endSession = (wasExpired: boolean) => {
    signOut()
    setExpired(wasExpired)
    setSignedIn(false)
  }

  if (!ready) return <div className="mx-auto w-full max-w-md px-4 py-8" aria-busy="true" />

  return signedIn ? (
    <PatientDashboard onSignedOut={endSession} />
  ) : (
    <SignIn
      expired={expired}
      onSignedIn={() => {
        setExpired(false)
        if (next) router.replace(next)
        else setSignedIn(true)
      }}
    />
  )
}

/** Seeded by backend/scripts/demo_patients.py; the code is always 123456 in development. */
const DEMO_PATIENTS = [
  { label: 'Nasrin Akter (2 clinics)', phone: '01700000001' },
  { label: 'Rahim Uddin (1 clinic)', phone: '01700000002' },
]

function SignIn({ expired, onSignedIn }: { expired: boolean; onSignedIn: () => void }) {
  const t = useTranslations('patientPortalUi.signIn')
  const [phone, setPhone] = useState('')
  const [challenge, setChallenge] = useState<VerifyRequestResponse | null>(null)
  const [code, setCode] = useState('')
  const [countdown, setCountdown] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // after "locked" the only way forward is a new code
  const [locked, setLocked] = useState(false)

  useEffect(() => {
    if (countdown <= 0) return
    const id = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000)
    return () => clearInterval(id)
  }, [countdown])

  function message(err: unknown): string {
    const { code: c, status } = identityError(err)
    switch (c) {
      case 'otp_invalid': return t('errors.otpInvalid')
      case 'otp_expired': return t('errors.otpExpired')
      case 'otp_locked': return t('errors.otpLocked')
      case 'otp_cooldown': return t('errors.otpCooldown')
      case 'otp_phone_limit':
      case 'otp_portal_daily_cap': return t('errors.tooMany')
    }
    if (status === 422) return t('errors.phone')
    if (status === 429) return t('errors.tooMany')
    if (status === 503) return t('errors.smsUnavailable')
    return t('errors.generic')
  }

  async function sendCode(e?: FormEvent) {
    e?.preventDefault()
    const normalized = normalizeBdPhone(phone)
    if (!normalized) return setError(t('errors.phone'))
    setError(null)
    setBusy(true)
    try {
      const res = await patientPortalApi.requestCode(normalized)
      setChallenge(res)
      setCountdown(res.resend_after_seconds)
      setCode('')
      setLocked(false)
    } catch (err) {
      setError(message(err))
    } finally {
      setBusy(false)
    }
  }

  async function confirm(e: FormEvent) {
    e.preventDefault()
    if (!challenge) return
    if (code.length !== 6) return setError(t('errors.codeLength'))
    setError(null)
    setBusy(true)
    try {
      await patientPortalApi.verify(challenge.challenge_id, code)
      onSignedIn()
    } catch (err) {
      if (identityError(err).code === 'otp_locked') setLocked(true)
      setError(message(err))
      setBusy(false)
    }
  }

  const errorBox = error && (
    <p role="alert" className={portalErrorBox}>
      {error}
    </p>
  )

  return (
    <div className="mx-auto w-full max-w-md px-4 py-8 sm:py-12">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
      {expired && (
        <p role="status" className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-base text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          {t('sessionEnded')}
        </p>
      )}

      {!challenge ? (
        <form onSubmit={sendCode} noValidate className="mt-4 space-y-5">
          <p className="text-base text-gray-600 dark:text-gray-400">{t('intro')}</p>
          <div>
            <label htmlFor="portal-phone" className={portalLabel}>{t('phoneLabel')}</label>
            <input id="portal-phone" type="tel" inputMode="tel" autoComplete="tel" className={portalInput} placeholder="01XXXXXXXXX" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={busy} />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('phoneHint')}</p>
          </div>
          {errorBox}
          <button type="submit" className={portalButton} disabled={busy}>{busy ? t('sending') : t('sendCode')}</button>
          {process.env.NODE_ENV !== 'production' && (
            <div className="space-y-2 rounded-md border border-dashed p-3 text-sm">
              <p className="font-medium">{t('devDemo.title')}</p>
              <div className="flex flex-wrap gap-2">
                {DEMO_PATIENTS.map((d) => (
                  <button key={d.phone} type="button" className={portalButtonOutline} disabled={busy} onClick={() => setPhone(d.phone)}>
                    {d.label}
                  </button>
                ))}
              </div>
              <p className="text-muted-foreground">{t('devDemo.hint')}</p>
            </div>
          )}
        </form>
      ) : (
        <form onSubmit={confirm} noValidate className="mt-4 space-y-5">
          <p className="text-base text-gray-600 dark:text-gray-400">{t('codeSent', { phone: challenge.phone_masked })}</p>
          <div>
            <label htmlFor="portal-sms" className={portalLabel}>{t('smsCodeLabel')}</label>
            <input id="portal-sms" inputMode="numeric" autoComplete="one-time-code" maxLength={6} className={`${portalInput} text-center text-2xl tracking-[0.4em]`} placeholder="000000" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} disabled={busy || locked} />
          </div>
          {errorBox}
          {locked ? (
            <button type="button" className={portalButton} disabled={busy || countdown > 0} onClick={() => void sendCode()}>
              {countdown > 0 ? t('resendIn', { seconds: countdown }) : t('sendNew')}
            </button>
          ) : (
            <>
              <button type="submit" className={portalButton} disabled={busy || code.length !== 6}>{busy ? t('confirming') : t('confirm')}</button>
              <button type="button" className={`${portalButtonOutline} w-full`} disabled={busy || countdown > 0} onClick={() => void sendCode()}>
                {countdown > 0 ? t('resendIn', { seconds: countdown }) : t('resend')}
              </button>
            </>
          )}
          <button type="button" className="w-full text-base text-gray-600 underline dark:text-gray-400" disabled={busy} onClick={() => { setChallenge(null); setError(null); setLocked(false) }}>
            {t('changeNumber')}
          </button>
        </form>
      )}
    </div>
  )
}
