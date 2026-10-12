'use client'

import { useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ImageIcon, Loader2 } from 'lucide-react'
import { useClinicProfile, useRemoveLogo, useUploadLogo } from '@/lib/hooks/useClinicLogo'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const MAX_BYTES = 2 * 1024 * 1024
const TYPES = ['image/png', 'image/jpeg', 'image/webp']

/** Upload or remove the clinic logo. Only doctors can change it (the server enforces this too). */
export function ClinicLogoCard({ canEdit }: { canEdit: boolean }) {
  const t = useTranslations('clinicLogoUi')
  const profile = useClinicProfile()
  const upload = useUploadLogo()
  const remove = useRemoveLogo()
  const input = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  const logo = profile.data?.logo_url ?? null
  const busy = upload.isLoading || remove.isLoading

  const onPick = (file: File | undefined) => {
    if (!file) return
    setError(null)
    // Quick checks for a friendly message; the server decides by the file's content
    if (!TYPES.includes(file.type)) return setError(t('wrongType'))
    if (file.size > MAX_BYTES) return setError(t('tooLarge'))
    upload.mutate(file)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-emerald-600" aria-hidden="true" />
          {t('title')}
        </CardTitle>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-lg border bg-muted">
            {logo ? (
              // eslint-disable-next-line @next/next/no-img-element -- remote object-storage URL, already resized by the server
              <img src={logo} alt={t('alt')} className="h-full w-full object-contain" />
            ) : (
              <span className="px-2 text-center text-xs text-muted-foreground">{t('none')}</span>
            )}
          </div>
          {canEdit ? (
            <div className="space-y-2">
              <input
                ref={input}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="sr-only"
                aria-label={t('choose')}
                onChange={(e) => {
                  onPick(e.target.files?.[0])
                  e.target.value = '' // allow choosing the same file again
                }}
              />
              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" disabled={busy} onClick={() => input.current?.click()}>
                  {upload.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                  {upload.isLoading ? t('working') : logo ? t('replace') : t('choose')}
                </Button>
                {logo && (
                  <Button type="button" variant="ghost" disabled={busy} onClick={() => remove.mutate()}>
                    {remove.isLoading ? t('removing') : t('remove')}
                  </Button>
                )}
              </div>
              {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t('readOnly')}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
