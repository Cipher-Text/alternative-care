'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useLocale } from 'next-intl'
import { consumeGoogleIdToken } from '@/lib/auth/google-session'
import { GoogleRegisterForm } from '@/components/auth/GoogleRegisterForm'

export default function GoogleRegisterPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const locale = useLocale()
  // Lazy initializer runs once on mount; reading (and clearing) the stashed
  // token here — rather than in an effect — keeps this a plain derived
  // value instead of a second render pass.
  const [idToken] = useState<string | null>(() =>
    typeof window === 'undefined' ? null : consumeGoogleIdToken()
  )

  useEffect(() => {
    if (!idToken) {
      // Direct navigation without going through the Google button first —
      // there's no identity to register, send back to login.
      router.replace('/login')
    }
  }, [idToken, router])

  if (!idToken) {
    return null
  }

  return (
    <GoogleRegisterForm
      idToken={idToken}
      email={searchParams.get('email') ?? ''}
      fullName={searchParams.get('name') ?? ''}
      language={locale === 'bn' ? 'bn' : 'en'}
    />
  )
}
