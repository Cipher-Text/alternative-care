'use client'

import { useEffect, useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { claimApi } from '@/lib/api/identity'
import { identityError, normalizeBdPhone } from '@/components/identity/identityUtils'
import { RELATIONSHIPS, type ClaimResult, type Relationship, type VerifyRequestResponse } from '@/types/identity'

const input =
  'mt-1 block w-full rounded-md border border-gray-300 bg-background px-4 py-3 text-lg dark:border-slate-700'
const button =
  'w-full rounded-md bg-emerald-600 px-4 py-3 text-base font-semibold text-white hover:bg-emerald-700 disabled:opacity-60'
const label = 'text-base font-medium text-gray-900 dark:text-white'

export default function ClaimPage() {
  const t = useTranslations('identityUi.claim')
  const [phone, setPhone] = useState('')
  const [claimCode, setClaimCode] = useState('')
  const [challenge, setChallenge] = useState<VerifyRequestResponse | null>(null)
  const [code, setCode] = useState('')
  const [relationship, setRelationship] = useState<Relationship>('self')
  const [consent, setConsent] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ClaimResult | null>(null)

  useEffect(() => {
    if (countdown <= 0) return
    const id = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000)
    return () => clearInterval(id)
  }, [countdown])

  function message(err: unknown): string {
    const { code: c, status } = identityError(err)
    switch (c) {
      case 'invalid_claim_code': return t('errors.invalidClaimCode')
      case 'otp_invalid': return t('errors.otpInvalid')
      case 'otp_expired': return t('errors.otpExpired')
      case 'otp_locked': return t('errors.otpLocked')
      case 'otp_cooldown': return t('errors.otpCooldown')
      case 'otp_phone_limit':
      case 'otp_clinic_daily_cap': return t('errors.tooMany')
      case 'clinic_unavailable': return t('errors.clinicUnavailable')
      case 'already_linked': return t('errors.alreadyLinked')
      case 'profile_already_linked_here': return t('errors.profileAlreadyLinkedHere')
      case 'profile_limit': return t('errors.profileLimit')
    }
    if (status === 429) return t('errors.tooMany')
    if (status === 503) return t('errors.smsUnavailable')
    return t('errors.generic')
  }

  async function sendCode(e?: FormEvent) {
    e?.preventDefault()
    const normalized = normalizeBdPhone(phone)
    if (!normalized) return setError(t('errors.phone'))
    if (!claimCode.trim()) return setError(t('errors.claimCodeRequired'))
    setError(null)
    setBusy(true)
    try {
      const res = await claimApi.request(normalized, claimCode.trim().toUpperCase())
      setChallenge(res)
      setCountdown(res.resend_after_seconds)
      setCode('')
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
    if (!consent) return setError(t('errors.consentRequired'))
    setError(null)
    setBusy(true)
    try {
      setResult(await claimApi.confirm(challenge.challenge_id, code, relationship, true))
    } catch (err) {
      setError(message(err))
    } finally {
      setBusy(false)
    }
  }

  const errorBox = error && (
    <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-base text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
      {error}
    </p>
  )

  return (
    <div className="mx-auto w-full max-w-md px-4 py-8 sm:py-12">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>

      {result ? (
        <div role="status" className="mt-6 space-y-2 rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
          <p className="text-lg font-semibold">{t('success', { clinic: result.clinic_name })}</p>
          <p className="text-base">{t('successBody', { name: result.profile_display_name })}</p>
        </div>
      ) : !challenge ? (
        <form onSubmit={sendCode} noValidate className="mt-4 space-y-5">
          <p className="text-base text-gray-600 dark:text-gray-400">{t('intro')}</p>
          <div>
            <label htmlFor="claim-phone" className={label}>{t('phoneLabel')}</label>
            <input id="claim-phone" type="tel" inputMode="tel" autoComplete="tel" className={input} placeholder="01XXXXXXXXX" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={busy} />
          </div>
          <div>
            <label htmlFor="claim-code" className={label}>{t('claimCodeLabel')}</label>
            <input id="claim-code" autoCapitalize="characters" autoComplete="off" spellCheck={false} className={`${input} font-mono uppercase tracking-widest`} placeholder="ABCD-EFGH" value={claimCode} onChange={(e) => setClaimCode(e.target.value)} maxLength={12} disabled={busy} />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('claimCodeHint')}</p>
          </div>
          {errorBox}
          <button type="submit" className={button} disabled={busy}>{busy ? t('sending') : t('sendCode')}</button>
        </form>
      ) : (
        <form onSubmit={confirm} noValidate className="mt-4 space-y-5">
          <p className="text-base text-gray-600 dark:text-gray-400">{t('codeSent', { phone: challenge.phone_masked })}</p>
          <div>
            <label htmlFor="claim-sms" className={label}>{t('smsCodeLabel')}</label>
            <input id="claim-sms" inputMode="numeric" autoComplete="one-time-code" maxLength={6} className={`${input} text-center text-2xl tracking-[0.4em]`} placeholder="000000" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} disabled={busy} />
          </div>
          <fieldset className="space-y-2">
            <legend className={label}>{t('relationshipLabel')}</legend>
            {RELATIONSHIPS.map((r) => (
              <label key={r} className="flex items-center gap-3 rounded-md border border-gray-300 px-4 py-3 text-base dark:border-slate-700">
                <input type="radio" name="relationship" className="h-5 w-5" checked={relationship === r} onChange={() => setRelationship(r)} disabled={busy} />
                {t(`relationship.${r}`)}
              </label>
            ))}
          </fieldset>
          <label className="flex items-start gap-3 text-base text-gray-800 dark:text-gray-200">
            <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" checked={consent} onChange={(e) => setConsent(e.target.checked)} disabled={busy} />
            <span>{t('consent')}</span>
          </label>
          {errorBox}
          <button type="submit" className={button} disabled={busy || code.length !== 6 || !consent}>{busy ? t('confirming') : t('confirm')}</button>
          <button type="button" className="w-full rounded-md border border-gray-300 px-4 py-3 text-base disabled:opacity-60 dark:border-slate-700" disabled={busy || countdown > 0} onClick={() => void sendCode()}>
            {countdown > 0 ? t('resendIn', { seconds: countdown }) : t('resend')}
          </button>
        </form>
      )}
    </div>
  )
}
