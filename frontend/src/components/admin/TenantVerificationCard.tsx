'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { BadgeCheck, Loader2 } from 'lucide-react'
import { useVerifyTenant } from '@/lib/hooks/useDirectory'
import { useDateFormat } from '@/lib/i18n/date'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface Props {
  tenantId: string
  isVerified: boolean
  /** Admins only; operators see the state read-only. */
  canEdit: boolean
}

/**
 * Credential verification (free; the public directory's trust signal). The tenant detail response
 * only says whether the tenant is verified, so the date and note are shown only for a change made
 * in this session, and the card says what it cannot show.
 */
export function TenantVerificationCard({ tenantId, isVerified, canEdit }: Props) {
  const t = useTranslations('directoryAdminUi')
  const { fmt } = useDateFormat()
  const verify = useVerifyTenant(tenantId)
  const [note, setNote] = useState('')
  const [noteError, setNoteError] = useState(false)
  const [result, setResult] = useState<{ verified_at: string | null; verification_note: string | null } | null>(null)

  const verified = verify.data ? verify.data.is_verified : isVerified

  const submit = async (value: boolean) => {
    if (!note.trim()) {
      setNoteError(true)
      return
    }
    setNoteError(false)
    try {
      const res = await verify.mutateAsync({ verified: value, note: note.trim() })
      setResult({ verified_at: res.verified_at, verification_note: res.verification_note })
      setNote('')
    } catch {
      /* the mutation's onError already showed the reason */
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BadgeCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('verification.title')}
        </CardTitle>
        <CardDescription>{t('verification.description')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <p className="text-sm text-muted-foreground">{t('verification.state')}</p>
            <Badge variant={verified ? 'default' : 'outline'}>
              {verified ? t('verification.verified') : t('verification.unverified')}
            </Badge>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t('verification.verifiedAt')}</p>
            <p className="font-medium">
              {result?.verified_at ? fmt(result.verified_at, 'MMM d, yyyy h:mm a') : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t('verification.note')}</p>
            <p className="font-medium whitespace-pre-wrap break-words">{result?.verification_note || '-'}</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{t('verification.noteMissing')}</p>

        <div className="rounded-lg border bg-muted/40 p-4 text-sm">
          <p className="font-semibold">{t('verification.details')}</p>
          <p className="mt-1 text-muted-foreground">{t('verification.detailsMissing')}</p>
        </div>

        {canEdit ? (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="verification-note">{t('verification.noteLabel')}</Label>
              <Textarea
                id="verification-note"
                rows={3}
                maxLength={1000}
                value={note}
                placeholder={t('verification.notePlaceholder')}
                onChange={(e) => {
                  setNote(e.target.value)
                  if (e.target.value.trim()) setNoteError(false)
                }}
                aria-invalid={noteError}
              />
              {noteError && <p role="alert" className="text-sm text-red-600">{t('verification.noteRequired')}</p>}
            </div>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => submit(true)} disabled={verify.isLoading} className="h-10">
                {verify.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                {verify.isLoading ? t('verification.working') : t('verification.verify')}
              </Button>
              {verified && (
                <Button variant="outline" onClick={() => submit(false)} disabled={verify.isLoading} className="h-10">
                  {t('verification.remove')}
                </Button>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t('verification.readOnly')}</p>
        )}
      </CardContent>
    </Card>
  )
}
