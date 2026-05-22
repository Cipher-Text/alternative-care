'use client'

import { useEffect } from 'react'
import { useThemeStore } from '@/store/themeStore'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, setTheme, hasHydrated, setHydrated } = useThemeStore()

  // Initialize theme on mount
  useEffect(() => {
    if (!hasHydrated) {
      setHydrated(true)
      // Re-apply theme after hydration
      setTheme(theme)
    }
  }, [hasHydrated, setHydrated, setTheme, theme])

  // Listen to system theme changes
  useEffect(() => {
    if (theme === 'system' && typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

      const handleChange = () => {
        setTheme('system') // Trigger re-resolution
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme, setTheme])

  return <>{children}</>
}
