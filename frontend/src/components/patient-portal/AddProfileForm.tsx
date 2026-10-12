'use client'

import { useState, type FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { identityError } from '@/components/identity/identityUtils'
import { useAddPortalProfile } from '@/lib/hooks/usePatientPortal'
import type { PortalProfile } from '@/types/patientPortal'
import type { PortalProfileInput } from '@/types/appointmentRequest'
import { isoDateFromToday, isUnauthorized, portalButton, portalButtonOutline, portalErrorBox, portalInput, portalLabel } from './portalUtils'

type Gender = 'male' | 'female' | 'other'
const GENDERS: Gender[] = ['male', 'female', 'other']

interface Props {
  /** True when this account already has its own ("self") profile: then only a child can be added */
  hasSelf: boolean
  /** Unique per place on the page, so two forms never share element ids */
  idPrefix: string
  onAdded: (profile: PortalProfile) => void
  onCancel?: () => void
  onSignedOut: (expired: boolean) => void
}

/** Add yourself or a child under 18 to the portal account. Shared by the dashboard and the practitioner page. */
export function AddProfileForm({ hasSelf, idPrefix, onAdded, onCancel, onSignedOut }: Props) {
  const t = useTranslations('patientPortalUi.addProfile')
  const add = useAddPortalProfile()
  const [relationship, setRelationship] = useState<'self' | 'child'>(hasSelf ? 'child' : 'self')
  const [name, setName] = useState('')
  const [ageMode, setAgeMode] = useState<'dob' | 'year'>('dob')
  const [dob, setDob] = useState('')
  const [year, setYear] = useState('')
  const [gender, setGender] = useState<Gender | ''>('')
  const [error, setError] = useState<string | null>(null)

  const isChild = relationship === 'child'
  const thisYear = new Date().getFullYear()

  function validate(): string | null {
    if (name.trim().length < 2) return t('errors.name')
    if (ageMode === 'dob') {
      if (!dob) return t('errors.dob')
      if (dob > isoDateFromToday(0)) return t('errors.dobFuture')
      if (isChild && dob <= isoDateFromToday(0).replace(/^\d{4}/, String(thisYear - 18))) return t('errors.childUnder18')
    } else {
      const y = Number(year)
      if (!/^\d{4}$/.test(year) || y < 1900 || y > thisYear) return t('errors.year')
      if (isChild && thisYear - y > 18) return t('errors.childUnder18')
    }
    if (!gender) return t('errors.gender')
    return null
  }

  function message(err: unknown): string {
    const { code, status } = identityError(err)
    if (code === 'self_profile_exists') return t('errors.selfExists')
    if (code === 'child_must_be_under_18') return t('errors.childUnder18')
    if (code === 'profile_limit') return t('errors.profileLimit')
    if (status === 422) return t('errors.invalid')
    return t('errors.generic')
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    const problem = validate()
    setError(problem)
    if (problem) return
    const input: PortalProfileInput = {
      display_name: name.trim(),
      date_of_birth: ageMode === 'dob' ? dob : null,
      approx_birth_year: ageMode === 'year' ? Number(year) : null,
      gender: gender || null,
      relationship,
    }
    try {
      onAdded(await add.mutateAsync(input))
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      setError(message(err))
    }
  }

  const id = (s: string) => `${idPrefix}-${s}`

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      {!hasSelf && (
        <fieldset className="space-y-2">
          <legend className={portalLabel}>{t('whoLabel')}</legend>
          {(['self', 'child'] as const).map((r) => (
            <label key={r} className="flex min-h-11 items-center gap-2 text-base">
              <input type="radio" name={id('who')} checked={relationship === r} onChange={() => setRelationship(r)} disabled={add.isLoading} />
              {t(`who.${r}`)}
            </label>
          ))}
        </fieldset>
      )}
      {isChild && <p className="text-base text-gray-600 dark:text-gray-400">{t('childNote')}</p>}

      <div>
        <label htmlFor={id('name')} className={portalLabel}>{isChild ? t('childName') : t('yourName')}</label>
        <input id={id('name')} className={portalInput} value={name} maxLength={255} autoComplete={isChild ? 'off' : 'name'} onChange={(e) => setName(e.target.value)} disabled={add.isLoading} />
      </div>

      <fieldset className="space-y-2">
        <legend className={portalLabel}>{t('ageLabel')}</legend>
        <div className="flex flex-wrap gap-4">
          {(['dob', 'year'] as const).map((m) => (
            <label key={m} className="flex min-h-11 items-center gap-2 text-base">
              <input type="radio" name={id('age')} checked={ageMode === m} onChange={() => setAgeMode(m)} disabled={add.isLoading} />
              {t(`ageMode.${m}`)}
            </label>
          ))}
        </div>
        {ageMode === 'dob' ? (
          <input id={id('dob')} type="date" aria-label={t('ageMode.dob')} className={portalInput} value={dob} max={isoDateFromToday(0)} onChange={(e) => setDob(e.target.value)} disabled={add.isLoading} />
        ) : (
          <input id={id('year')} inputMode="numeric" aria-label={t('ageMode.year')} className={portalInput} placeholder={t('yearPlaceholder')} maxLength={4} value={year} onChange={(e) => setYear(e.target.value.replace(/\D/g, '').slice(0, 4))} disabled={add.isLoading} />
        )}
      </fieldset>

      <div>
        <label htmlFor={id('gender')} className={portalLabel}>{t('genderLabel')}</label>
        <select id={id('gender')} className={portalInput} value={gender} onChange={(e) => setGender(e.target.value as Gender | '')} disabled={add.isLoading}>
          <option value="">{t('genderChoose')}</option>
          {GENDERS.map((g) => <option key={g} value={g}>{t(`gender.${g}`)}</option>)}
        </select>
      </div>

      {error && <p role="alert" className={portalErrorBox}>{error}</p>}

      <div className="flex flex-wrap gap-2">
        <button type="submit" className={`${portalButton} sm:w-auto`} disabled={add.isLoading}>{add.isLoading ? t('saving') : t('save')}</button>
        {onCancel && <button type="button" className={portalButtonOutline} onClick={onCancel} disabled={add.isLoading}>{t('cancel')}</button>}
      </div>
    </form>
  )
}
