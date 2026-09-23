'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { authApi } from '@/lib/api/auth'
import { getErrorMessage } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

type Status = 'verifying' | 'success' | 'error'

export function VerifyEmailStatus({ token }: { token: string | null }) {
  const t = useTranslations('auth')
  const [status, setStatus] = useState<Status>(token ? 'verifying' : 'error')
  const [errorMessage, setErrorMessage] = useState<string>(t('missingVerifyToken'))

  useEffect(() => {
    if (!token) return

    let cancelled = false
    authApi
      .verifyEmail({ token })
      .then(() => {
        if (!cancelled) setStatus('success')
      })
      .catch((error) => {
        if (!cancelled) {
          setErrorMessage(getErrorMessage(error, t('verifyEmailFailed')))
          setStatus('error')
        }
      })

    return () => {
      cancelled = true
    }
    // Only re-run if the token itself changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">{t('verifyEmailTitle')}</CardTitle>
        <CardDescription>
          {status === 'verifying' && t('verifyingEmail')}
          {status === 'success' && t('verifyEmailSuccess')}
          {status === 'error' && errorMessage}
        </CardDescription>
      </CardHeader>
      {status !== 'verifying' && (
        <CardContent>
          <Button asChild className="w-full">
            <Link href="/login">{t('goToLogin')}</Link>
          </Button>
        </CardContent>
      )}
    </Card>
  )
}
