'use client'

import Link from 'next/link'
import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { Menu, X } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { LanguageSwitcher } from '@/components/language/LanguageSwitcher'
import { useAuthStore } from '@/store/authStore'
import { getPostLoginPath } from '@/lib/auth/redirects'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme/ThemeToggle'
import { cn } from '@/lib/utils'

const navigation = [
  { key: 'navMedicines', href: '/knowledge/medicines' },
  { key: 'navSymptoms', href: '/knowledge/symptoms' },
  { key: 'navInstitutions', href: '/institutions' },
  { key: 'navPractitioners', href: '/for-practitioners' },
  { key: 'navPricing', href: '/pricing' },
  { key: 'navAbout', href: '/about' },
] as const

export function PublicHeader() {
  const t = useTranslations('publicShellUi')
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 dark:border-slate-800 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <span className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
              AltCare
            </span>
          </Link>

          <nav className="hidden lg:flex items-center gap-1">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  pathname === item.href || pathname.startsWith(item.href + '/')
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                )}
              >
                {t(item.key)}
              </Link>
            ))}
          </nav>

          <div className="hidden lg:flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeToggle />
            {isAuthenticated && user ? (
              <Button asChild size="sm">
                <Link href={getPostLoginPath(user)}>{t('goToDashboard')}</Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm">
                  <Link href="/login">{t('signIn')}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link href="/register">{t('getStarted')}</Link>
                </Button>
              </>
            )}
          </div>

          <button
            className="lg:hidden p-2 text-gray-600 dark:text-gray-300"
            onClick={() => setMobileOpen((open) => !open)}
            aria-label={t('toggleMenu')}
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {mobileOpen && (
          <nav className="lg:hidden pb-4 flex flex-col gap-1">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800"
              >
                {t(item.key)}
              </Link>
            ))}
            <div className="flex items-center gap-2 pt-2 px-3">
              <LanguageSwitcher />
            <ThemeToggle />
              {isAuthenticated && user ? (
                <Button asChild size="sm" className="flex-1">
                  <Link href={getPostLoginPath(user)}>{t('goToDashboard')}</Link>
                </Button>
              ) : (
                <>
                  <Button asChild variant="outline" size="sm" className="flex-1">
                    <Link href="/login">{t('signIn')}</Link>
                  </Button>
                  <Button asChild size="sm" className="flex-1">
                    <Link href="/register">{t('getStarted')}</Link>
                  </Button>
                </>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
