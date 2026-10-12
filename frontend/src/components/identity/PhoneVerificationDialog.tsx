'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { AlertCircle, CheckCircle2, Loader2, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { identityApi } from '@/lib/api/identity'
import { errorMessage } from '@/lib/apiErrors'
import { useClinicName, useLinkIdentity } from '@/lib/hooks/useIdentity'
import type { Patient } from '@/types/patient'
import {
  RELATIONSHIPS,
  type BasicDetails,
  type LinkResponse,
  type ProfileSummary,
  type Relationship,
  type VerifyConfirmResponse,
  type VerifyRequestResponse,
} from '@/types/identity'
import { identityError, isRelationship, newProfileFromPatient, normalizeBdPhone } from './identityUtils'

/** What the new-patient page gets back: either a chosen profile's basic details or "new person". */
export interface PrefillResult {
  token: string
  /** Basic details of the chosen profile (prefill mode, existing profile) */
  details?: BasicDetails
  /** The patient is a new person: the parent links after saving, using these */
  newPerson?: boolean
  relationship?: Relationship
  approxBirthYear?: number | null
}

interface BaseProps {
  open: boolean
  onClose: () => void
  /** Prefilled into step 1 */
  initialPhone?: string
  /** Prefilled into the name search (it still only runs when staff press Search) */
  initialName?: string
}

type Props =
  | (BaseProps & { mode: 'link'; patient: Patient; onLinked?: (res: LinkResponse) => void })
  | (BaseProps & { mode: 'prefill'; onPrefill: (result: PrefillResult) => void })

type Step = 'phone' | 'code' | 'person' | 'done'
type ScriptLang = 'bn' | 'en'

interface Notice {
  text: string
  /** Extra action shown under the message */
  action?: 'resend' | 'verifyAgain' | 'billing' | 'existing'
  existingPatientId?: string
}

