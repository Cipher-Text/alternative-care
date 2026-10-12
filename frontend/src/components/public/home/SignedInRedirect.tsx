'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { getPostLoginPath } from '@/lib/auth/redirects'

/** Sends an already signed-in user from the marketing home page to their dashboard. Renders nothing. */
export function SignedInRedirect() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  useEffect(() => {
    if (hasHydrated && isAuthenticated && user) {
      router.replace(getPostLoginPath(user))
    }
  }, [hasHydrated, isAuthenticated, user, router])

  return null
}
