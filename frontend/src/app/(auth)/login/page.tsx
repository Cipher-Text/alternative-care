'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { LoginForm } from '@/components/auth/LoginForm'
import { Toaster } from 'react-hot-toast'

export default function LoginPage() {
  const router = useRouter()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    // Redirect to dashboard if already logged in
    if (isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, router])

  return (
    <>
      <LoginForm />
      <Toaster position="top-right" />
    </>
  )
}
