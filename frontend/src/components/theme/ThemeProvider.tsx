'use client'

import { useEffect } from 'react'
import { useThemeStore } from '@/store/themeStore'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, setTheme, resolvedTheme } = useThemeStore()

  // Apply theme immediately on mount (before hydration)
  useEffect(() => {
    // Apply the resolved theme to HTML element
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(resolvedTheme)

    // Also set the theme to trigger any necessary updates
    setTheme(theme)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Run once on mount to initialize

  // Listen to theme changes
  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(resolvedTheme)
  }, [resolvedTheme])

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
