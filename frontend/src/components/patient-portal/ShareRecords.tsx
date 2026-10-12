'use client'

import { useMemo, useState } from 'react'
import { addDays } from 'date-fns'
import { useTranslations } from 'next-intl'
import { Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useDateFormat } from '@/lib/i18n/date'
import { identityError } from '@/components/identity/identityUtils'
import { useCreateShare, usePortalShares, useRevokeShare } from '@/lib/hooks/useSharing'
import { SHARE_CATEGORIES, SHARE_DAYS } from '@/types/sharing'
import type { PortalShare, ShareCategory, ShareDays, ShareStatus } from '@/types/sharing'
import type { PortalProfile } from '@/types/patientPortal'
import { isUnauthorized, portalButton, portalButtonOutline, portalErrorBox, portalLabel } from './portalUtils'

const card = 'rounded-lg border border-gray-200 p-4 dark:border-slate-800'
const select =
  'mt-1 block w-full rounded-md border border-gray-300 bg-background px-3 py-3 text-base dark:border-slate-700'
const STATUS_STYLE: Record<ShareStatus, string> = {
  active: 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200',
  expired: 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-gray-200',
  revoked: 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-gray-200',
  ended: 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
}

/** The "Share my records" section for one profile (ADR 009 phase 4). */
export function ShareRecords({ profile, onSignedOut }: { profile: PortalProfile; onSignedOut: (expired: boolean) => void }) {
  const t = useTranslations('sharingUi')
  const { fmt } = useDateFormat()
  const canShare = profile.clinics.length >= 2
  const shares = usePortalShares(canShare)
  const revoke = useRevokeShare()
  const [creating, setCreating] = useState(false)
  const [stopTarget, setStopTarget] = useState<PortalShare | null>(null)
  const [stopError, setStopError] = useState<string | null>(null)

  const mine = useMemo(
    () => (shares.data ?? []).filter((s) => s.profile_id === profile.id).sort((a, b) => b.created_at.localeCompare(a.created_at)),
    [shares.data, profile.id]
  )

  const categoryList = (cats: ShareCategory[]) => cats.map((c) => t(`categories.${c}`)).join(t('listJoin'))

  const doStop = async () => {
    if (!stopTarget) return
    try {
      await revoke.mutateAsync(stopTarget.id)
      setStopTarget(null)
      setStopError(null)
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      setStopError(identityError(err).status === 404 ? t('portal.stopMissing') : t('portal.stopFailed'))
    }
  }

  return (
    <section className={`${card} space-y-3`} aria-labelledby="share-records-heading">
      <h2 id="share-records-heading" className="text-xl font-semibold text-gray-900 dark:text-white">{t('portal.heading')}</h2>

      {!canShare ? (
        <p className="text-base text-gray-700 dark:text-gray-300">{t('portal.needTwo')}</p>
      ) : (
        <>
          <p className="text-base text-gray-700 dark:text-gray-300">{t('portal.intro')}</p>
          <p className="text-base font-medium text-gray-900 dark:text-white">{t('dialog.neverShared')}</p>

          {shares.isLoading && <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label={t('portal.loading')} />}
          {shares.isError && (
            isUnauthorized(shares.error) ? null : (
              <div role="alert" className={portalErrorBox}>
                <p>{t('portal.loadFailed')}</p>
                <button type="button" className={`${portalButtonOutline} mt-2`} onClick={() => void shares.refetch()}>{t('portal.retry')}</button>
              </div>
            )
          )}

          {shares.data && (
            <>
              <h3 className="text-base font-medium text-gray-700 dark:text-gray-300">{t('portal.listHeading')}</h3>
              {mine.length === 0 ? (
                <p className="text-base text-gray-600 dark:text-gray-400">{t('portal.none')}</p>
              ) : (
                <ul className="space-y-2">
                  {mine.map((s) => (
                    <li key={s.id} className="space-y-1 rounded-md bg-gray-50 p-3 dark:bg-slate-900">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-base font-medium">{t('portal.route', { source: s.source_clinic, recipient: s.recipient_clinic })}</span>
                        <span className={`rounded-full px-2 py-0.5 text-sm ${STATUS_STYLE[s.status]}`}>{t(`status.${s.status}`)}</span>
                      </div>
                      <p className="text-base text-gray-700 dark:text-gray-300">{categoryList(s.categories)}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{t('portal.untilDate', { date: fmt(s.expires_at, 'MMM d, yyyy') })}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {s.access_count > 0 && s.last_accessed_at
                          ? t('portal.readCount', { count: s.access_count, date: fmt(s.last_accessed_at, 'MMM d, yyyy, h:mm a') })
                          : t('portal.notOpened')}
                      </p>
                      {s.status === 'active' && (
                        <button type="button" className={`${portalButtonOutline} mt-1 py-2`} onClick={() => { setStopError(null); setStopTarget(s) }}>
                          {t('portal.stop')}
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <button type="button" className={portalButton} onClick={() => setCreating(true)}>{t('portal.new')}</button>
            </>
          )}
        </>
      )}

      <Dialog open={!!stopTarget} onOpenChange={(o) => { if (!o && !revoke.isLoading) setStopTarget(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('portal.stopTitle', { recipient: stopTarget?.recipient_clinic ?? '' })}</DialogTitle>
            <DialogDescription>{t('portal.stopBody', { recipient: stopTarget?.recipient_clinic ?? '', source: stopTarget?.source_clinic ?? '' })}</DialogDescription>
          </DialogHeader>
          {stopError && <p role="alert" className={portalErrorBox}>{stopError}</p>}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setStopTarget(null)} disabled={revoke.isLoading}>{t('portal.keep')}</Button>
            <Button variant="destructive" onClick={doStop} disabled={revoke.isLoading}>
              {revoke.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('portal.stopConfirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {creating && <CreateShareDialog profile={profile} categoryList={categoryList} onClose={() => setCreating(false)} onSignedOut={onSignedOut} />}
    </section>
  )
}

function CreateShareDialog({
  profile,
  categoryList,
  onClose,
  onSignedOut,
}: {
  profile: PortalProfile
  categoryList: (cats: ShareCategory[]) => string
  onClose: () => void
  onSignedOut: (expired: boolean) => void
}) {
  const t = useTranslations('sharingUi')
  const { fmt } = useDateFormat()
  const create = useCreateShare()
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [cats, setCats] = useState<ShareCategory[]>([])
  const [days, setDays] = useState<ShareDays>(30)
  const [consent, setConsent] = useState(false)
  const [errorCode, setErrorCode] = useState<string | null>(null)

  const fromClinic = profile.clinics.find((c) => c.link_id === from)
  const toClinic = profile.clinics.find((c) => c.link_id === to)
  const same = !!from && from === to
  const ready = !!fromClinic && !!toClinic && !same && cats.length > 0
  // the server fixes the exact end time; this is the day it will show
  const until = fmt(addDays(new Date(), days), 'MMM d, yyyy')
  const ordered = SHARE_CATEGORIES.filter((c) => cats.includes(c))
  const vars = { to: toClinic?.clinic_name ?? '', from: fromClinic?.clinic_name ?? '', person: profile.display_name, date: until }

  const toggle = (c: ShareCategory) => {
    setConsent(false)
    setCats((cur) => (cur.includes(c) ? cur.filter((x) => x !== c) : [...cur, c]))
  }
  // any change to what is shared clears the consent, so it always matches what is on screen
  const changed = <T,>(set: (v: T) => void) => (v: T) => { setConsent(false); setErrorCode(null); set(v) }

  const submit = async () => {
    if (!ready || !consent || create.isLoading) return
    setErrorCode(null)
    try {
      await create.mutateAsync({ source_link_id: from, recipient_link_id: to, categories: ordered, days, consent: true })
      toast.success(t('dialog.done'))
      onClose()
    } catch (err) {
      if (isUnauthorized(err)) return onSignedOut(true)
      const { code, status } = identityError(err)
      setErrorCode(code ?? (status === 404 ? 'not_found' : 'generic'))
    }
  }

  const errorText: Record<string, string> = {
    share_exists: t('dialog.shareExists'),
    different_people: t('dialog.differentPeople'),
    same_clinic: t('dialog.same'),
    not_found: t('dialog.notFound'),
    generic: t('dialog.failed'),
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o && !create.isLoading) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t('dialog.title')}</DialogTitle>
          <DialogDescription>{t('dialog.intro', { person: profile.display_name })}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label htmlFor="share-from" className={portalLabel}>{t('dialog.from')}</label>
            <select id="share-from" className={select} value={from} onChange={(e) => changed(setFrom)(e.target.value)} disabled={create.isLoading}>
              <option value="">{t('dialog.choose')}</option>
              {profile.clinics.map((c) => <option key={c.link_id} value={c.link_id}>{c.clinic_name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="share-to" className={portalLabel}>{t('dialog.to')}</label>
            <select id="share-to" className={select} value={to} onChange={(e) => changed(setTo)(e.target.value)} disabled={create.isLoading}>
              <option value="">{t('dialog.choose')}</option>
              {profile.clinics.map((c) => <option key={c.link_id} value={c.link_id}>{c.clinic_name}</option>)}
            </select>
            {same && <p role="alert" className="mt-1 text-sm text-red-700 dark:text-red-300">{t('dialog.sameClinic')}</p>}
          </div>

          <fieldset className="space-y-2">
            <legend className={portalLabel}>{t('dialog.what')}</legend>
            {SHARE_CATEGORIES.map((c) => (
              <label key={c} className="flex items-start gap-3 rounded-md border border-gray-200 p-3 dark:border-slate-800">
                <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" checked={cats.includes(c)} onChange={() => toggle(c)} disabled={create.isLoading} />
                <span>
                  <span className="block text-base font-medium">{t(`categories.${c}`)}</span>
                  <span className="block text-sm text-gray-600 dark:text-gray-400">{t(`categoryHelp.${c}`)}</span>
                </span>
              </label>
            ))}
            {cats.length === 0 && <p className="text-sm text-gray-600 dark:text-gray-400">{t('dialog.atLeastOne')}</p>}
            <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-base font-medium text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
              {t('dialog.neverShared')}
            </p>
          </fieldset>

          <div>
            <label htmlFor="share-days" className={portalLabel}>{t('dialog.howLong')}</label>
            <select id="share-days" className={select} value={days} onChange={(e) => changed<ShareDays>(setDays)(Number(e.target.value) as ShareDays)} disabled={create.isLoading}>
              {SHARE_DAYS.map((d) => <option key={d} value={d}>{t('dialog.days', { days: d })}</option>)}
            </select>
          </div>

          {ready && (
            <div className="space-y-3 rounded-md border border-gray-300 p-3 dark:border-slate-700">
              <p className="text-base font-medium">{t('dialog.summary', { ...vars, categories: categoryList(ordered) })}</p>
              <label className="flex items-start gap-3">
                <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" checked={consent} onChange={(e) => setConsent(e.target.checked)} disabled={create.isLoading} />
                <span className="text-base">{t('dialog.consent', vars)}</span>
              </label>
            </div>
          )}
          {!ready && !same && <p className="text-sm text-gray-600 dark:text-gray-400">{t('dialog.needClinics')}</p>}

          {errorCode === 'recent_sign_in_required' && (
            <div role="alert" className={`${portalErrorBox} space-y-2`}>
              <p>{t('dialog.recentSignIn')}</p>
              <button type="button" className={portalButtonOutline} onClick={() => onSignedOut(false)}>{t('dialog.signInAgain')}</button>
            </div>
          )}
          {errorCode && errorCode !== 'recent_sign_in_required' && (
            <p role="alert" className={portalErrorBox}>{errorText[errorCode] ?? errorText.generic}</p>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={create.isLoading}>{t('dialog.cancel')}</Button>
          <Button onClick={submit} disabled={!ready || !consent || create.isLoading}>
            {create.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
            {t('dialog.submit')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
