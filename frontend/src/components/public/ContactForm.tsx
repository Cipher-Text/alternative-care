'use client'

import Link from 'next/link'
import { useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { sendContactMessage } from '@/lib/api/contact'
import { CONTACT_TOPICS, type ContactTopic } from '@/types/contact'

type Field = 'name' | 'email' | 'phone' | 'contact' | 'message' | 'consent'
type Errors = Partial<Record<Field, string>>

const TOPIC_KEY: Record<ContactTopic, string> = {
  general: 'topicGeneral',
  enterprise: 'topicEnterprise',
  billing: 'topicBilling',
  report_profile: 'topicReportProfile',
  other: 'topicOther',
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** Public contact form. Not a support ticket: no reply time is promised. */
export function ContactForm({ initialTopic = 'general', practitioner }: { initialTopic?: ContactTopic; practitioner?: string }) {
  const t = useTranslations('publicContactUi')
  const [topic, setTopic] = useState<ContactTopic>(initialTopic)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [organisation, setOrganisation] = useState('')
  const [message, setMessage] = useState(() =>
    initialTopic === 'report_profile' && practitioner ? `${t('aboutProfile', { slug: practitioner })}\n\n` : ''
  )
  const [consent, setConsent] = useState(false)
  const [website, setWebsite] = useState('') // honeypot
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const next: Errors = {}
    const em = email.trim()
    const ph = phone.trim()
    const msg = message.trim()
    if (!name.trim()) next.name = t('errorName')
    if (!em && !ph) next.contact = t('errorContact')
    if (em && !EMAIL_RE.test(em)) next.email = t('errorEmail')
    if (ph && ph.replace(/\D/g, '').length < 8) next.phone = t('errorPhone')
    if (msg.length < 10) next.message = t('errorMessageShort')
    else if (msg.length > 2000) next.message = t('errorMessageLong')
    if (!consent) next.consent = t('errorConsent')
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length) return

    setLoading(true)
    try {
      await sendContactMessage({
        topic,
        name: name.trim(),
        email: em || undefined,
        phone: ph || undefined,
        organisation: topic === 'enterprise' && organisation.trim() ? organisation.trim() : undefined,
        message: msg,
        consent: true,
        website,
      })
      setDone(true)
    } catch (err) {
      const e2 = err as Error & { status?: number }
      setFormError(e2.status === 429 ? t('error429') : e2.message || t('errorGeneric'))
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

  const input = 'mt-1 block w-full rounded-md border border-gray-300 bg-background px-3 py-2 text-sm dark:border-slate-700'
  const label = 'text-sm font-medium text-gray-900 dark:text-white'
  const hint = 'mt-1 text-xs text-gray-600 dark:text-gray-400'
  const errText = 'mt-1 text-xs text-red-600 dark:text-red-400'

  return (
    <form onSubmit={onSubmit} noValidate className="relative space-y-4">
      <div>
        <label htmlFor="contact-topic" className={label}>{t('topic')}</label>
        <select id="contact-topic" className={input} value={topic} onChange={(e) => setTopic(e.target.value as ContactTopic)} disabled={loading}>
          {CONTACT_TOPICS.map((value) => (
            <option key={value} value={value}>{t(TOPIC_KEY[value])}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="contact-name" className={label}>{t('name')}</label>
        <input id="contact-name" className={input} value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoComplete="name" aria-invalid={!!errors.name} disabled={loading} />
        {errors.name && <p className={errText}>{errors.name}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="contact-email" className={label}>{t('email')}</label>
          <input id="contact-email" type="email" className={input} value={email} onChange={(e) => setEmail(e.target.value)} maxLength={254} autoComplete="email" aria-invalid={!!errors.email} disabled={loading} />
          {errors.email && <p className={errText}>{errors.email}</p>}
        </div>
        <div>
          <label htmlFor="contact-phone" className={label}>{t('phone')}</label>
          <input id="contact-phone" type="tel" inputMode="tel" className={input} value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={20} autoComplete="tel" aria-invalid={!!errors.phone} disabled={loading} />
          {errors.phone && <p className={errText}>{errors.phone}</p>}
        </div>
      </div>
      <p className={hint}>{t('replyHint')}</p>
      {errors.contact && <p className={errText} role="alert">{errors.contact}</p>}

      {topic === 'enterprise' && (
        <div>
          <label htmlFor="contact-org" className={label}>{t('organisation')}</label>
          <input id="contact-org" className={input} value={organisation} onChange={(e) => setOrganisation(e.target.value)} maxLength={160} autoComplete="organization" disabled={loading} />
          <p className={hint}>{t('enterpriseHint')}</p>
        </div>
      )}

      <div>
        <label htmlFor="contact-message" className={label}>{t('message')}</label>
        <textarea id="contact-message" className={input} rows={6} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={2000} aria-invalid={!!errors.message} disabled={loading} />
        <p className={hint}>{t('messageHint')}</p>
        {errors.message && <p className={errText}>{errors.message}</p>}
      </div>

      {/* Honeypot: people never see or fill this; bots often do. */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
        <input type="text" name="website" tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
      </div>

      <div>
        <label className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
          <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} aria-invalid={!!errors.consent} disabled={loading} />
          <span>
            {t('consent')}{' '}
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

      <button type="submit" disabled={loading} className="w-full rounded-md bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 sm:w-auto">
        {loading ? t('sending') : t('send')}
      </button>
    </form>
  )
}
