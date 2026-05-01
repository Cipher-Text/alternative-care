'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'

export default function Home() {
  const router = useRouter()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    // Redirect to dashboard if authenticated, otherwise to login
    if (isAuthenticated) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }, [isAuthenticated, router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-muted-foreground">Redirecting...</p>
    </div>
  )
}