export function PhoneVerificationDialog(props: Props) {
  return (
    <Dialog open={props.open} onOpenChange={(o) => { if (!o) props.onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        {/* mounted only while open, so every opening starts from step 1 */}
        {props.open && <Flow {...props} />}
      </DialogContent>
    </Dialog>
  )
}

function Flow(props: Props) {
  const t = useTranslations('identityUi')
  const clinicName = useClinicName()
  const link = useLinkIdentity()

  const [step, setStep] = useState<Step>('phone')
  const [phone, setPhone] = useState(props.initialPhone ?? '')
  const [phoneError, setPhoneError] = useState(false)
  const [challenge, setChallenge] = useState<VerifyRequestResponse | null>(null)
  const [countdown, setCountdown] = useState(0)
  const [code, setCode] = useState('')
  const [scriptRead, setScriptRead] = useState(false)
  const [scriptLang, setScriptLang] = useState<ScriptLang>('bn')
  const [session, setSession] = useState<VerifyConfirmResponse | null>(null)
  const [name, setName] = useState(props.initialName ?? '')
  const [results, setResults] = useState<ProfileSummary[] | null>(null)
  const [newPerson, setNewPerson] = useState(false)
  const [relationship, setRelationship] = useState<Relationship>('self')
  const [birthYear, setBirthYear] = useState('')
  const [birthYearError, setBirthYearError] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [linked, setLinked] = useState<LinkResponse | null>(null)

  useEffect(() => {
    if (countdown <= 0) return
    const id = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000)
    return () => clearInterval(id)
  }, [countdown])

  const describe = useCallback(
    (error: unknown): Notice => {
      const { code: c, status, retryAfter, existingPatientId } = identityError(error)
      switch (c) {
        case 'otp_invalid': return { text: t('errors.otpInvalid') }
        case 'otp_expired': return { text: t('errors.otpExpired'), action: 'resend' }
        case 'otp_locked': return { text: t('errors.otpLocked'), action: 'resend' }
        case 'otp_cooldown':
          return { text: retryAfter ? t('errors.otpCooldownSeconds', { seconds: retryAfter }) : t('errors.otpCooldown') }
        case 'otp_phone_limit': return { text: t('errors.otpPhoneLimit') }
        case 'otp_clinic_daily_cap': return { text: t('errors.otpClinicDailyCap') }
        case 'plan_limit_reached':
        case 'feature_not_in_plan':
        case 'plan_expired':
          return { text: t('errors.plan'), action: 'billing' }
        case 'invalid_verification': return { text: t('errors.verificationExpired'), action: 'verifyAgain' }
        case 'already_linked': return { text: t('errors.alreadyLinked') }
        case 'profile_already_linked_here':
          return { text: t('errors.profileAlreadyLinkedHere'), action: existingPatientId ? 'existing' : undefined, existingPatientId }
        case 'profile_limit': return { text: t('errors.profileLimit') }
      }
      if (status === 503) return { text: t('errors.smsUnavailable') }
      if (status === 429) return { text: t('errors.tooManyRequests') }
      return { text: errorMessage(error, t('errors.generic')) }
    },
    [t]
  )

  const sendCode = async () => {
    const normalized = normalizeBdPhone(phone)
    if (!normalized) {
      setPhoneError(true)
      return
    }
    setPhoneError(false)
    setNotice(null)
    setBusy(true)
    try {
      const res = await identityApi.requestCode(normalized)
      setChallenge(res)
      setCountdown(res.resend_after_seconds)
      setCode('')
      setStep('code')
    } catch (err) {
      const info = identityError(err)
      if (info.code === 'otp_cooldown' && info.retryAfter && challenge) setCountdown(info.retryAfter)
      setNotice(describe(err))
    } finally {
      setBusy(false)
    }
  }

  const verify = async () => {
    if (!challenge || !scriptRead || code.length !== 6) return
    setNotice(null)
    setBusy(true)
    try {
      const res = await identityApi.confirmCode(challenge.challenge_id, code, true)
      setSession(res)
      setNewPerson(!res.has_profiles)
      setStep('person')
    } catch (err) {
      setCode('')
      setNotice(describe(err))
    } finally {
      setBusy(false)
    }
  }

  const search = async () => {
    if (!session || name.trim().length < 2) return
    setNotice(null)
    setBusy(true)
    try {
      setResults(await identityApi.searchProfiles(session.verification_token, name.trim()))
    } catch (err) {
      setNotice(describe(err))
    } finally {
      setBusy(false)
    }
  }

  const parsedYear = (): number | null | undefined => {
    if (!birthYear.trim()) return null
    const y = Number(birthYear)
    const max = new Date().getFullYear()
    if (!Number.isInteger(y) || y < 1900 || y > max) return undefined
    return y
  }

  const finishLink = async (input: { profileId?: string }) => {
    if (props.mode !== 'link' || !session) return
    let year: number | null = null
    if (!input.profileId) {
      const parsed = parsedYear()
      if (parsed === undefined) {
        setBirthYearError(true)
        return
      }
      year = parsed
    }
    setBirthYearError(false)
    setNotice(null)
    try {
      const res = await link.mutateAsync(
        input.profileId
          ? { verification_token: session.verification_token, patient_id: props.patient.id, profile_id: input.profileId }
          : {
              verification_token: session.verification_token,
              patient_id: props.patient.id,
              new_profile: newProfileFromPatient(props.patient, relationship, year),
            }
      )
      setLinked(res)
      setStep('done')
      props.onLinked?.(res)
    } catch (err) {
      setNotice(describe(err))
    }
  }

  const choose = async (profile: ProfileSummary) => {
    if (!session) return
    if (props.mode === 'link') {
      await finishLink({ profileId: profile.id })
      return
    }
    setNotice(null)
    setBusy(true)
    try {
      const details = await identityApi.prefill(session.verification_token, profile.id)
      props.onPrefill({ token: session.verification_token, details })
      props.onClose()
    } catch (err) {
      setNotice(describe(err))
    } finally {
      setBusy(false)
    }
  }

  const chooseNewPerson = async () => {
    if (!session) return
    if (props.mode === 'link') {
      await finishLink({})
      return
    }
    const year = parsedYear()
    if (year === undefined) {
      setBirthYearError(true)
      return
    }
    props.onPrefill({ token: session.verification_token, newPerson: true, relationship, approxBirthYear: year })
    props.onClose()
  }

  const restart = () => {
    setStep('phone')
    setSession(null)
    setChallenge(null)
    setResults(null)
    setCode('')
    setScriptRead(false)
    setNotice(null)
  }

  const clinic = clinicName ?? t(scriptLang === 'bn' ? 'consent.clinicFallbackBn' : 'consent.clinicFallbackEn')
  const working = busy || link.isLoading
  const showYear = props.mode === 'prefill' || !props.patient.date_of_birth

  const noticeBox = notice && (
    <div role="alert" className="space-y-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
      <p className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{notice.text}</span>
      </p>
      <div className="flex flex-wrap gap-2">
        {notice.action === 'resend' && (
          <Button type="button" size="sm" variant="outline" onClick={sendCode} disabled={working}>
            {t('errors.sendNew')}
          </Button>
        )}
        {notice.action === 'verifyAgain' && (
          <Button type="button" size="sm" variant="outline" onClick={restart}>
            {t('errors.verifyAgain')}
          </Button>
        )}
        {notice.action === 'billing' && (
          <Button type="button" size="sm" variant="outline" asChild>
            <Link href="/billing">{t('errors.openBilling')}</Link>
          </Button>
        )}
        {notice.action === 'existing' && notice.existingPatientId && (
          <Button type="button" size="sm" variant="outline" asChild>
            <Link href={`/patients/${notice.existingPatientId}`}>{t('errors.openExisting')}</Link>
          </Button>
        )}
      </div>
    </div>
  )

  const skip = (
    <Button type="button" variant="ghost" onClick={props.onClose} className="text-muted-foreground">
      {step === 'done' ? t('dialog.close') : t('dialog.skip')}
    </Button>
  )

  return (
    <>
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('dialog.title')}
        </DialogTitle>
        <DialogDescription>{t('dialog.intro')}</DialogDescription>
      </DialogHeader>

      {step === 'phone' && (
        <form
          noValidate
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); void sendCode() }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="idv-phone">{t('phone.label')}</Label>
            <Input
              id="idv-phone"
              type="tel"
              inputMode="tel"
              autoComplete="off"
              placeholder="01XXXXXXXXX"
              value={phone}
              onChange={(e) => { setPhone(e.target.value); setPhoneError(false) }}
              aria-invalid={phoneError}
              disabled={working}
            />
            {phoneError ? (
              <p className="text-sm text-red-600">{t('phone.invalid')}</p>
            ) : (
              <p className="text-xs text-muted-foreground">{t('phone.hint')}</p>
            )}
          </div>
          {noticeBox}
          <DialogFooter className="gap-2 sm:justify-between">
            {skip}
            <Button type="submit" disabled={working || !phone.trim()}>
              {working && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('phone.send')}
            </Button>
          </DialogFooter>
        </form>
      )}

      {step === 'code' && challenge && (
        <form
          noValidate
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); void verify() }}
        >
          <section className="space-y-2 rounded-lg border-2 border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/40">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">{t('consent.title')}</h3>
              <div className="flex gap-1" role="group" aria-label={t('consent.language')}>
                {(['bn', 'en'] as const).map((l) => (
                  <Button
                    key={l}
                    type="button"
                    size="sm"
                    variant={scriptLang === l ? 'default' : 'outline'}
                    className="h-7 px-2 text-xs"
                    aria-pressed={scriptLang === l}
                    onClick={() => setScriptLang(l)}
                  >
                    {t(l === 'bn' ? 'consent.langBn' : 'consent.langEn')}
                  </Button>
                ))}
              </div>
            </div>
            <p lang={scriptLang} className="text-base leading-relaxed text-emerald-950 dark:text-emerald-50">
              {t(scriptLang === 'bn' ? 'consent.scriptBn' : 'consent.scriptEn', { clinic })}
            </p>
          </section>

          <label className="flex items-start gap-2 text-sm font-medium">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4"
              checked={scriptRead}
              onChange={(e) => setScriptRead(e.target.checked)}
              disabled={working}
            />
            <span>{t('code.scriptRead')}</span>
          </label>

          <div className="space-y-1.5">
            <Label htmlFor="idv-code">{t('code.label')}</Label>
            <p className="text-xs text-muted-foreground">{t('code.sentTo', { phone: challenge.phone_masked })}</p>
            <Input
              id="idv-code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="h-12 text-center text-2xl tracking-[0.4em]"
              disabled={working}
            />
            {(!scriptRead || code.length !== 6) && (
              <p className="text-xs text-muted-foreground">{t('code.needBoth')}</p>
            )}
          </div>

          {noticeBox}

          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={sendCode} disabled={working || countdown > 0}>
              {countdown > 0 ? t('code.resendIn', { seconds: countdown }) : t('code.resend')}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={restart} disabled={working}>
              {t('code.changePhone')}
            </Button>
          </div>

          <DialogFooter className="gap-2 sm:justify-between">
            {skip}
            <Button type="submit" disabled={working || !scriptRead || code.length !== 6}>
              {working && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('code.verify')}
            </Button>
          </DialogFooter>
        </form>
      )}

      {step === 'person' && session && (
        <div className="space-y-5">
          <p className="flex items-center gap-2 text-sm text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            {t('person.verified')}
          </p>

          {session.has_profiles && (
            <section className="space-y-3">
              <div>
                <h3 className="text-sm font-semibold">{t('person.findHeading')}</h3>
                <p className="text-xs text-muted-foreground">{t('person.findHelp')}</p>
              </div>
              <form
                noValidate
                className="flex gap-2"
                onSubmit={(e) => { e.preventDefault(); void search() }}
              >
                <Input
                  aria-label={t('person.nameLabel')}
                  placeholder={t('person.nameLabel')}
                  value={name}
                  onChange={(e) => { setName(e.target.value); setResults(null) }}
                  disabled={working}
                />
                <Button type="submit" variant="outline" disabled={working || name.trim().length < 2}>
                  {t('person.search')}
                </Button>
              </form>
              {results && results.length === 0 && (
                <p className="text-sm text-muted-foreground">{t('person.noResults')}</p>
              )}
              {results && results.length > 0 && (
                <ul className="space-y-2">
                  {results.map((p) => (
                    <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3">
                      <div className="space-y-1">
                        <p className="font-medium">{p.display_name}</p>
                        <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                          {p.age_years !== null && <span>{t('person.age', { age: p.age_years })}</span>}
                          {p.gender && <span>{t.has(`person.gender.${p.gender}`) ? t(`person.gender.${p.gender}`) : p.gender}</span>}
                          <Badge variant="outline">{t(`relationship.${p.relationship}`)}</Badge>
                          {p.is_dependent && <Badge variant="secondary">{t('person.dependent')}</Badge>}
                        </div>
                        {p.linked_here && <p className="text-xs text-amber-700 dark:text-amber-400">{t('person.linkedHere')}</p>}
                      </div>
                      <Button type="button" size="sm" disabled={working || p.linked_here} onClick={() => void choose(p)}>
                        {t('person.choose')}
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          <section className="space-y-3 rounded-md border border-dashed p-3">
            {!session.has_profiles && <p className="text-sm text-muted-foreground">{t('person.noProfiles')}</p>}
            {session.has_profiles && !newPerson ? (
              <Button type="button" variant="outline" onClick={() => setNewPerson(true)} disabled={working}>
                {t('person.newPerson')}
              </Button>
            ) : (
              <>
                <h3 className="text-sm font-semibold">{t('person.newPerson')}</h3>
                <p className="text-xs text-muted-foreground">{t('person.newPersonHelp')}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="idv-rel">{t('person.relationshipLabel')}</Label>
                    <Select value={relationship} onValueChange={(v) => { if (isRelationship(v)) setRelationship(v) }}>
                      <SelectTrigger id="idv-rel" aria-label={t('person.relationshipLabel')}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {RELATIONSHIPS.map((r) => (
                          <SelectItem key={r} value={r}>{t(`relationship.${r}`)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {showYear && (
                    <div className="space-y-1.5">
                      <Label htmlFor="idv-year">{t('person.birthYearLabel')}</Label>
                      <Input
                        id="idv-year"
                        inputMode="numeric"
                        maxLength={4}
                        placeholder="1990"
                        value={birthYear}
                        onChange={(e) => { setBirthYear(e.target.value.replace(/\D/g, '')); setBirthYearError(false) }}
                        aria-invalid={birthYearError}
                      />
                      <p className={birthYearError ? 'text-xs text-red-600' : 'text-xs text-muted-foreground'}>
                        {birthYearError ? t('person.birthYearInvalid') : t('person.birthYearHelp')}
                      </p>
                    </div>
                  )}
                </div>
                <Button type="button" onClick={() => void chooseNewPerson()} disabled={working}>
                  {working && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                  {props.mode === 'link' ? t('person.linkAsNew') : t('person.useAsNew')}
                </Button>
              </>
            )}
          </section>

          {noticeBox}
          <DialogFooter>{skip}</DialogFooter>
        </div>
      )}

      {step === 'done' && linked && (
        <div className="space-y-4">
          <div role="status" className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-semibold">{t('done.title')}</p>
              <p>{t('done.body', { name: linked.profile_display_name })}</p>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" onClick={props.onClose}>{t('dialog.close')}</Button>
          </DialogFooter>
        </div>
      )}
    </>
  )
}
