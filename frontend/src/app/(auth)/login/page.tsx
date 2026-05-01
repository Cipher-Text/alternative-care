'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { LoginForm } from '@/components/auth/LoginForm'
import { Toaster } from 'react-hot-toast'

export default function LoginPage() {
  const router = useRouter()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  useEffect(() => {
    // Redirect to dashboard if already logged in
    if (hasHydrated && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [hasHydrated, isAuthenticated, router])

  return (
    <>
      <LoginForm />
      <Toaster position="top-right" />
    </>
  )
}
