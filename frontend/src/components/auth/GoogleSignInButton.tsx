'use client'

import { useEffect, useRef, useState } from 'react'
import { loadGoogleIdentityScript } from '@/lib/google-identity'

interface GoogleSignInButtonProps {
  onCredential: (idToken: string) => void
}

const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID

export function GoogleSignInButton({ onCredential }: GoogleSignInButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const onCredentialRef = useRef(onCredential)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    onCredentialRef.current = onCredential
  })

  useEffect(() => {
    if (!clientId) return
    let cancelled = false

    loadGoogleIdentityScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.google) return

        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => onCredentialRef.current(response.credential),
        })
        window.google.accounts.id.renderButton(containerRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: String(containerRef.current.offsetWidth || 300),
        })
      })
      .catch(() => setFailed(true))

    return () => {
      cancelled = true
    }
  }, [])

  if (!clientId || failed) {
    // No client ID configured, or the script failed to load — omit the
    // button rather than show a broken control. Password login still works.
    return null
  }

  return <div ref={containerRef} />
}
