'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getPostLoginPath } from '@/lib/auth/redirects'
import { useAuthStore } from '@/store/authStore'

export default function Home() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  useEffect(() => {
    if (!hasHydrated) return

    // Redirect to dashboard if authenticated, otherwise to login
    if (isAuthenticated && user) {
      router.push(getPostLoginPath(user))
    } else {
      router.push('/login')
    }
  }, [hasHydrated, isAuthenticated, router, user])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-muted-foreground">Redirecting...</p>
    </div>
  )
}
