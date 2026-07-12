'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getPostLoginPath } from '@/lib/auth/redirects'
import { useAuthStore } from '@/store/authStore'
import { LoginForm } from '@/components/auth/LoginForm'

export default function LoginPage() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  useEffect(() => {
    // Redirect to dashboard if already logged in
    if (hasHydrated && isAuthenticated && user) {
      router.push(getPostLoginPath(user))
    }
  }, [hasHydrated, isAuthenticated, router, user])

  return <LoginForm />
}
