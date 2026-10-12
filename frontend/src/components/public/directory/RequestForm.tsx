'use client'

import Link from 'next/link'
import { useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { submitContactRequest } from '@/lib/api/publicDirectory'

type Errors = Partial<Record<'name' | 'phone' | 'consent', string>>

/** "Request a call back" form. Not a booking; the clinic calls the patient. */
export function RequestForm({ slug, clinicName, title }: { slug: string; clinicName: string; title?: string }) {
  const t = useTranslations('publicPractitionersUi')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [time, setTime] = useState('')
  const [message, setMessage] = useState('')
  const [consent, setConsent] = useState(false)
  const [website, setWebsite] = useState('') // honeypot
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const next: Errors = {}
    if (!name.trim()) next.name = t('errorName')
    if (phone.replace(/\D/g, '').length < 8) next.phone = t('errorPhone')
    if (!consent) next.consent = t('errorConsent')
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length) return

    setLoading(true)
    try {
      await submitContactRequest(slug, {
        patient_name: name.trim(),
        patient_phone: phone.trim(),
        preferred_time: time.trim() || undefined,
        message: message.trim() || undefined,
        consent: true,
        website,
      })
      setDone(true)
    } catch (err) {
      const status = (err as Error & { status?: number }).status
      setFormError(
        status === 429 ? t('error429') : status === 409 ? t('error409') : status === 404 ? t('error404') : t('errorGeneric')
      )
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
        {t('success')}
      </div>
    )
  }

  const input =
    'mt-1 block w-full rounded-md border border-gray-300 bg-background px-3 py-2 text-sm dark:border-slate-700'
  const errText = 'mt-1 text-xs text-red-600 dark:text-red-400'

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title ?? t('requestTitle')}</h2>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{t('requestIntro')}</p>
      </div>

      <div>
        <label htmlFor="req-name" className="text-sm font-medium text-gray-900 dark:text-white">{t('fieldName')}</label>
        <input id="req-name" className={input} value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoComplete="name" aria-invalid={!!errors.name} disabled={loading} />
        {errors.name && <p className={errText}>{errors.name}</p>}
      </div>

      <div>
        <label htmlFor="req-phone" className="text-sm font-medium text-gray-900 dark:text-white">{t('fieldPhone')}</label>
        <input id="req-phone" type="tel" inputMode="tel" className={input} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t('fieldPhoneHint')} maxLength={20} autoComplete="tel" aria-invalid={!!errors.phone} disabled={loading} />
        {errors.phone && <p className={errText}>{errors.phone}</p>}
      </div>

      <div>
        <label htmlFor="req-time" className="text-sm font-medium text-gray-900 dark:text-white">{t('fieldTime')}</label>
        <input id="req-time" className={input} value={time} onChange={(e) => setTime(e.target.value)} placeholder={t('fieldTimePlaceholder')} maxLength={120} disabled={loading} />
      </div>

      <div>
        <label htmlFor="req-message" className="text-sm font-medium text-gray-900 dark:text-white">{t('fieldMessage')}</label>
        <textarea id="req-message" className={input} rows={3} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={1000} disabled={loading} />
      </div>

      {/* Honeypot: people never see or fill this; bots often do. */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
        <input type="text" name="website" tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
      </div>

      <div>
        <label className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
          <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} aria-invalid={!!errors.consent} disabled={loading} />
          <span>
            {t('consent', { clinic: clinicName })}{' '}
            <Link href="/privacy" className="text-emerald-700 underline dark:text-emerald-400">{t('consentPrivacy')}</Link>
          </span>
        </label>
        {errors.consent && <p className={errText}>{errors.consent}</p>}
      </div>

      {formError && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {formError}
        </p>
      )}

      <button type="submit" disabled={loading} className="w-full rounded-md bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">
        {loading ? t('submitting') : t('submit')}
      </button>
    </form>
  )
}
