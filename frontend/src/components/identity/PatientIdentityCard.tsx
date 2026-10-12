'use client'

import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useTranslations } from 'next-intl'
import { toast } from 'react-hot-toast'
import { BadgeCheck, KeyRound, Loader2, Printer, ShieldAlert, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useDateFormat } from '@/lib/i18n/date'
import { errorMessage } from '@/lib/apiErrors'
import { useAuthStore } from '@/store/authStore'
import { useCreateClaimCode, useCreatePortalCode, usePatientIdentity, useRevokeIdentity } from '@/lib/hooks/useIdentity'
import type { Patient } from '@/types/patient'
import type { ClaimCode } from '@/types/identity'
import { PhoneVerificationDialog } from './PhoneVerificationDialog'

/** Everything outside the printed slip is hidden while printing (the slip is portalled to <body>). */
const PRINT_CSS = '@media print { body > *:not([data-claim-print]) { display: none !important; } }'

export function PatientIdentityCard({ patient }: { patient: Patient }) {
  const t = useTranslations('identityUi')
  const { fmt } = useDateFormat()
  const isDoctor = useAuthStore((s) => s.user?.role) === 'doctor'
  const { data: status, isLoading, isError, refetch } = usePatientIdentity(patient.id)
  const createCode = useCreateClaimCode(patient.id)
  const portalCodeMut = useCreatePortalCode(patient.id)
  const revoke = useRevokeIdentity(patient.id)

  const [verifyOpen, setVerifyOpen] = useState(false)
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [note, setNote] = useState('')
  const [claim, setClaim] = useState<ClaimCode | null>(null)
  const [portal, setPortal] = useState<ClaimCode | null>(null)
  // read when the code is created: window is not available while server-rendering
  const [origin, setOrigin] = useState('')

  const makeCode = async () => {
    try {
      const created = await createCode.mutateAsync()
      setOrigin(window.location.origin)
      setClaim(created)
    } catch (err) {
      toast.error(errorMessage(err, t('claimCode.failed')))
    }
  }

  const makePortalCode = async () => {
    try {
      const created = await portalCodeMut.mutateAsync()
      setOrigin(window.location.origin)
      setPortal(created)
    } catch (err) {
      toast.error(errorMessage(err, t('portalCode.failed')))
    }
  }

  const doRevoke = async () => {
    try {
      await revoke.mutateAsync(note.trim() || undefined)
      toast.success(t('revoke.success'))
      setRevokeOpen(false)
      setNote('')
    } catch (err) {
      toast.error(errorMessage(err, t('revoke.failed')))
    }
  }

  // the printed slip is the code that is on screen
  const slip = portal ? { kind: 'portal' as const, code: portal } : claim ? { kind: 'claim' as const, code: claim } : null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          {t('card.title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" aria-label={t('card.loading')} />}

        {isError && (
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span>{t('card.loadFailed')}</span>
            <Button size="sm" variant="outline" onClick={() => refetch()}>{t('card.retry')}</Button>
          </div>
        )}

        {status && status.level === 1 && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-emerald-600 hover:bg-emerald-600">
                <BadgeCheck className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                {t('card.level1Title')}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {t('card.level1Body')}
              {status.profile_display_name ? ` ${t('card.linkedProfile', { name: status.profile_display_name })}` : ''}
            </p>
            {(status.linked_at || status.method) && (
              <p className="text-sm">
                {status.linked_at && t('card.verifiedOn', { date: fmt(status.linked_at, 'MMM d, yyyy') })}
                {status.linked_at && status.method ? ' · ' : ''}
                {status.method === 'clinic_otp' && t('card.methodClinic')}
                {status.method === 'claim_code' && t('card.methodClaim')}
              </p>
            )}
            <p className="text-sm">
              {status.portal_access ? t('portalCode.visible') : t('portalCode.notVisible')}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" onClick={makePortalCode} disabled={portalCodeMut.isLoading}>
                {portalCodeMut.isLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <KeyRound className="mr-2 h-4 w-4" aria-hidden="true" />
                )}
                {t('portalCode.give')}
              </Button>
              {isDoctor && (
                <Button variant="outline" size="sm" onClick={() => setRevokeOpen(true)}>
                  {t('revoke.button')}
                </Button>
              )}
            </div>
            {portal && (
              <div className="space-y-3 rounded-lg border-2 border-dashed p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('portalCode.heading')}</p>
                <p className="font-mono text-4xl font-bold tracking-widest" data-testid="portal-code">{portal.code}</p>
                <p className="text-sm text-muted-foreground">{t('claimCode.expires', { date: fmt(portal.expires_at, 'MMM d, yyyy, h:mm a') })}</p>
                <p className="text-sm">{t('portalCode.explain', { origin })}</p>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => window.print()}>
                    <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                    {t('claimCode.print')}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setPortal(null)}>{t('claimCode.hide')}</Button>
                </div>
              </div>
            )}
          </div>
        )}

        {status && status.level === 0 && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">
                <ShieldAlert className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                {t('card.level0Title')}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">{t('card.level0Body')}</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => setVerifyOpen(true)}>
                <ShieldCheck className="mr-2 h-4 w-4" aria-hidden="true" />
                {t('card.verifyPhone')}
              </Button>
              <Button size="sm" variant="outline" onClick={makeCode} disabled={createCode.isLoading}>
                {createCode.isLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <KeyRound className="mr-2 h-4 w-4" aria-hidden="true" />
                )}
                {t('card.giveClaimCode')}
              </Button>
            </div>

            {claim && (
              <div className="space-y-3 rounded-lg border-2 border-dashed p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('claimCode.heading')}</p>
                <p className="font-mono text-4xl font-bold tracking-widest" data-testid="claim-code">{claim.code}</p>
                <p className="text-sm text-muted-foreground">{t('claimCode.expires', { date: fmt(claim.expires_at, 'MMM d, yyyy, h:mm a') })}</p>
                <p className="text-sm">{t('claimCode.explain', { origin })}</p>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => window.print()}>
                    <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                    {t('claimCode.print')}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setClaim(null)}>{t('claimCode.hide')}</Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>

      {slip &&
        createPortal(
          <div data-claim-print className="hidden bg-white p-10 text-black print:block">
            <style>{PRINT_CSS}</style>
            <h1 className="text-2xl font-bold">{t(slip.kind === 'portal' ? 'portalCode.slipTitle' : 'claimCode.slipTitle')}</h1>
            <p className="mt-6 font-mono text-5xl font-bold tracking-widest">{slip.code.code}</p>
            <p className="mt-6 text-lg">{t(slip.kind === 'portal' ? 'portalCode.explain' : 'claimCode.explain', { origin })}</p>
            <p className="mt-4 text-base">{t('claimCode.expires', { date: fmt(slip.code.expires_at, 'MMM d, yyyy, h:mm a') })}</p>
          </div>,
          document.body
        )}

      <PhoneVerificationDialog
        mode="link"
        open={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        patient={patient}
        initialPhone={patient.phone ?? ''}
        initialName={patient.full_name}
      />

      <Dialog open={revokeOpen} onOpenChange={(o) => { if (!o && !revoke.isLoading) setRevokeOpen(false) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('revoke.title')}</DialogTitle>
            <DialogDescription>{t('revoke.body')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="revoke-note">{t('revoke.noteLabel')}</Label>
            <Textarea id="revoke-note" rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setRevokeOpen(false)} disabled={revoke.isLoading}>{t('revoke.cancel')}</Button>
            <Button variant="destructive" onClick={doRevoke} disabled={revoke.isLoading}>
              {revoke.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
              {t('revoke.confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
