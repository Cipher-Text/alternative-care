'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { Toaster } from 'react-hot-toast'
import type { ReactNode } from 'react'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthStore((state) => state.hasHydrated)

  useEffect(() => {
    // Redirect to login if not authenticated
    if (hasHydrated && !isAuthenticated) {
      router.push('/login')
    }
  }, [hasHydrated, isAuthenticated, router])

  if (!hasHydrated || !isAuthenticated) {
    return null // Don't render anything while redirecting
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 bg-gray-50 dark:bg-gray-900">
          {children}
        </main>
      </div>

      <Toaster position="top-right" />
    </div>
  )
}
