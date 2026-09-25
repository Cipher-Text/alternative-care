'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/lib/api/auth'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import type { ReactNode } from 'react'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)
  const setAuth = useAuthStore((state) => state.setAuth)
  const setAccessToken = useAuthStore((state) => state.setAccessToken)
  const logout = useAuthStore((state) => state.logout)

  useEffect(() => {
    if (!hasHydrated || isAuthenticated) {
      return
    }

    // The access token lives only in memory, so it doesn't survive a page
    // reload — only the backend's httpOnly refresh_token cookie does. Try
    // a silent refresh before redirecting to login.
    let cancelled = false
    void (async () => {
      try {
        const { access_token } = await authApi.refresh()
        // Store the token before the next call — apiClient's request
        // interceptor reads it from the store, not from this closure.
        setAccessToken(access_token)
        const profile = await authApi.getCurrentUser()
        if (!cancelled) {
          setAuth(profile.user, access_token)
        }
      } catch {
        if (!cancelled) {
          logout()
          router.push('/login')
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [hasHydrated, isAuthenticated, setAuth, setAccessToken, logout, router])

  if (!hasHydrated || !isAuthenticated) {
    return null // Don't render anything while checking/redirecting
  }

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-slate-900 transition-colors">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 bg-gray-50 dark:bg-gradient-to-br dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors">
          {children}
        </main>
      </div>

    </div>
  )
}
